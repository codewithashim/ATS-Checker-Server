from beanie import PydanticObjectId
from app.modules.auth.models import User
from app.modules.auth.schemas import UserCreate, UserUpdate
from typing import Optional, List
from datetime import datetime

class UserService:
    @staticmethod
    async def create_user(user_data: UserCreate, hashed_password: str) -> User:
        """Create a new user"""
        user = User(
            name=user_data.name,
            email=user_data.email,
            hashed_password=hashed_password,
            role=user_data.role
        )
        await user.insert()
        return user

    @staticmethod
    async def get_user_by_id(user_id: PydanticObjectId) -> Optional[User]:
        """Get user by ID"""
        return await User.get(user_id)

    @staticmethod
    async def get_user_by_email(email: str) -> Optional[User]:
        """Get user by email"""
        return await User.find_one(User.email == email)

    @staticmethod
    async def update_user(user_id: PydanticObjectId, user_data: UserUpdate) -> Optional[User]:
        """Update user"""
        user = await User.get(user_id)
        if not user:
            return None
        
        update_data = user_data.dict(exclude_unset=True)
        if update_data:
            update_data["updated_at"] = datetime.utcnow()
            await user.update({"$set": update_data})
        
        return await User.get(user_id)

    @staticmethod
    async def delete_user(user_id: PydanticObjectId) -> bool:
        """Soft delete user"""
        user = await User.get(user_id)
        if not user:
            return False
        
        await user.update({"$set": {"is_active": False, "updated_at": datetime.utcnow()}})
        return True

    @staticmethod
    async def update_last_login(user_id: PydanticObjectId) -> None:
        """Update user's last login time"""
        await User.find_one(User.id == user_id).update(
            {"$set": {"last_login": datetime.utcnow()}}
        )

    @staticmethod
    async def verify_email(user_id: PydanticObjectId) -> bool:
        """Mark user email as verified"""
        user = await User.get(user_id)
        if not user:
            return False
        
        await user.update({"$set": {"is_email_verified": True, "updated_at": datetime.utcnow()}})
        return True

    @staticmethod
    async def get_user_stats(user_id: PydanticObjectId) -> dict:
        """Get user statistics"""
        from app.modules.resume.models import Resume
        from app.modules.job_posting.models import JobPosting
        
        user = await User.get(user_id)
        if not user:
            return {}
        
        # Count resumes
        resume_count = await Resume.find(Resume.user_id == user_id).count()
        
        # Count job postings (for recruiters)
        job_posting_count = 0
        if user.role == "recruiter":
            job_posting_count = await JobPosting.find(JobPosting.user_id == user_id).count()
        
        return {
            "resume_count": resume_count,
            "job_posting_count": job_posting_count,
            "account_created": user.created_at,
            "last_login": user.last_login
        }
