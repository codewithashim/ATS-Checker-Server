from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from beanie import PydanticObjectId

class JobPostingBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    company: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1)
    requirements: Optional[str] = None
    location: Optional[str] = Field(None, max_length=100)
    salary_min: Optional[int] = Field(None, ge=0)
    salary_max: Optional[int] = Field(None, ge=0)
    employment_type: Optional[str] = Field(None, max_length=50)
    remote_allowed: bool = False

class JobPostingCreate(JobPostingBase):
    pass

class JobPostingUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    company: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, min_length=1)
    requirements: Optional[str] = None
    location: Optional[str] = Field(None, max_length=100)
    salary_min: Optional[int] = Field(None, ge=0)
    salary_max: Optional[int] = Field(None, ge=0)
    employment_type: Optional[str] = Field(None, max_length=50)
    remote_allowed: Optional[bool] = None
    is_active: Optional[bool] = None

class JobPostingInDB(JobPostingBase):
    id: PydanticObjectId
    user_id: PydanticObjectId
    keywords: Optional[Dict[str, Any]] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class JobPosting(JobPostingInDB):
    pass

class JobPostingSearch(BaseModel):
    query: Optional[str] = None
    location: Optional[str] = None
    employment_type: Optional[str] = None
    remote_allowed: Optional[bool] = None
    salary_min: Optional[int] = Field(None, ge=0)
    salary_max: Optional[int] = Field(None, ge=0)
    page: int = Field(1, ge=1)
    limit: int = Field(10, ge=1, le=100)
