# database.py
from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client["Avarta"]
users_collection = db["Users_Credentials"]
