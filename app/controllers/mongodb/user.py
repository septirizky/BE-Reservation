from flask import Blueprint, request, jsonify, current_app
import os
import jwt
import random
import requests
import json
from bson import ObjectId
from datetime import datetime, timedelta
import pytz 
from app.middleware import role_required

user_controller = Blueprint("user_controller", __name__)

WA_URI = os.getenv('WA_URI')
WA_TOKEN = os.getenv('WA_TOKEN')

SECRET_KEY = os.getenv("SECRET_KEY", "my_secret_key")

def generate_jwt(payload):
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

def generate_otp():
    return str(random.randint(100000, 999999))

def send_otp_via_whatsapp(phone, otp):
    url = WA_URI
    headers = {
        "Authorization": f"Bearer {WA_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": phone,
        "type": "template",
        "template": {
            "name": "otp_template_code",
            "language": {
                "code": "id"
            },
            "components": [
                {
                    "type": "body",
                    "parameters": [
                        {
                            "type": "text",
                            "text": otp
                        }
                    ]
                },
                {
                    "type": "button",
                    "sub_type": "url",
                    "index": 0,
                    "parameters": [
                        {
                            "type": "text",
                            "text": otp
                        }
                    ]
                }
            ]
        }
    }
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    return response.status_code == 200

@user_controller.route("/user", methods=["POST"])
@role_required(["IT"])
def create_user():
    try:
        name = request.json["name"]
        phone = request.json["phone"]
        role = request.json["role"]
        photo = request.json.get(
            "photo", 
            "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQmRLRMXynnc7D6-xfdpeaoEUeon2FaU0XtPg&s"
        )
        branchCode = request.json.get("branchCode", [])

        # Mengatur lastLogin ke zona waktu Jakarta
        jakarta_tz = pytz.timezone('Asia/Jakarta')
        lastLogin = datetime.now(jakarta_tz)
        
        status = "ACTIVE"

        db = current_app.config['db']
        collection = db.user

        # Cek apakah nomor telepon sudah ada
        existing_user = collection.find_one({"phone": phone})
        if existing_user:
            return jsonify({
                "message": "Phone number already exists.",
                "data": {
                    "userId": str(existing_user["_id"]),
                    "name": existing_user["name"],
                    "phone": existing_user["phone"],
                    "role": existing_user["role"],
                    "photo": existing_user["photo"],
                    "branchCode": existing_user["branchCode"],
                    "lastLogin": existing_user["lastLogin"],
                    "createdAt": existing_user["createdAt"].isoformat() + 'Z',
                    "updatedAt": existing_user["updatedAt"].isoformat() + 'Z'
                }
            }), 409  # Mengganti status code menjadi 409 untuk konflik data yang sudah ada

        # Jika nomor telepon belum ada, buat user baru
        user = {
            "name": name,
            "phone": phone,
            "role": role,
            "photo": photo,  # Menggunakan nilai default jika tidak ada input
            "branchCode": branchCode,
            "status": status,
            "lastLogin": lastLogin,
            "createdAt": datetime.utcnow(),
            "updatedAt": datetime.utcnow()
        }
        inserted_id = collection.insert_one(user).inserted_id
        new_user = collection.find_one({"_id": inserted_id})

        return jsonify({
            "message": "User created successfully.",
            "data": {
                "userId": str(new_user["_id"]),
                "name": new_user["name"],
                "phone": new_user["phone"],
                "role": new_user["role"],
                "photo": new_user["photo"],  # Foto yang berhasil disimpan
                "branchCode": new_user["branchCode"],
                "lastLogin": new_user["lastLogin"].isoformat(),
                "createdAt": new_user["createdAt"].isoformat() + 'Z',
                "updatedAt": new_user["updatedAt"].isoformat() + 'Z'
            }
        }), 201
    except Exception as e:
        print(e)
        return jsonify({"errorMessage": str(e)}), 500
    
@user_controller.route("/user", methods=["GET"])
@role_required(["IT"])
def get_users():
    try:
        db = current_app.config['db']
        collection = db.user

        users = []
        for user in collection.find():
            users.append({
                "userId": str(user["_id"]),
                "name": user["name"],
                "phone": user["phone"],
                "role": user["role"],
                "photo": user["photo"],
                "status": user["status"],
                "branchCode": user["branchCode"],
                "lastLogin": user["lastLogin"].isoformat(),
                "createdAt": user["createdAt"].isoformat() + 'Z',
                "updatedAt": user["updatedAt"].isoformat() + 'Z'
            })

        return jsonify({
            "message": "Users retrieved successfully.",
            "data": users
        }), 200
    except Exception as e:
        print(e)
        return jsonify({"errorMessage": str(e)}), 500
    
