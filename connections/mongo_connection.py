import os
from urllib.parse import quote_plus
from motor.motor_asyncio import AsyncIOMotorClient
from config.env_loader import load_env

load_env()

class MotorMongoDBResourceManager:
    """
    Async MongoDB Resource Manager using Motor.
    - Connects lazily to MongoDB inside FastAPI lifespan
    - Supports clean shutdown
    - Includes a ping test to fail fast if MongoDB is unreachable
    """
    def __init__(self):
        self.client: AsyncIOMotorClient | None = None
        self.db = None

        self.db_name = os.getenv("MONGO_DB_NAME")
        username = quote_plus(os.getenv("MONGO_USER"))
        password = os.getenv("MONGO_PASSWORD")
        cluster = os.getenv("MONGO_CLUSTER")
        app_name = os.getenv("MONGO_APP_NAME")

        self.uri = (
            f"mongodb+srv://{username}:{password}@{cluster}/"
            f"?retryWrites=true&w=majority&appName={app_name}"
        )

    async def connect(self):
        """Connect to MongoDB and test connection"""
        self.client = AsyncIOMotorClient(
            self.uri,
            serverSelectionTimeoutMS=5000  # 5s timeout
        )
        self.db = self.client[self.db_name]

        # Test connection
        try:
            await self.db.command("ping")
            print(f"MongoDB connected to database '{self.db_name}'")
        except Exception as e:
            raise ConnectionError(f"MongoDB connection failed: {e}") from e

    def close(self):
        """Close MongoDB client"""
        if self.client:
            self.client.close()
            print("MongoDB connection closed")
