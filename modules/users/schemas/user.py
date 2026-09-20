import uuid

from pydantic import BaseModel, EmailStr


class ProfilePlanResponse(BaseModel):
    id: uuid.UUID
    code: str
    name: str
    tier_level: int
    yearly_price: float
    monthly_price: float

class ProfileSubscriptionResponse(BaseModel):
    id: uuid.UUID
    status: str
    billing_cycle: str
    plan: ProfilePlanResponse | None = None

class ProfileSettingResponse(BaseModel):
    key: str
    value: str | None = None
    description: str | None = None

class ProfileResponse(BaseModel):
    id: uuid.UUID
    name: str
    email: EmailStr
    username: str
    phone: str | None = None
    account: str

class UpdateProfileRequest(BaseModel):
    name: str | None = None
    phone: str | None = None

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str
