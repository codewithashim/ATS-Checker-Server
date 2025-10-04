from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from beanie import PydanticObjectId

class ResumeBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)
    is_public: bool = False

class ResumeCreate(ResumeBase):
    pass

class ResumeUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    content: Optional[str] = Field(None, min_length=1)
    is_public: Optional[bool] = None

class ResumeInDB(ResumeBase):
    id: PydanticObjectId
    user_id: PydanticObjectId
    file_path: Optional[str] = None
    file_name: Optional[str] = None
    file_size: Optional[int] = None
    ats_score: Optional[int] = None
    analysis_results: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class Resume(ResumeInDB):
    pass

class ResumeAnalysisBase(BaseModel):
    analysis_type: str = Field(..., min_length=1, max_length=50)
    score: int = Field(..., ge=0, le=100)
    details: Optional[Dict[str, Any]] = None
    recommendations: Optional[Dict[str, Any]] = None

class ResumeAnalysisCreate(ResumeAnalysisBase):
    resume_id: PydanticObjectId
    job_posting_id: Optional[PydanticObjectId] = None

class ResumeAnalysisInDB(ResumeAnalysisBase):
    id: PydanticObjectId
    resume_id: PydanticObjectId
    job_posting_id: Optional[PydanticObjectId] = None
    created_at: datetime

    class Config:
        from_attributes = True

class ResumeAnalysis(ResumeAnalysisInDB):
    pass

class ResumeUpload(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    is_public: bool = False

class ResumeAnalysisRequest(BaseModel):
    resume_id: PydanticObjectId
    job_posting_id: Optional[PydanticObjectId] = None
    analysis_type: str = Field(..., min_length=1, max_length=50)
