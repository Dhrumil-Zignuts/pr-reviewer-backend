import asyncio
import logging
from app.db.session import engine
from app.models.base import Base

# Import all models
from app.models.user import User

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def init_db():
    async with engine.begin() as conn:
        # For development purposes, you might want to drop all tables first
        # await conn.run_sync(Base.metadata.drop_all)
        logger.info("Creating tables...")
        await conn.run_sync(Base.metadata.create_all)
        logger.info("Tables created successfully.")


if __name__ == "__main__":
    asyncio.run(init_db())
