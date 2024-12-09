import os
from dotenv import load_dotenv
from pymongo import MongoClient

# Muat file .env
load_dotenv()

class Config:
    # Konfigurasi Celery
    CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
    CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')

    # Konfigurasi lainnya
    SERVER = os.getenv('SERVER')
    DOC_ID = os.getenv('DOC_ID')
    API_KEY = os.getenv('API_KEY')
    MONGODB_URI = os.getenv('MONGODB_URI')

    def __init__(self):
        self.db = self.connect_to_mongodb()

    def connect_to_mongodb(self):
        try:
            client = MongoClient(self.MONGODB_URI)
            db = client.reservation
            client.server_info()  # Test koneksi ke MongoDB
            return db
        except Exception as e:
            print(f"Error connecting to MongoDB: {e}")
            return None
