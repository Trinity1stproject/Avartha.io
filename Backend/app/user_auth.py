import pymongo
import hashlib

class UserAuth:
    def __init__(self, db_uri="mongodb://localhost:27017/", db_name="Avarta"):
        self.client = pymongo.MongoClient(db_uri)
        self.db = self.client[db_name]
        self.collection = self.db["Users_Credentials"]

    def hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

    def register(self, email: str, password: str):
        hashed_password = self.hash_password(password)
        
        if self.collection.find_one({"email": email}):
            return False, "Email already registered. Please login."
        
        self.collection.insert_one({"email": email, "password": hashed_password})
        return True, "Registration successful!"

    def login(self, email: str, password: str):
        hashed_password = self.hash_password(password)
        
        user = self.collection.find_one({"email": email, "password": hashed_password})
        
        if user:
            return True
        else:
            return False
