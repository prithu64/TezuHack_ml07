import os
from pathlib import Path

from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv(Path(__file__).with_name(".env"))

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "student_support")
MONGODB_COLLECTION = os.getenv("MONGODB_COLLECTION", "predictions")

client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=2000)
database = client[MONGODB_DATABASE]
predictions_collection = database[MONGODB_COLLECTION]


def check_database_connection() -> None:
    client.admin.command("ping")
