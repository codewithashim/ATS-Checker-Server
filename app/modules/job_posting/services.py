from beanie import PydanticObjectId
from app.modules.job_posting.models import JobPosting
from app.modules.job_posting.schemas import JobPostingCreate, JobPostingUpdate, JobPostingSearch
from typing import Optional, List
from datetime import datetime

class JobPostingService:
    @staticmethod
    async def create_job_posting(user_id: PydanticObjectId, job_data: JobPostingCreate) -> JobPosting:
        """Create a new job posting"""
        job_posting = JobPosting(
            user_id=user_id,
            title=job_data.title,
            company=job_data.company,
            description=job_data.description,
            requirements=job_data.requirements,
            location=job_data.location,
            salary_min=job_data.salary_min,
            salary_max=job_data.salary_max,
            employment_type=job_data.employment_type,
            remote_allowed=job_data.remote_allowed
        )
        await job_posting.insert()
        return job_posting

    @staticmethod
    async def get_job_posting_by_id(job_id: PydanticObjectId) -> Optional[JobPosting]:
        """Get job posting by ID"""
        return await JobPosting.get(job_id)

    @staticmethod
    async def get_user_job_postings(user_id: PydanticObjectId) -> List[JobPosting]:
        """Get all job postings for a user"""
        return await JobPosting.find(JobPosting.user_id == user_id).to_list()

    @staticmethod
    async def search_job_postings(search_params: JobPostingSearch) -> List[JobPosting]:
        """Search job postings with filters"""
        query = JobPosting.find(JobPosting.is_active == True)
        
        # Apply search filters
        if search_params.query:
            query = query.find({
                "$or": [
                    {"title": {"$regex": search_params.query, "$options": "i"}},
                    {"company": {"$regex": search_params.query, "$options": "i"}},
                    {"description": {"$regex": search_params.query, "$options": "i"}}
                ]
            })
        
        if search_params.location:
            query = query.find({"location": {"$regex": search_params.location, "$options": "i"}})
        
        if search_params.employment_type:
            query = query.find({"employment_type": search_params.employment_type})
        
        if search_params.remote_allowed is not None:
            query = query.find({"remote_allowed": search_params.remote_allowed})
        
        if search_params.salary_min:
            query = query.find({"salary_min": {"$gte": search_params.salary_min}})
        
        if search_params.salary_max:
            query = query.find({"salary_max": {"$lte": search_params.salary_max}})
        
        # Apply pagination
        skip = (search_params.page - 1) * search_params.limit
        return await query.skip(skip).limit(search_params.limit).to_list()

    @staticmethod
    async def update_job_posting(
        job_id: PydanticObjectId, 
        user_id: PydanticObjectId, 
        job_data: JobPostingUpdate
    ) -> Optional[JobPosting]:
        """Update job posting"""
        job_posting = await JobPosting.find_one(JobPosting.id == job_id, JobPosting.user_id == user_id)
        if not job_posting:
            return None
        
        update_data = job_data.dict(exclude_unset=True)
        if update_data:
            update_data["updated_at"] = datetime.utcnow()
            await job_posting.update({"$set": update_data})
        
        return await JobPosting.get(job_id)

    @staticmethod
    async def delete_job_posting(job_id: PydanticObjectId, user_id: PydanticObjectId) -> bool:
        """Soft delete job posting"""
        job_posting = await JobPosting.find_one(JobPosting.id == job_id, JobPosting.user_id == user_id)
        if not job_posting:
            return False
        
        await job_posting.update({"$set": {"is_active": False, "updated_at": datetime.utcnow()}})
        return True

    @staticmethod
    async def get_active_job_posting(job_id: PydanticObjectId) -> Optional[JobPosting]:
        """Get active job posting by ID"""
        return await JobPosting.find_one(JobPosting.id == job_id, JobPosting.is_active == True)
