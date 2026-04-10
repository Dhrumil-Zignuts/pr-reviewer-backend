import asyncio
import logging
from app.db.session import AsyncSessionLocal
from app.repositories.user_repository import user_repository
from app.schemas.user import UserCreate

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def seed_data():
    async with AsyncSessionLocal() as db:
        # Create a superuser placeholder if it doesn't exist
        # Note: In a GitHub-only system, the superuser must eventually
        # be linked to a GitHub account during their first login.
        user = await user_repository.get_by_username(db, username="admin")
        if not user:
            logger.info("Creating superuser placeholder...")
            from app.models.user import User

            db_obj = User(
                username="admin",
                email="admin@example.com",
                is_superuser=True,
            )
            db.add(db_obj)
            await db.commit()
            logger.info("Superuser placeholder created successfully.")
        else:
            logger.info("Superuser already exists.")


if __name__ == "__main__":
    asyncio.run(seed_data())
