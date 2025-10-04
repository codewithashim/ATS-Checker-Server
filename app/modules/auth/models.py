from beanie import Document
from pydantic import EmailStr, Field
from typing import Optional
from datetime import datetime
from enum import Enum

class UserRole(str, Enum):
    JOB_SEEKER = "job_seeker"
    RECRUITER = "recruiter"

class User(Document):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr = Field(..., unique=True)
    hashed_password: str
    role: UserRole = UserRole.JOB_SEEKER
    avatar: Optional[str] = None
    is_email_verified: bool = False
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None

    class Settings:
        name = "users"
        indexes = [
            "email",
            "role",
            "is_active",
            "created_at"
        ]

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, role={self.role})>"
