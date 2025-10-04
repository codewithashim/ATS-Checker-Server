from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings
from app.modules.auth.models import User
from app.modules.resume.models import Resume, ResumeAnalysis
from app.modules.job_posting.models import JobPosting

class Database:
    client: AsyncIOMotorClient = None
    database = None

db = Database()

async def init_db():
    """Initialize database connection and collections"""
    db.client = AsyncIOMotorClient(settings.MONGODB_URL)
    db.database = db.client.ats_checker
    
    # Initialize Beanie with the document models
    await init_beanie(
        database=db.database,
        document_models=[
            User,
            Resume,
            ResumeAnalysis,
            JobPosting,
        ]
    )

async def close_db():
    """Close database connection"""
    if db.client:
        db.client.close()

def get_database():
    """Get database instance"""
    return db.database