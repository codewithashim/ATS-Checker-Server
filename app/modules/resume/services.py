from beanie import PydanticObjectId
from app.modules.resume.models import Resume, ResumeAnalysis
from app.modules.resume.schemas import ResumeCreate, ResumeUpdate, ResumeAnalysisCreate
from typing import Optional, List
from datetime import datetime

class ResumeService:
    @staticmethod
    async def create_resume(user_id: PydanticObjectId, resume_data: ResumeCreate) -> Resume:
        """Create a new resume"""
        resume = Resume(
            user_id=user_id,
            title=resume_data.title,
            content=resume_data.content,
            is_public=resume_data.is_public
        )
        await resume.insert()
        return resume

    @staticmethod
    async def get_resume_by_id(resume_id: PydanticObjectId) -> Optional[Resume]:
        """Get resume by ID"""
        return await Resume.get(resume_id)

    @staticmethod
    async def get_user_resumes(user_id: PydanticObjectId) -> List[Resume]:
        """Get all resumes for a user"""
        return await Resume.find(Resume.user_id == user_id).to_list()

    @staticmethod
    async def update_resume(resume_id: PydanticObjectId, user_id: PydanticObjectId, resume_data: ResumeUpdate) -> Optional[Resume]:
        """Update resume"""
        resume = await Resume.find_one(Resume.id == resume_id, Resume.user_id == user_id)
        if not resume:
            return None
        
        update_data = resume_data.dict(exclude_unset=True)
        if update_data:
            update_data["updated_at"] = datetime.utcnow()
            await resume.update({"$set": update_data})
        
        return await Resume.get(resume_id)

    @staticmethod
    async def delete_resume(resume_id: PydanticObjectId, user_id: PydanticObjectId) -> bool:
        """Delete resume"""
        resume = await Resume.find_one(Resume.id == resume_id, Resume.user_id == user_id)
        if not resume:
            return False
        
        # Delete associated analyses
        await ResumeAnalysis.find(ResumeAnalysis.resume_id == resume_id).delete()
        
        # Delete resume
        await resume.delete()
        return True

    @staticmethod
    async def upload_resume_file(
        user_id: PydanticObjectId, 
        title: str, 
        file_path: str, 
        file_name: str, 
        file_size: int,
        is_public: bool = False
    ) -> Resume:
        """Create resume from uploaded file"""
        resume = Resume(
            user_id=user_id,
            title=title,
            content="",  # Will be extracted from file later
            file_path=file_path,
            file_name=file_name,
            file_size=file_size,
            is_public=is_public
        )
        await resume.insert()
        return resume

class ResumeAnalysisService:
    @staticmethod
    async def create_analysis(analysis_data: ResumeAnalysisCreate) -> ResumeAnalysis:
        """Create a new resume analysis"""
        analysis = ResumeAnalysis(
            resume_id=analysis_data.resume_id,
            job_posting_id=analysis_data.job_posting_id,
            analysis_type=analysis_data.analysis_type,
            score=analysis_data.score,
            details=analysis_data.details,
            recommendations=analysis_data.recommendations
        )
        await analysis.insert()
        return analysis

    @staticmethod
    async def get_analysis_by_id(analysis_id: PydanticObjectId) -> Optional[ResumeAnalysis]:
        """Get analysis by ID"""
        return await ResumeAnalysis.get(analysis_id)

    @staticmethod
    async def get_resume_analyses(resume_id: PydanticObjectId) -> List[ResumeAnalysis]:
        """Get all analyses for a resume"""
        return await ResumeAnalysis.find(ResumeAnalysis.resume_id == resume_id).to_list()

    @staticmethod
    async def update_analysis(analysis_id: PydanticObjectId, update_data: dict) -> Optional[ResumeAnalysis]:
        """Update analysis results"""
        analysis = await ResumeAnalysis.get(analysis_id)
        if not analysis:
            return None
        
        await analysis.update({"$set": update_data})
        return await ResumeAnalysis.get(analysis_id)

    @staticmethod
    async def delete_analysis(analysis_id: PydanticObjectId) -> bool:
        """Delete analysis"""
        analysis = await ResumeAnalysis.get(analysis_id)
        if not analysis:
            return False
        
        await analysis.delete()
        return True
