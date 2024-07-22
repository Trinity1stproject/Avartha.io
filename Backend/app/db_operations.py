# app/db_operations.py

from werkzeug.security import generate_password_hash, check_password_hash
from pymongo import MongoClient

# Connect to MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['Avarta']
users_collection = db['Users_Credentials']

def register_user(email: str, password: str):
    hashed_password = generate_password_hash(password)
    user = {
        'email': email,
        'password': hashed_password
    }
    result = users_collection.insert_one(user)
    return result.inserted_id

def authenticate_user(email: str, password: str) -> bool:
    user = users_collection.find_one({'email': email})
    if user and check_password_hash(user['password'], password):
        return True
    return False
