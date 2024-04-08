from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings


MONGO_INITDB_ROOT_USERNAME = "root"
MONGO_INITDB_ROOT_PASSWORD = "examplepassword"
MONGO_HOST = "13.229.133.71"
MONGO_PORT = "27017"
MONGO_DATABASE = "cloud_backup"

DATABASE_URL = f"mongodb://{MONGO_INITDB_ROOT_USERNAME}:{MONGO_INITDB_ROOT_PASSWORD}@{MONGO_HOST}:{MONGO_PORT}/{MONGO_DATABASE}?authSource=admin"


# DATABASE_URL = "mongodb://localhost:27017"

client = AsyncIOMotorClient(DATABASE_URL)

# Define the MongoDB database
database = client["cloud_backup"]
