
from pymongo import MongoClient

client = MongoClient(
        'mongodb+srv://vrvimalraj04:s1WarkceHiLQ47jh@cluster0.edetq.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0',
        tls=True,
    tlsAllowInvalidCertificates=True,
    tlsAllowInvalidHostnames=True,
    )
db = client["chatdb"]
users_collection = db["users"]
messages_collection = db["messages"]
