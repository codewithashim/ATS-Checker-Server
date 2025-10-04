from beanie import Document
from pydantic import Field
from typing import Optional, Dict, Any
from datetime import datetime
from beanie import PydanticObjectId

class JobPosting(Document):
    user_id: PydanticObjectId
    title: str = Field(..., min_length=1, max_length=200)
    company: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1)
    requirements: Optional[str] = None
    location: Optional[str] = Field(None, max_length=100)
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    employment_type: Optional[str] = Field(None, max_length=50)  # 'full_time', 'part_time', 'contract', 'internship'
    remote_allowed: bool = False
    keywords: Optional[Dict[str, Any]] = None  # Extracted keywords for matching
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "job_postings"
        indexes = [
            "user_id",
            "title",
            "company",
            "location",
            "employment_type",
            "is_active",
            "created_at",
            "salary_min",
            "salary_max"
        ]

    def __repr__(self):
        return f"<JobPosting(id={self.id}, title={self.title}, company={self.company})>"
