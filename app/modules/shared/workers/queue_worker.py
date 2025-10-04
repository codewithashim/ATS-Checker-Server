import asyncio
import logging
from typing import Dict, Any
from app.core.queue import queue_manager
from app.modules.shared.queues.file_processing import FileProcessingQueue
from app.modules.shared.queues.email_processing import EmailProcessingQueue

logger = logging.getLogger(__name__)

class QueueWorker:
    def __init__(self):
        self.running = False
        self.workers = {
            "file_processing": FileProcessingQueue.process_file,
            "email_processing": EmailProcessingQueue.process_email
        }

    async def start(self):
        """Start the queue worker"""
        self.running = True
        logger.info("Starting queue worker...")
        
        # Connect to Redis
        await queue_manager.connect()
        
        # Start worker tasks
        tasks = []
        for queue_name in self.workers.keys():
            task = asyncio.create_task(self._process_queue(queue_name))
            tasks.append(task)
        
        # Wait for all tasks
        await asyncio.gather(*tasks)

    async def stop(self):
        """Stop the queue worker"""
        self.running = False
        logger.info("Stopping queue worker...")
        await queue_manager.disconnect()

    async def _process_queue(self, queue_name: str):
        """Process jobs from a specific queue"""
        logger.info(f"Starting worker for queue: {queue_name}")
        
        while self.running:
            try:
                # Get job from queue
                job_data = await queue_manager.get_job(queue_name)
                
                if job_data:
                    logger.info(f"Processing job from queue {queue_name}")
                    
                    try:
                        # Process the job
                        await self.workers[queue_name](job_data)
                        logger.info(f"Successfully processed job from queue {queue_name}")
                        
                    except Exception as e:
                        logger.error(f"Failed to process job from queue {queue_name}: {e}")
                        # In a real implementation, you might want to retry or move to failed queue
                        
                else:
                    # No jobs available, wait a bit
                    await asyncio.sleep(1)
                    
            except Exception as e:
                logger.error(f"Error processing queue {queue_name}: {e}")
                await asyncio.sleep(5)  # Wait before retrying

    async def get_queue_stats(self) -> Dict[str, Dict[str, int]]:
        """Get statistics for all queues"""
        stats = {}
        for queue_name in self.workers.keys():
            stats[queue_name] = await queue_manager.get_queue_stats(queue_name)
        return stats

# Global worker instance
queue_worker = QueueWorker()
