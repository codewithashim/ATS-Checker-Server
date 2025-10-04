from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any
from app.modules.shared.workers.queue_worker import queue_worker
from app.modules.auth.endpoints import get_current_user
from app.modules.auth.schemas import User

router = APIRouter()

@router.get("/stats")
async def get_queue_stats(current_user: User = Depends(get_current_user)):
    """Get queue statistics (admin only)"""
    # In production, you might want to add admin role check
    if current_user.role != "recruiter":  # Using recruiter as admin for now
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    stats = await queue_worker.get_queue_stats()
    return {
        "queues": stats,
        "total_jobs": sum(queue_stats["waiting"] + queue_stats["active"] + queue_stats["completed"] + queue_stats["failed"] 
                         for queue_stats in stats.values())
    }

@router.get("/health")
async def get_queue_health():
    """Get queue health status"""
    try:
        stats = await queue_worker.get_queue_stats()
        return {
            "status": "healthy",
            "queues": list(stats.keys()),
            "message": "Queue system is running"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "message": "Queue system is not responding"
        }
