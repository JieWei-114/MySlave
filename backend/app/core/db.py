import logging

from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

from app.config.settings import settings

logger = logging.getLogger(__name__)

try:
    client = MongoClient(
        settings.MONGO_URI,
        serverSelectionTimeoutMS=settings.MONGO_SERVER_SELECTION_TIMEOUT_MS,
        maxPoolSize=settings.MONGO_MAX_POOL_SIZE,
        minPoolSize=settings.MONGO_MIN_POOL_SIZE,
        directConnection=True,
    )
    # Test connection
    client.admin.command('ping')
    logger.info('MongoDB connection established successfully')
    db = client[settings.DB_NAME]

except ConnectionFailure as e:
    logger.error(f'MongoDB connection failed: {e}')
    raise Exception('Failed to connect to MongoDB. Please ensure MongoDB is running.')

sessions_collection = db['sessions']
memories_collection = db['memories']
serper_quota_collection = db['serper_quota']
tavily_quota_collection = db['tavily_quota']
rules_collection = db['rules']
