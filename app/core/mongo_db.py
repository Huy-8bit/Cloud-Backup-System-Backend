from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings


# MONGO_INITDB_ROOT_USERNAME = ""
# MONGO_INITDB_ROOT_PASSWORD = ""
MONGO_HOST = "52.221.216.188"
MONGO_PORT = "27017"
MONGO_DATABASE = "cloud_backup"

# DATABASE_URL = f"mongodb://{MONGO_INITDB_ROOT_USERNAME}:{MONGO_INITDB_ROOT_PASSWORD}@{MONGO_HOST}:{MONGO_PORT}/{MONGO_DATABASE}?authSource=admin"

DATABASE_URL = f"mongodb://{MONGO_HOST}:{MONGO_PORT}/{MONGO_DATABASE}"

# DATABASE_URL = "mongodb://18.141.58.127:27017"

client = AsyncIOMotorClient(DATABASE_URL)

# Define the MongoDB database
database = client["cloud_backup"]
