import calendar
import random
import uuid
from datetime import date, datetime, timedelta, timezone

from app.repositories.plan_repository import PlanRepository
from app.repositories.subscription_event_repository import SubscriptionEventRepository
from app.repositories.subscription_repository import SubscriptionRepository
from app.services.subscription_service import SubscriptionService
from app.shared.enums import BillingCycle
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import (
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    ValidationError,
)
from app.core.helpers import (
    generate_org_code,
    generate_username,
    validate_login_settings,
    validate_password,
)
from app.core.security import (
    create_2fa_token,
    create_access_token,
    create_refresh_token,
    hash_password,
    hash_token,
    verify_password,
    verify_token,
)
from models.refresh_token import (
    RefreshToken,
)
from models.user import User
from models.verification_code import VerificationCode


class AuthService:
    def __init__(
        self,
        session: AsyncSession,
        user_repo,
        refresh_repo=None,
    ):
        self.session = session
        self.user_repo = user_repo
        self.refresh_repo = refresh_repo

    async def login(
        self,
        username: str,
        password: str,
    ):
        user = await self.user_repo.get_by_login(username)
        
        if not user:
            raise AuthenticationError(
                "Incorrect username or password"
            )

        if user.account == 'organization':
            requires_2fa = await validate_login_settings(
                username=username,
                user=user,
                session=self.session
            )
        else:
            requires_2fa = False

        if not verify_password(
            password,
            user.password_hash,
        ):
            raise AuthenticationError(
                "Incorrect username or password"
            )

        if not user.is_active:
            raise AuthenticationError(
                "Account is inactive"
            )

        if not user.is_verified:
            raise AuthenticationError(
                "Please verify your email address before logging in"
            )

        if requires_2fa:
            temp_token = create_2fa_token(str(user.id))
            verification_code_str = f"{random.randint(100000, 999999)}"
            
            verification_code_obj = VerificationCode(
                user_id=user.id,
                code=verification_code_str,
                expires_at=datetime.now(timezone.utc) + timedelta(minutes=10),
            )
            self.session.add(verification_code_obj)
            await self.session.commit()
            
            print(
                f"\n{'='*50}\n"
                f"[2FA LOGIN CODE for {user.email}]: {verification_code_str}\n"
                f"{'='*50}\n"
            )
            
            return {
                "requires_2fa": True,
                "temp_token": temp_token,
                "message": "A 2FA code has been sent to your email address.",
                "access_token": None,
                "refresh_token": None,
                "user": None
            }

        await self.refresh_repo.remove(
            str(user.id)
        )

        access_token = create_access_token(str(user.id))

        refresh_token = create_refresh_token(str(user.id))

        refresh = RefreshToken(
            id=str(uuid.uuid4()),
            user_id=user.id,
            token_hash=hash_token(refresh_token),
        )

        await self.refresh_repo.create(refresh)

        await self.session.commit()

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "username": user.username,
                "phone": user.phone,
                "account": user.account,
            },
        }

    async def verify_2fa(self, temp_token: str, code: str):
        try:
            payload = jwt.decode(
                temp_token,
                settings.JWT_SECRET,
                algorithms=[settings.JWT_ALGORITHM],
            )
            
            if payload.get("type") != "2fa":
                raise AuthenticationError("Invalid token type")
                
            user_id = payload.get("sub")
            if not user_id:
                raise AuthenticationError("Invalid token payload")
        except JWTError:
            raise AuthenticationError("Invalid or expired temp token")
            
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundError("User not found")
            
        # Verify the code
        result = await self.session.execute(
            select(VerificationCode).where(
                VerificationCode.user_id == user.id,
                VerificationCode.code == code.strip(),
                VerificationCode.is_used == False
            ).order_by(VerificationCode.created_at.desc())
        )
        verification_code_obj = result.scalars().first()
        
        if not verification_code_obj:
            raise ValidationError("Invalid 2FA code")
            
        if verification_code_obj.expires_at < datetime.now(timezone.utc):
            raise ValidationError("2FA code has expired. Please request a new code.")
            
        # Mark as used
        verification_code_obj.is_used = True
        
        await self.refresh_repo.remove(str(user.id))
        
        access_token = create_access_token(str(user.id))
        refresh_token = create_refresh_token(str(user.id))
        
        refresh = RefreshToken(
            id=str(uuid.uuid4()),
            user_id=user.id,
            token_hash=hash_token(refresh_token),
        )
        
        await self.refresh_repo.create(refresh)
        
        await self.session.commit()
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "username": user.username,
                "phone": user.phone,
                "account": user.account,
            },
        }

    async def register(
        self,
        name: str,
        email: str,
        password: str,
        phone: str | None = None
    ):

        await validate_password(
            password=password,
            settings_repo=self.system_repo,
        )

        existing_user = await self.user_repo.get_by_email(email)

        if existing_user:
            raise ValidationError(
                "Email already exists"
            )

        try:
            username = await generate_username(name, self.user_repo)
            user = User(
                id=uuid.uuid4(),
                name=name,
                email=email,
                password_hash=hash_password(password),
                username=username,
                phone=phone,
                account="user",
                is_active=True,
                is_verified=False,
            )

            await self.user_repo.create(user)

            # --- Generate 6-digit Email Verification Code ---
            verification_code_str = f"{random.randint(100000, 999999)}"
            expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)
            verification_code_obj = VerificationCode(
                id=uuid.uuid4(),
                user_id=user.id,
                code=verification_code_str,
                expires_at=expires_at,
                is_used=False,
            )
            self.session.add(verification_code_obj)
            print(
                f"\n=======================================================\n"
                f"[EMAIL VERIFICATION CODE for {email}]: {verification_code_str}\n"
                f"=======================================================\n",
                flush=True,
            )
            # ------------------------------------------------

            # --- Assign Default Plan Subscription ---
            plan_repo = PlanRepository(self.session)
            default_plan = await plan_repo.get_default_plan()
            if default_plan is None:
                raise NotFoundError(
                    "Default plan not found"
                )

            subscription_service = SubscriptionService(
                    subscription_repository=SubscriptionRepository(self.session),
                    subscription_event_repository=SubscriptionEventRepository(self.session),
                    plan_repository=plan_repo,
            )
            await subscription_service.create_subscription(
                    plan_id=default_plan.id,
                    billing_cycle=BillingCycle.ANNUAL,
                    period=1
            )
            # ----------------------------------------

            return user

        except Exception:

            await self.session.rollback()

            raise

    async def refresh_tokens(self, refresh_token_str: str):
        try:
            payload = jwt.decode(
                refresh_token_str,
                settings.JWT_SECRET,
                algorithms=[settings.JWT_ALGORITHM],
            )
        except JWTError:
            raise AuthenticationError("Invalid or expired refresh token")

        if payload.get("type") != "refresh":
            raise AuthenticationError("Invalid token type")

        user_id = payload.get("sub")
        if not user_id:
            raise AuthenticationError("Invalid token payload")

        user = await self.user_repo.get_by_id(user_id)
        if not user or not user.is_active:
            raise AuthenticationError("User not found or inactive")

        active_tokens = await self.refresh_repo.get_active_by_user_id(user.id)
        matching_token = None
        for token_rec in active_tokens:
            if verify_token(refresh_token_str, token_rec.token_hash):
                matching_token = token_rec
                break

        if not matching_token:
            raise AuthenticationError("Invalid or revoked refresh token")

        # Explicitly revoke matched token and delete old tokens
        matching_token.is_revoked = True
        await self.refresh_repo.remove(user.id)

        new_access_token = create_access_token(str(user.id))
        new_refresh_token = create_refresh_token(str(user.id))

        new_refresh = RefreshToken(
            id=str(uuid.uuid4()),
            user_id=user.id,
            token_hash=hash_token(new_refresh_token),
        )
        await self.refresh_repo.create(new_refresh)

        await self.session.commit()

        return {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
            "user": {
                "id": str(user.id),
                "name": user.name,
                "email": user.email,
                "username": user.username,
                "phone": user.phone,
            },
        }

    async def verify_email(self, email: str, code: str):
        user = await self.user_repo.get_by_email(email)
        if not user:
            raise NotFoundError("User with this email does not exist")

        if user.is_verified:
            return True

        stmt = (
            select(VerificationCode)
            .where(
                VerificationCode.user_id == user.id,
                VerificationCode.code == code.strip(),
                VerificationCode.is_used == False,
            )
            .order_by(VerificationCode.created_at.desc())
        )

        result = await self.session.execute(stmt)
        record = result.scalars().first()

        if not record:
            raise ValidationError("Invalid verification code")

        now_utc = datetime.now(timezone.utc)
        if record.expires_at < now_utc:
            raise ValidationError("Verification code has expired. Please request a new code.")

        record.is_used = True
        user.is_verified = True
        await self.session.commit()
        return True

    async def resend_verification_code(self, email: str):
        user = await self.user_repo.get_by_email(email)
        if not user:
            raise NotFoundError("User with this email does not exist")

        if user.is_verified:
            raise ValidationError("Email is already verified")

        stmt = select(VerificationCode).where(
            VerificationCode.user_id == user.id,
            VerificationCode.is_used == False,
        )
        result = await self.session.execute(stmt)
        for old_code in result.scalars().all():
            old_code.is_used = True

        verification_code_str = f"{random.randint(100000, 999999)}"
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)
        new_code = VerificationCode(
            id=uuid.uuid4(),
            user_id=user.id,
            code=verification_code_str,
            expires_at=expires_at,
            is_used=False,
        )
        self.session.add(new_code)
        await self.session.commit()

        print(
            f"\n=======================================================\n"
            f"[RESENT VERIFICATION CODE for {email}]: {verification_code_str}\n"
            f"=======================================================\n",
            flush=True,
        )
        return True
