import re
import uuid
from datetime import datetime
from typing import Any

from app.models.organization_setting import OrganizationSetting
from cryptography.fernet import Fernet
from fastapi import Request
from fastapi.responses import JSONResponse
from sqlalchemy import select

from app.core.config import settings
from app.core.exceptions import AppException, AuthenticationError, ValidationError

cipher = Fernet(settings.APP_ENCRYPTION_KEY.encode())

async def generate_username(
    full_name: str,
    user_repo,
) -> str:
    """
    Akeem O. Salau -> akeem
    John Doe -> john
    """

    first_name = full_name.strip().split()[0]

    base_username = re.sub(
        r"[^a-zA-Z0-9]",
        "",
        first_name.lower(),
    )

    username = base_username
    counter = 1

    while await user_repo.username_exists(username):
        username = f"{base_username}{counter}"
        counter += 1

    return username

def generate_org_code(sequence: int) -> str:
    """
    ORG-050926-00001
    """
    date_part = datetime.utcnow().strftime("%d%m%y")

    return f"ORG-{date_part}-{sequence:05d}"

async def validate_password(
    password: str,
    settings_repo,
):
    settings = await settings_repo.get_many([
        "security.password_min_length",
        "security.password_require_uppercase",
        "security.password_require_special",
        "security.password_require_lowercase",
        "security.password_require_number",
    ])
    min_length = int(
        settings.get("security.password_min_length", "8")
    )

    require_uppercase = (
        settings.get("security.password_require_uppercase", "true")
    ).lower() == "true"

    require_special = (
        settings.get("security.password_require_special", "true")
    ).lower() == "true"

    require_lowercase = (
        settings.get("security.password_require_lowercase", "true")
    ).lower() == "true"

    require_number = (
        settings.get("security.password_require_number", "true")
    ).lower() == "true"

    if len(password) < min_length:
        raise ValidationError(
            f"Password must be at least {min_length} characters long"
        )

    if require_uppercase and not re.search(
        r"[A-Z]",
        password,
    ):
        raise ValidationError(
            "Password must contain atleast one uppercase letter"
        )

    if require_special and not re.search(
        r"[!@#$%^&*()_\-+=\[\]{};:,.<>?/\\|`~]",
        password,
    ):
        raise ValidationError(
            "Password must contain atleast one special character"
        )

    if require_lowercase and not re.search(
        r"[a-z]",
        password,
    ):
        raise ValidationError(
            "Password must contain atleast one lowercase letter"
        )

    if require_number and not re.search(
        r"[0-9]",
        password,
    ):
        raise ValidationError(
            "Password must contain atleast one number"
        )

async def validate_login_settings(
    username: str,
    user,
    session,
):

    if not user.organization_id:
        return False

    org_settings_stmt = select(OrganizationSetting).where(
        OrganizationSetting.organization_id == user.organization_id,
        OrganizationSetting.key.in_([
            "auth.allow_username_login",
            "auth.allow_email_login",
            "security.two_factor_authentication"
        ])
    )
    settings_result = await session.execute(org_settings_stmt)
    org_settings = {s.key: s.value for s in settings_result.scalars().all()}
    
    allow_username = org_settings.get("auth.allow_username_login", "true") == "true"
    allow_email = org_settings.get("auth.allow_email_login", "true") == "true"
    two_factor_auth = org_settings.get("security.two_factor_authentication", "false") == "true"
    
    is_email_login = username == user.email
    is_username_login = username == user.username
    
    if is_email_login and not allow_email:
        raise AuthenticationError("Email login is disabled by your organization")
        
    if is_username_login and not allow_username:
        raise AuthenticationError("Username login is disabled by your organization")
        
    return two_factor_auth
def success(sucess: bool = True, message: str = "Operation successful", data: Any = None):
    return {
        "success": sucess,
        "message": message,
        "data": data
    }

def encrypt_value(value: str) -> str:
    return cipher.encrypt(value.encode()).decode()

def decrypt_value(value: str) -> str:
    return cipher.decrypt(value.encode()).decode()

def generate_journal_reference() -> str:
    """
    Example: JNL-260919-A1B2C3D
    """
    date_part = datetime.utcnow().strftime("%y%m%d")
    short_id = str(uuid.uuid4()).split("-")[0].upper()
    return f"JNL-{date_part}-{short_id}"

async def app_exception_handler(
    request: Request,
    exc: AppException,
):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": exc.error_code,
                "message": exc.message,
            },
        },
    )