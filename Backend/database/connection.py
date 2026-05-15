from pymongo import AsyncMongoClient
from Backend.core.config import get_settings

class Database:
    client: AsyncMongoClient = None
    db = None

db_instance = Database()

async def connect_db():
    settings = get_settings()
    db_instance.client = AsyncMongoClient(settings.mongodb_url)
    db_instance.db = db_instance.client[settings.database_name]

async def close_db():
    if db_instance.client:
        await db_instance.client.close()

def get_database():
    return db_instance.db
