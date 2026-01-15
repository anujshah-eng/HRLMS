import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient

# Use the URI provided by the user
MONGO_URI = "mongodb+srv://nagarjunts_db_user:HRMS1234@hrms.xr3lreu.mongodb.net/?appName=hrms"
DB_NAME = "ai_interview"
COLLECTION_NAME = "ai_interviewers"

DEFAULT_INTERVIEWERS = [
    {
        "id": 1,
        "name": "Priya Sharma",
        "voice_id": "shimmer",
        "gender": "Female",
        "accent": "Indian English",
        "description": "Experienced technical interviewer with expertise in software engineering",
        "is_active": True,
        "greet_video": None, "video_blink_1": None, "video_blink_2": None, "video_dubb": None, "img": None
    },
    {
        "id": 2,
        "name": "Sarah Johnson",
        "voice_id": "coral",
        "gender": "Female",
        "accent": "US English",
        "description": "Senior HR interviewer specializing in behavioral assessments",
        "is_active": True,
        "greet_video": None, "video_blink_1": None, "video_blink_2": None, "video_dubb": None, "img": None
    },
    {
        "id": 3,
        "name": "Arjun Patel",
        "voice_id": "echo",
        "gender": "Male",
        "accent": "Indian English",
        "description": "Tech lead with focus on system design interviews",
        "is_active": True,
        "greet_video": None, "video_blink_1": None, "video_blink_2": None, "video_dubb": None, "img": None
    },
    {
        "id": 4,
        "name": "Michael Chen",
        "voice_id": "alloy",
        "gender": "Male",
        "accent": "US English",
        "description": "Engineering manager focused on leadership and technical skills",
        "is_active": True,
        "greet_video": None, "video_blink_1": None, "video_blink_2": None, "video_dubb": None, "img": None
    }
]

async def seed_data():
    client = AsyncIOMotorClient(MONGO_URI)
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]

    # Check connection
    try:
        await db.command("ping")
        print(f"Connected to MongoDB: {DB_NAME}")
    except Exception as e:
        print(f"Connection failed: {e}")
        return

    # Check for existing data
    count = await collection.count_documents({})
    print(f"Current document count in '{COLLECTION_NAME}': {count}")

    if count == 0:
        print("Collection is empty. Seeding default interviewers...")
        result = await collection.insert_many(DEFAULT_INTERVIEWERS)
        print(f"Successfully inserted {len(result.inserted_ids)} interviewers.")
    else:
        print("Collection already has data. Skipping seed.")
        # Print existing IDs
        async for doc in collection.find({}, {"id": 1, "name": 1}):
            print(f" - Found: {doc.get('name')} (ID: {doc.get('id')})")

    client.close()

if __name__ == "__main__":
    asyncio.run(seed_data())
