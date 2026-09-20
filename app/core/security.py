import uuid
from datetime import datetime
from datetime import timedelta
from datetime import timezone

from jose import jwt
import bcrypt

from app.core.config import settings
from app.auth.repositories.refresh_token_repository import RefreshTokenRepository

import hashlib
import hmac

def hash_password(password: str) -> str:
    # bcrypt has a hard 72-byte limit on passwords
    return bcrypt.hashpw(
        password[:72].encode("utf-8"),
        bcrypt.gensalt(),
    ).decode("utf-8")

def verify_password(
    plain: str,
    hashed: str,
) -> bool:
    return bcrypt.checkpw(
        plain[:72].encode("utf-8"),
        hashed.encode("utf-8"),
    )

def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()

def verify_token(plain: str, token_hash: str) -> bool:
    calc_hash = hashlib.sha256(plain.encode("utf-8")).hexdigest()
    if hmac.compare_digest(calc_hash, token_hash):
        return True
    try:
        return verify_password(plain, token_hash)
    except Exception:
        return False


def create_access_token(
    user_id: str,
) -> str:

    expire = datetime.now(
        timezone.utc
    ) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "sub": user_id,
        "type": "access",
        "jti": str(uuid.uuid4()),
        "exp": expire,
    }

    return jwt.encode(
        payload,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )

def create_refresh_token(
    user_id: str,
) -> str:

    expire = datetime.now(
        timezone.utc
    ) + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )

    payload = {
        "sub": user_id,
        "type": "refresh",
        "jti": str(uuid.uuid4()),
        "exp": expire,
    }

    return jwt.encode(
        payload,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )

def create_2fa_token(
    user_id: str,
) -> str:
    # Short lived token for 2fa flow
    expire = datetime.now(
        timezone.utc
    ) + timedelta(
        minutes=10
    )

    payload = {
        "sub": user_id,
        "type": "2fa",
        "jti": str(uuid.uuid4()),
        "exp": expire,
    }

    return jwt.encode(
        payload,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )
