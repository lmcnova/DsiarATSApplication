
from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client["chatdb"]
users_collection = db["users"]
messages_collection = db["messages"]
