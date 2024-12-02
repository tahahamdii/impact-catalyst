import os
from pymongo import MongoClient
from dotenv import load_dotenv
import logging
from typing import Dict

load_dotenv()

class MongoDBClient:
    def __init__(self):
        self.client = None
        self.db = None
        self.collections = {}

    def connect(self):
        if not self.client:
            MONGO_USER = os.getenv("MONGO_USER")
            MONGO_PASSWORD = os.getenv("MONGO_PASSWORD")
            MONGO_URI = os.getenv("MONGO_URI", f'mongodb+srv://{MONGO_USER}:{MONGO_PASSWORD}@cluster0.5sbsz.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0')
            DB_NAME = os.getenv("DB_NAME", "CCandGender")

            try:
                # Connect to MongoDB
                self.client = MongoClient(MONGO_URI)
                self.db = self.client[DB_NAME]

                self.collections = {
                    "embeddings": self.db['embeddings'],
                    "report": self.db['report'],
                    "community": self.db['community'],
                    "users": self.db['users'],
                    "projects": self.db['projects'],
                    "notifications": self.db['notifications']
                }

                print("MongoDB connection established.")
            except Exception as e:
                logging.error(f"Error connecting to MongoDB: {e}")
                raise Exception(f"Failed to connect to MongoDB: {e}")

    def get_collections(self) -> Dict[str, any]:
        if not self.client:
            self.connect()
        return self.collections

# Singleton instance of MongoDB client
mongo_client = MongoDBClient()
