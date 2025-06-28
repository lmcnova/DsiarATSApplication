
from flask import Blueprint, request, jsonify
from db import users_collection
import bcrypt

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/signup', methods=['POST'])
def signup():
    data = request.json
    if users_collection.find_one({"username": data['username']}):
        return jsonify({"error": "User already exists"}), 400
    hashed_pw = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt())
    users_collection.insert_one({
        "username": data['username'],
        "email": data['email'],
        "password": hashed_pw
    })
    return jsonify({"message": "User created"})

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.json
    user = users_collection.find_one({"username": data['username']})
    if user and bcrypt.checkpw(data['password'].encode('utf-8'), user['password']):
        return jsonify({"message": "Login successful", "username": user['username']})
    return jsonify({"error": "Invalid credentials"}), 401
