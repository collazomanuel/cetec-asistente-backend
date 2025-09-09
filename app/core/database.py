from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings

class Database:
    client: AsyncIOMotorClient = None
    database = None

db = Database()

async def get_database():
    return db.database

async def connect_to_mongo():
    """Create database connection"""
    db.client = AsyncIOMotorClient(settings.MONGODB_URI)
    db.database = db.client[settings.DB_NAME]

async def close_mongo_connection():
    """Close database connection"""
    if db.client:
        db.client.close()
