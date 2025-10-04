from fastapi import APIRouter, Depends, HTTPException, status
from beanie import PydanticObjectId
from typing import Dict, Any, List
from app.modules.shared.services.gemini_ai_service import gemini_ai_service
from app.modules.auth.endpoints import get_current_user
from app.modules.auth.schemas import User
from app.modules.resume.models import Resume
from app.modules.job_posting.models import JobPosting

router = APIRouter()

@router.post("/analyze-resume")
async def analyze_resume_with_ai(
    resume_id: PydanticObjectId,
    job_posting_id: PydanticObjectId = None,
    current_user: User = Depends(get_current_user)
):
    """Analyze resume using AI without creating analysis record"""
    # Get resume
    resume = await Resume.find_one(Resume.id == resume_id, Resume.user_id == current_user.id)
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found"
        )
    
    # Get job description if provided
    job_description = None
    if job_posting_id:
        job_posting = await JobPosting.get(job_posting_id)
        if job_posting:
            job_description = f"{job_posting.title} - {job_posting.description}"
    
    # Perform AI analysis
    analysis = await gemini_ai_service.analyze_resume_ats(resume.content, job_description)
    
    return {
        "resume_id": str(resume_id),
        "job_posting_id": str(job_posting_id) if job_posting_id else None,
        "analysis": analysis
    }

@router.post("/extract-keywords")
async def extract_keywords_with_ai(
    text: str,
    max_keywords: int = 20,
    current_user: User = Depends(get_current_user)
):
    """Extract keywords from text using AI"""
    if len(text) > 10000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Text too long. Maximum 10,000 characters allowed."
        )
    
    keywords = await gemini_ai_service.extract_keywords(text, max_keywords)
    
    return {
        "text_length": len(text),
        "keywords": keywords,
        "keyword_count": len(keywords)
    }

@router.post("/improve-resume")
async def get_resume_improvement_suggestions(
    resume_id: PydanticObjectId,
    job_posting_id: PydanticObjectId = None,
    current_user: User = Depends(get_current_user)
):
    """Get AI-powered resume improvement suggestions"""
    # Get resume
    resume = await Resume.find_one(Resume.id == resume_id, Resume.user_id == current_user.id)
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found"
        )
    
    # Get job description if provided
    job_description = None
    if job_posting_id:
        job_posting = await JobPosting.get(job_posting_id)
        if job_posting:
            job_description = f"{job_posting.title} - {job_posting.description}"
    
    # Get improvement suggestions
    suggestions = await gemini_ai_service.improve_resume_suggestions(resume.content, job_description)
    
    return {
        "resume_id": str(resume_id),
        "job_posting_id": str(job_posting_id) if job_posting_id else None,
        "suggestions": suggestions
    }

@router.post("/match-job")
async def match_resume_to_job(
    resume_id: PydanticObjectId,
    job_posting_id: PydanticObjectId,
    current_user: User = Depends(get_current_user)
):
    """Match resume against specific job posting using AI"""
    # Get resume
    resume = await Resume.find_one(Resume.id == resume_id, Resume.user_id == current_user.id)
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found"
        )
    
    # Get job posting
    job_posting = await JobPosting.get(job_posting_id)
    if not job_posting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job posting not found"
        )
    
    job_description = f"{job_posting.title} - {job_posting.description}"
    
    # Perform job matching
    match_analysis = await gemini_ai_service.match_resume_to_job(resume.content, job_description)
    
    return {
        "resume_id": str(resume_id),
        "job_posting_id": str(job_posting_id),
        "match_analysis": match_analysis
    }

@router.get("/ai-status")
async def get_ai_status():
    """Check if AI services are available"""
    return {
        "ai_available": gemini_ai_service.model is not None,
        "model": "gemini-1.5-flash" if gemini_ai_service.model else None,
        "status": "active" if gemini_ai_service.model else "inactive"
    }
