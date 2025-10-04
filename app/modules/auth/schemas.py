from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from beanie import PydanticObjectId
from app.modules.auth.models import UserRole

class UserBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    role: UserRole = UserRole.JOB_SEEKER

class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=100)
    confirm_password: str = Field(..., min_length=8, max_length=100)

class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    avatar: Optional[str] = Field(None, max_length=500)

class UserInDB(UserBase):
    id: PydanticObjectId
    avatar: Optional[str] = None
    is_email_verified: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True
        json_encoders = {
            PydanticObjectId: str
        }

class User(UserInDB):
    pass

class UserLogin(BaseModel):
    email: EmailStr
    password: str
    remember_me: Optional[bool] = False

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

class TokenData(BaseModel):
    user_id: Optional[str] = None
    email: Optional[str] = None

class PasswordReset(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    token: str
    password: str = Field(..., min_length=8, max_length=100)
    confirm_password: str = Field(..., min_length=8, max_length=100)

class EmailVerification(BaseModel):
    token: str
