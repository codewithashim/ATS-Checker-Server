import asyncio
import signal
import logging
from app.modules.shared.workers.queue_worker import queue_worker

logger = logging.getLogger(__name__)

class WorkerManager:
    def __init__(self):
        self.worker = queue_worker
        self.shutdown_event = asyncio.Event()

    async def start(self):
        """Start the worker manager"""
        logger.info("Starting worker manager...")
        
        # Set up signal handlers for graceful shutdown
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, initiating shutdown...")
            self.shutdown_event.set()
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        try:
            # Start the queue worker
            await self.worker.start()
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt, shutting down...")
        finally:
            await self.shutdown()

    async def shutdown(self):
        """Shutdown the worker manager gracefully"""
        logger.info("Shutting down worker manager...")
        await self.worker.stop()
        logger.info("Worker manager shutdown complete")

    async def get_stats(self):
        """Get worker statistics"""
        return await self.worker.get_queue_stats()

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Start the worker manager
    manager = WorkerManager()
    asyncio.run(manager.start())
