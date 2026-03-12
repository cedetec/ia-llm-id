#mongo.py
from pymongo import MongoClient
import gridfs
import os

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")

client = MongoClient(MONGO_URI)

db = client["asistenteID"]

# documentos originales
documents_collection = db["documentos"]

# texto limpio
clean_collection = db["concursos_limpios"]

# chunks intermedios (opcional)
chunks_collection = db["chunks"]

# 🔴 ESTA ES LA IMPORTANTE (RAG REAL)
index_collection = db["indexados"]

# PDFs
fs = gridfs.GridFS(db)
