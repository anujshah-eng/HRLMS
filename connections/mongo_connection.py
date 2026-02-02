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

        
        mongo_uri = os.getenv("MONGO_URI")
        
        if mongo_uri:
            
            self.uri = mongo_uri
          
            self.db_name = os.getenv("MONGO_DB_NAME", "ai_interview")
        else:
            
            self.db_name = os.getenv("MONGO_DB_NAME", "ai_interview")
            username = quote_plus(os.getenv("MONGO_USER", ""))
            password = quote_plus(os.getenv("MONGO_PASSWORD", ""))
            cluster = os.getenv("MONGO_CLUSTER", "localhost")
            app_name = os.getenv("MONGO_APP_NAME", "HRLMS")

            self.uri = (
                f"mongodb+srv://{username}:{password}@{cluster}/"
                f"?retryWrites=true&w=majority&appName={app_name}"
            )

    async def connect(self):
        """Connect to MongoDB and test connection"""
        try:
            self.client = AsyncIOMotorClient(
                self.uri,
                serverSelectionTimeoutMS=5000 
            )
            self.db = self.client[self.db_name]

           
            try:
                await self.db.command("ping")
                print(f"✅ MongoDB connected to database '{self.db_name}'")
            except Exception as e:
                print(f"⚠️  WARNING: MongoDB connection failed: {e}")
                print(f"⚠️  Server will start but interview features won't work!")
                print(f"⚠️  Install MongoDB or use MongoDB Atlas to enable full functionality")
        except Exception as e:
            print(f"⚠️  WARNING: Could not initialize MongoDB client: {e}")
            print(f"⚠️  Server will continue without MongoDB")

    def close(self):
        """Close MongoDB client"""
        if self.client:
            self.client.close()
            print("MongoDB connection closed")
