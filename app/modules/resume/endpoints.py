from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from beanie import PydanticObjectId
from typing import List, Optional
import os
import aiofiles

from app.modules.resume.schemas import Resume, ResumeCreate, ResumeUpdate, ResumeAnalysis, ResumeAnalysisRequest
from app.modules.resume.services import ResumeService, ResumeAnalysisService
from app.modules.auth.endpoints import get_current_user
from app.modules.auth.schemas import User
from app.modules.shared.queues.file_processing import FileProcessingQueue

router = APIRouter()

# File upload directory
UPLOAD_DIR = "uploads/resumes"

@router.post("/", response_model=Resume)
async def create_resume(
    resume_data: ResumeCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new resume"""
    return await ResumeService.create_resume(current_user.id, resume_data)

@router.post("/upload", response_model=Resume)
async def upload_resume_file(
    file: UploadFile = File(...),
    title: str = Form(...),
    is_public: bool = Form(False),
    current_user: User = Depends(get_current_user)
):
    """Upload resume file"""
    # Validate file type
    if not file.filename.lower().endswith(('.pdf', '.doc', '.docx')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF, DOC, and DOCX files are allowed"
        )
    
    # Create upload directory if it doesn't exist
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    
    # Generate unique filename
    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"{current_user.id}_{title}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    
    # Save file
    async with aiofiles.open(file_path, 'wb') as f:
        content = await file.read()
        await f.write(content)
    
    # Create resume record
    resume = await ResumeService.upload_resume_file(
        current_user.id, title, file_path, file.filename, len(content), is_public
    )
    
    # Add file processing job to queue
    await FileProcessingQueue.add_file_processing_job(
        str(resume.id),
        file_path,
        "ats_check"
    )
    
    return resume

@router.get("/", response_model=List[Resume])
async def get_user_resumes(current_user: User = Depends(get_current_user)):
    """Get all resumes for current user"""
    return await ResumeService.get_user_resumes(current_user.id)

@router.get("/{resume_id}", response_model=Resume)
async def get_resume(
    resume_id: PydanticObjectId,
    current_user: User = Depends(get_current_user)
):
    """Get specific resume"""
    resume = await ResumeService.get_resume_by_id(resume_id)
    
    if not resume or resume.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found"
        )
    
    return resume

@router.put("/{resume_id}", response_model=Resume)
async def update_resume(
    resume_id: PydanticObjectId,
    resume_update: ResumeUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update resume"""
    resume = await ResumeService.update_resume(resume_id, current_user.id, resume_update)
    
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found"
        )
    
    return resume

@router.delete("/{resume_id}")
async def delete_resume(
    resume_id: PydanticObjectId,
    current_user: User = Depends(get_current_user)
):
    """Delete resume"""
    success = await ResumeService.delete_resume(resume_id, current_user.id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found"
        )
    
    return {"message": "Resume deleted successfully"}

@router.post("/{resume_id}/analyze", response_model=ResumeAnalysis)
async def analyze_resume(
    resume_id: PydanticObjectId,
    analysis_request: ResumeAnalysisRequest,
    current_user: User = Depends(get_current_user)
):
    """Analyze resume for ATS compatibility"""
    # Verify resume belongs to user
    resume = await ResumeService.get_resume_by_id(resume_id)
    if not resume or resume.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found"
        )
    
    # Create analysis record
    analysis_data = ResumeAnalysisCreate(
        resume_id=resume_id,
        job_posting_id=analysis_request.job_posting_id,
        analysis_type=analysis_request.analysis_type,
        score=0,  # Will be calculated by analysis service
        details={},
        recommendations={}
    )
    
    analysis = await ResumeAnalysisService.create_analysis(analysis_data)
    
    # Add analysis job to queue for background processing
    if resume.file_path:
        await FileProcessingQueue.add_file_processing_job(
            str(resume_id),
            resume.file_path,
            analysis_request.analysis_type,
            str(analysis_request.job_posting_id) if analysis_request.job_posting_id else None
        )
    else:
        # If no file, process the content directly with AI
        await FileProcessingQueue.perform_ai_ats_analysis(analysis, resume.content, str(analysis_request.job_posting_id) if analysis_request.job_posting_id else None)
    
    return analysis

@router.get("/{resume_id}/analyses", response_model=List[ResumeAnalysis])
async def get_resume_analyses(
    resume_id: PydanticObjectId,
    current_user: User = Depends(get_current_user)
):
    """Get all analyses for a resume"""
    # Verify resume belongs to user
    resume = await ResumeService.get_resume_by_id(resume_id)
    if not resume or resume.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found"
        )
    
    return await ResumeAnalysisService.get_resume_analyses(resume_id)
