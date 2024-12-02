from fastapi import Depends
from api.models.database import mongo_client

# Dependency to get MongoDB collections
def get_collections():
    collections = mongo_client.get_collections()
    return collections
