from fastapi import APIRouter
from app.modules.auth.endpoints import router as auth_router
from app.modules.resume.endpoints import router as resume_router
from app.modules.job_posting.endpoints import router as job_posting_router
from app.modules.shared.endpoints.queue_monitoring import router as queue_router
from app.modules.shared.endpoints.ai_analysis import router as ai_router

api_router = APIRouter()

api_router.include_router(auth_router, prefix="/auth", tags=["authentication"])
api_router.include_router(resume_router, prefix="/resumes", tags=["resumes"])
api_router.include_router(job_posting_router, prefix="/job-postings", tags=["job-postings"])
api_router.include_router(queue_router, prefix="/queues", tags=["queue-monitoring"])
api_router.include_router(ai_router, prefix="/ai", tags=["ai-analysis"])
