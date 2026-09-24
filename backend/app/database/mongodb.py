# app/database/mongodb.py

import os

from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

MONGODB_URI = os.getenv(
    "MONGODB_URI",
    "mongodb://mongodb:27017"
)

MONGODB_DATABASE = os.getenv(
    "MONGODB_DATABASE",
    "cedetec"
)

client = MongoClient(MONGODB_URI)

db: Database = client[MONGODB_DATABASE]

documentos: Collection = db["documentos"]

conversaciones: Collection = db["conversaciones"]