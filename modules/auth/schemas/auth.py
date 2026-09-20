from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str | None = None
    refresh_token: str | None = None
    token_type: str = "bearer"
    user: dict | None = None
    requires_2fa: bool = False
    temp_token: str | None = None
    message: str | None = None

class Verify2FARequest(BaseModel):
    temp_token: str
    code: str

class RegisterRequest(BaseModel):
    organization_name: str
    organization_type: str
    name: str
    email: EmailStr
    password: str
    phone: str | None = None

class RegisterResponse(BaseModel):
    id: str
    name: str
    email: str
    username: str
    is_owner: bool = False
    organization_id: str
    organization_name: str | None = None
    organization_type: str | None = None
    phone: str | None = None

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class VerifyEmailRequest(BaseModel):
    email: EmailStr
    code: str

class ResendCodeRequest(BaseModel):
    email: EmailStr

class MessageResponse(BaseModel):
    success: bool = True