@user_controller.route("/user/<string:user_id>", methods=["PUT"])
@role_required(["IT"])
def update_user(user_id):
    try:
        data = request.json
        db = current_app.config['db']
        collection = db.user

        update_data = {
            "name": data.get("name"),
            "phone": data.get("phone"),
            "role": data.get("role"),
            "status": data.get("status"),
            "branchCode": data.get("branchCode", []),
            "updatedAt": datetime.utcnow(),
        }

        result = collection.update_one({"_id": ObjectId(user_id)}, {"$set": update_data})

        if result.matched_count == 0:
            return jsonify({"message": "User not found"}), 404

        updated_user = collection.find_one({"_id": ObjectId(user_id)})
        return jsonify({
            "message": "User updated successfully",
            "data": {
                "userId": str(updated_user["_id"]),
                "name": updated_user["name"],
                "phone": updated_user["phone"],
                "role": updated_user["role"],
                "status": updated_user["status"],
                "branchCode": updated_user["branchCode"],
                "updatedAt": updated_user["updatedAt"].isoformat() + 'Z',
            }
        }), 200
    except Exception as e:
        print(e)
        return jsonify({"errorMessage": str(e)}), 500
    
@user_controller.route("/user_status/<string:user_id>", methods=["PATCH"])
@role_required(["IT"])    
def update_user_status(user_id):
    try:
        db = current_app.config['db']
        collection = db.user
        data = request.json

        update_data = {
            "status": data.get("status")
        }

        result = collection.update_one({"_id": ObjectId(user_id)}, {"$set": update_data})

        if result.matched_count == 0:
            return jsonify({"message": "User not found"}), 404

        updated_user = collection.find_one({"_id": ObjectId(user_id)})
        return jsonify({
            "message": "User status updated successfully",
            "data": {
                "userId": str(updated_user["_id"]),
                "name": updated_user["name"],
                "phone": updated_user["phone"],
                "role": updated_user["role"],
                "status": updated_user["status"],
                "branchCode": updated_user["branchCode"],
                "updatedAt": updated_user["updatedAt"].isoformat() + 'Z',
            }
        }), 200
    except Exception as e:
        print(e)
        return jsonify({"errorMessage": str(e)}), 500

@user_controller.route("/user/login", methods=["POST"])
def login_user():
    try:
        phone = request.json.get("phone")
        if not phone:
            return jsonify({"message": "Phone number is required."}), 400

        db = current_app.config['db']
        collection = db.user

        user = collection.find_one({"phone": phone})
        if user:
            otp = generate_otp()
            if send_otp_via_whatsapp(phone, otp):
                jakarta_tz = pytz.timezone('Asia/Jakarta')
                lastLogin = datetime.now(jakarta_tz)
                
                collection.update_one(
                    {"_id": user["_id"]},
                    {
                        "$set": {
                            "otp": otp,
                            "otpCreatedAt": datetime.utcnow(),
                            "lastLogin": lastLogin
                        }
                    }
                )
                
                token = generate_jwt({
                    "userId": str(user["_id"]),
                    "branchCode": user["branchCode"],
                    "role": user["role"],
                    "exp": datetime.utcnow() + timedelta(hours=12)
                })
                
                return jsonify({
                    "message": "OTP sent to user's phone.",
                    "token": token,
                    "user": {
                        "userId": str(user["_id"]),
                        "name": user["name"],
                        "phone": user["phone"],
                        "role": user["role"],
                        "photo": user["photo"],
                        "status": user["status"],
                        "branchCode": user["branchCode"], 
                        "lastLogin": lastLogin.isoformat(),
                        "createdAt": user["createdAt"].isoformat() + 'Z',
                        "updatedAt": user["updatedAt"].isoformat() + 'Z'
                    }
                }), 200
            else:
                return jsonify({"message": "Failed to send OTP."}), 400
        else:
            return jsonify({"message": "Nomor telepon tidak ditemukan."}), 404
    except Exception as e:
        print(e)
        return jsonify({"errorMessage": str(e)}), 500 