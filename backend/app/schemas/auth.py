from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional
from datetime import datetime


class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    referral_code: Optional[str] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AffiliateInToken(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    referral_code: str
    is_admin: bool
    status: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: AffiliateInToken
