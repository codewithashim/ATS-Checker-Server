from fastapi import APIRouter, Depends, HTTPException, status, Query
from beanie import PydanticObjectId
from typing import List, Optional

from app.modules.job_posting.schemas import JobPosting, JobPostingCreate, JobPostingUpdate, JobPostingSearch
from app.modules.job_posting.services import JobPostingService
from app.modules.auth.endpoints import get_current_user
from app.modules.auth.schemas import User

router = APIRouter()

@router.post("/", response_model=JobPosting)
async def create_job_posting(
    job_data: JobPostingCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new job posting (recruiters only)"""
    if current_user.role != "recruiter":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only recruiters can create job postings"
        )
    
    return await JobPostingService.create_job_posting(current_user.id, job_data)

@router.get("/", response_model=List[JobPosting])
async def get_job_postings(
    query: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    employment_type: Optional[str] = Query(None),
    remote_allowed: Optional[bool] = Query(None),
    salary_min: Optional[int] = Query(None),
    salary_max: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100)
):
    """Get job postings with search and filters"""
    search_params = JobPostingSearch(
        query=query,
        location=location,
        employment_type=employment_type,
        remote_allowed=remote_allowed,
        salary_min=salary_min,
        salary_max=salary_max,
        page=page,
        limit=limit
    )
    
    return await JobPostingService.search_job_postings(search_params)

@router.get("/my", response_model=List[JobPosting])
async def get_my_job_postings(current_user: User = Depends(get_current_user)):
    """Get current user's job postings (recruiters only)"""
    if current_user.role != "recruiter":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only recruiters can view their job postings"
        )
    
    return await JobPostingService.get_user_job_postings(current_user.id)

@router.get("/{job_id}", response_model=JobPosting)
async def get_job_posting(job_id: PydanticObjectId):
    """Get specific job posting"""
    job_posting = await JobPostingService.get_active_job_posting(job_id)
    
    if not job_posting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job posting not found"
        )
    
    return job_posting

@router.put("/{job_id}", response_model=JobPosting)
async def update_job_posting(
    job_id: PydanticObjectId,
    job_update: JobPostingUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update job posting (owner only)"""
    job_posting = await JobPostingService.update_job_posting(job_id, current_user.id, job_update)
    
    if not job_posting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job posting not found"
        )
    
    return job_posting

@router.delete("/{job_id}")
async def delete_job_posting(
    job_id: PydanticObjectId,
    current_user: User = Depends(get_current_user)
):
    """Delete job posting (owner only)"""
    success = await JobPostingService.delete_job_posting(job_id, current_user.id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job posting not found"
        )
    
    return {"message": "Job posting deleted successfully"}
