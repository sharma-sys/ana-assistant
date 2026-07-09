import time
import logging
from scheduler.jobs import scheduler
from database.session import Base, engine

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("worker")

if __name__ == "__main__":
    logger.info("Starting isolated scheduler worker...")
    # Ensure tables exist (Removed for production, use alembic)
    # Base.metadata.create_all(bind=engine)
    
    scheduler.start()
    
    try:
        while True:
            time.sleep(60)
    except (KeyboardInterrupt, SystemExit):
        logger.info("Shutting down worker...")
        scheduler.shutdown()
