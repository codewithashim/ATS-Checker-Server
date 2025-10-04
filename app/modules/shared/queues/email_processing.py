import asyncio
from typing import Dict, Any
from app.core.queue import queue_manager
from app.modules.shared.services.email_service import send_verification_email, send_password_reset_email
import logging

logger = logging.getLogger(__name__)

class EmailProcessingQueue:
    QUEUE_NAME = "email_processing"
    
    @staticmethod
    async def add_verification_email_job(email: str, token: str):
        """Add a verification email job to the queue"""
        job_data = {
            "type": "verification",
            "email": email,
            "token": token,
            "created_at": asyncio.get_event_loop().time()
        }
        
        await queue_manager.add_job(
            EmailProcessingQueue.QUEUE_NAME,
            job_data,
            {"priority": 2, "delay": 0}
        )
        logger.info(f"Added verification email job for {email}")

    @staticmethod
    async def add_password_reset_email_job(email: str, token: str):
        """Add a password reset email job to the queue"""
        job_data = {
            "type": "password_reset",
            "email": email,
            "token": token,
            "created_at": asyncio.get_event_loop().time()
        }
        
        await queue_manager.add_job(
            EmailProcessingQueue.QUEUE_NAME,
            job_data,
            {"priority": 2, "delay": 0}
        )
        logger.info(f"Added password reset email job for {email}")

    @staticmethod
    async def process_email(job_data: Dict[str, Any]):
        """Process an email from the queue"""
        email_type = job_data.get("type")
        email = job_data.get("email")
        token = job_data.get("token")
        
        try:
            if email_type == "verification":
                await send_verification_email(email, token)
                logger.info(f"Sent verification email to {email}")
            elif email_type == "password_reset":
                await send_password_reset_email(email, token)
                logger.info(f"Sent password reset email to {email}")
            else:
                logger.warning(f"Unknown email type: {email_type}")
                
        except Exception as e:
            logger.error(f"Failed to send {email_type} email to {email}: {e}")
            raise
