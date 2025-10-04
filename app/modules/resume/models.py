from beanie import Document, Link
from pydantic import Field
from typing import Optional, Dict, Any
from datetime import datetime
from beanie import PydanticObjectId
from app.modules.auth.models import User
from app.modules.job_posting.models import JobPosting

class Resume(Document):
    user_id: PydanticObjectId
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)
    file_path: Optional[str] = None
    file_name: Optional[str] = None
    file_size: Optional[int] = None
    is_public: bool = False
    ats_score: Optional[int] = None  # ATS compatibility score (0-100)
    analysis_results: Optional[Dict[str, Any]] = None  # Store detailed analysis results
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "resumes"
        indexes = [
            "user_id",
            "title",
            "is_public",
            "created_at",
            "ats_score"
        ]

    def __repr__(self):
        return f"<Resume(id={self.id}, title={self.title}, user_id={self.user_id})>"

class ResumeAnalysis(Document):
    resume_id: PydanticObjectId
    job_posting_id: Optional[PydanticObjectId] = None
    analysis_type: str = Field(..., min_length=1, max_length=50)  # 'ats_check', 'keyword_match', 'format_check'
    score: int = Field(..., ge=0, le=100)  # 0-100
    details: Optional[Dict[str, Any]] = None  # Detailed analysis results
    recommendations: Optional[Dict[str, Any]] = None  # Improvement recommendations
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "resume_analyses"
        indexes = [
            "resume_id",
            "job_posting_id",
            "analysis_type",
            "score",
            "created_at"
        ]

    def __repr__(self):
        return f"<ResumeAnalysis(id={self.id}, resume_id={self.resume_id}, score={self.score})>"
