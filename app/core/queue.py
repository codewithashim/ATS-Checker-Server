import asyncio
import json
import redis.asyncio as redis
from typing import Dict, Any, Optional
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class QueueManager:
    def __init__(self):
        self.redis_connection: Optional[redis.Redis] = None
        self.queues: Dict[str, Any] = {}

    async def connect(self):
        """Connect to Redis"""
        try:
            self.redis_connection = redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )
            logger.info("Connected to Redis for queue processing")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise

    async def disconnect(self):
        """Disconnect from Redis"""
        if self.redis_connection:
            await self.redis_connection.close()
            logger.info("Disconnected from Redis")

    async def add_job(self, queue_name: str, job_data: Dict[str, Any], options: Dict[str, Any] = None):
        """Add a job to the specified queue"""
        if not self.redis_connection:
            await self.connect()
        
        try:
            # Create job payload
            job_payload = {
                "data": job_data,
                "options": options or {},
                "id": f"{queue_name}_{asyncio.get_event_loop().time()}"
            }
            
            # Add job to Redis list
            await self.redis_connection.lpush(f"bull:{queue_name}:waiting", json.dumps(job_payload))
            logger.info(f"Added job to queue {queue_name}: {job_data}")
            
        except Exception as e:
            logger.error(f"Failed to add job to queue {queue_name}: {e}")
            raise

    async def get_job(self, queue_name: str) -> Optional[Dict[str, Any]]:
        """Get a job from the specified queue"""
        if not self.redis_connection:
            await self.connect()
        
        try:
            # Get job from Redis list (blocking pop)
            result = await self.redis_connection.brpop(f"bull:{queue_name}:waiting", timeout=1)
            if result:
                _, job_payload = result
                return json.loads(job_payload)
            return None
            
        except Exception as e:
            logger.error(f"Failed to get job from queue {queue_name}: {e}")
            return None

    async def complete_job(self, queue_name: str, job_id: str, result: Dict[str, Any] = None):
        """Mark a job as completed"""
        if not self.redis_connection:
            await self.connect()
        
        try:
            # Move job to completed list
            job_data = {
                "id": job_id,
                "result": result or {},
                "completed_at": asyncio.get_event_loop().time()
            }
            await self.redis_connection.lpush(f"bull:{queue_name}:completed", json.dumps(job_data))
            logger.info(f"Completed job {job_id} in queue {queue_name}")
            
        except Exception as e:
            logger.error(f"Failed to complete job {job_id} in queue {queue_name}: {e}")

    async def fail_job(self, queue_name: str, job_id: str, error: str):
        """Mark a job as failed"""
        if not self.redis_connection:
            await self.connect()
        
        try:
            # Move job to failed list
            job_data = {
                "id": job_id,
                "error": error,
                "failed_at": asyncio.get_event_loop().time()
            }
            await self.redis_connection.lpush(f"bull:{queue_name}:failed", json.dumps(job_data))
            logger.error(f"Failed job {job_id} in queue {queue_name}: {error}")
            
        except Exception as e:
            logger.error(f"Failed to mark job {job_id} as failed in queue {queue_name}: {e}")

    async def get_queue_stats(self, queue_name: str) -> Dict[str, int]:
        """Get queue statistics"""
        if not self.redis_connection:
            await self.connect()
        
        try:
            waiting = await self.redis_connection.llen(f"bull:{queue_name}:waiting")
            active = await self.redis_connection.llen(f"bull:{queue_name}:active")
            completed = await self.redis_connection.llen(f"bull:{queue_name}:completed")
            failed = await self.redis_connection.llen(f"bull:{queue_name}:failed")
            
            return {
                "waiting": waiting,
                "active": active,
                "completed": completed,
                "failed": failed
            }
            
        except Exception as e:
            logger.error(f"Failed to get queue stats for {queue_name}: {e}")
            return {"waiting": 0, "active": 0, "completed": 0, "failed": 0}

# Global queue manager instance
queue_manager = QueueManager()
