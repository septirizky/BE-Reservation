from flask import Blueprint, request, jsonify, current_app
import os
import random
import requests
import json
from bson import ObjectId
from datetime import datetime, timedelta
from app.middleware import role_required
from app.celery_app import celery

customer_controller = Blueprint("customer_controller", __name__)

WA_URI = os.getenv('WA_URI')
WA_TOKEN = os.getenv('WA_TOKEN')

def generate_otp():
    return str(random.randint(100000, 999999))  

@celery.task
def send_otp_via_whatsapp_task(phone, otp):
    try:
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
        if response.status_code == 200:
            print(f"OTP berhasil dikirim ke {phone}")
        else:
            print(f"Gagal mengirim OTP ke {phone}. Response: {response.json()}")
    except Exception as e:
        print(f"Error in send_otp_via_whatsapp_task: {e}")

@customer_controller.route("/customer", methods=["POST"])
def create_customer():
    try:
        name = request.json["name"]
        email = request.json["email"]
        phone = request.json["phone"]
        otpVerified = request.json.get("otpVerified", False)
        status = "ACTIVE"
        
        db = current_app.config['db']
        collection = db.customer

        # Periksa apakah nomor telepon sudah ada di database
        existing_customer = collection.find_one({"phone": phone})

        if existing_customer:
            otp_verified = existing_customer.get("otpVerified", False)

            if not otp_verified:
                # Buat OTP baru
                otp = generate_otp()
                customer_id = str(existing_customer["_id"])
                
                # Kirim ulang OTP ke WhatsApp
                send_otp_via_whatsapp_task.apply_async(args=[phone, otp])

                # Perbarui OTP di database
                collection.update_one(
                    {"_id": ObjectId(customer_id)},
                    {
                        "$set": {
                            "otp": otp,
                            "otpCreatedAt": datetime.utcnow(),
                        }
                    }
                )

                return jsonify({
                    "message": "OTP not verified for this phone number. New OTP sent.",
                    "data": {
                        "customerId": customer_id,
                        "otpVerified": False
                    }
                }), 200

            return jsonify({
                "message": "Phone number already exists and OTP verified.",
                "data": {
                    "customerId": str(existing_customer["_id"]),
                    "name": existing_customer["name"],
                    "email": existing_customer["email"],
                    "phone": existing_customer["phone"],
                    "otpVerified": existing_customer.get("otpVerified", False),
                    "createdAt": existing_customer["createdAt"].isoformat() + 'Z',
                    "updatedAt": existing_customer["updatedAt"].isoformat() + 'Z'
                }
            }), 200

        # Jika telepon belum ada, buat customer baru
        otp = generate_otp()
        
        # Kirim OTP menggunakan Celery Task
        send_otp_via_whatsapp_task.apply_async(args=[phone, otp])

        # Simpan data customer ke MongoDB
        customer = {
            "name": name,
            "email": email,
            "phone": phone,
            "status": status,
            "otp": otp,
            "otpVerified": False,
            "otpCreatedAt": datetime.utcnow(),
            "createdAt": datetime.utcnow(),
            "updatedAt": datetime.utcnow()
        }
        inserted_id = collection.insert_one(customer).inserted_id
        new_customer = collection.find_one({"_id": inserted_id})

        return jsonify({
            "message": "Success added customer. OTP sent asynchronously.",
            "data": {
                "customerId": str(new_customer["_id"]),
                "name": new_customer["name"],
                "email": new_customer["email"],
                "phone": new_customer["phone"],
                "otp": new_customer["otp"],
                "otpVerified": new_customer["otpVerified"],
                "otpCreatedAt": new_customer["otpCreatedAt"].isoformat() + 'Z',
                "createdAt": new_customer["createdAt"].isoformat() + 'Z',
                "updatedAt": new_customer["updatedAt"].isoformat() + 'Z'
            }
        }), 201
    
    except Exception as e:
        print(e)
        return jsonify({"errorMessage": str(e)}), 500

@customer_controller.route("/customer_gro", methods=["POST"])
def create_customer_gro():
    try:
        name = request.json["name"]
        email = request.json["email"]
        phone = request.json["phone"]
        status = "ACTIVE"
        
        db = current_app.config['db']
        collection = db.customer

        existing_customer = collection.find_one({"phone": phone})

        if existing_customer:
            return jsonify({
                "message": "Phone number already exists.",
                "data": {
                    "customerId": str(existing_customer["_id"]),
                    "name": existing_customer["name"],
                    "email": existing_customer["email"],
                    "phone": existing_customer["phone"],
                    "createdAt": existing_customer["createdAt"].isoformat() + 'Z',
                    "updatedAt": existing_customer["updatedAt"].isoformat() + 'Z'
                }
            }), 200

        customer = {
            "name": name,
            "email": email,
            "phone": phone,
            "status": status,
            "createdAt": datetime.utcnow(),
            "updatedAt": datetime.utcnow()
        }
        inserted_id = collection.insert_one(customer).inserted_id
        new_customer = collection.find_one({"_id": inserted_id})

        return jsonify({
            "message": "Success create new customer",
            "data": {
                "customerId": str(new_customer["_id"]),
                "name": new_customer["name"],
                "email": new_customer["email"],
                "phone": new_customer["phone"],
                "createdAt": new_customer["createdAt"].isoformat() + 'Z',
                "updatedAt": new_customer["updatedAt"].isoformat() + 'Z'
            }
        }), 201
    
    except Exception as e:
        print(e)
        return jsonify({"errorMessage": str(e)}), 500
    
@customer_controller.route("/resend-otp", methods=["POST"])
def resend_otp():
    try:
        customerId = request.json.get("customerId")
        if not customerId:
            return jsonify({"message": "customer ID not provided."}), 400

        db = current_app.config['db']
        collection = db.customer

        customer = collection.find_one({"_id": ObjectId(customerId)})
        if not customer:
            return jsonify({"message": "customer not found."}), 404

        otp = generate_otp()  # Buat OTP baru
        customer_phone = customer["phone"]

        # Kirim OTP via WhatsApp
        send_otp_via_whatsapp_task.apply_async(args=[customer_phone, otp])

        # Perbarui atau buat OTP baru di database
        collection.update_one(
            {"_id": ObjectId(customerId)},
            {
                "$set": {
                    "otp": otp,
                    "otpCreatedAt": datetime.utcnow(),
                }
            },
        )

        return jsonify({"message": "OTP baru berhasil dikirim ulang."}), 200

    except Exception as e:
        print(f"Error in resend_otp: {e}")
        return jsonify({"errorMessage": str(e)}), 500
    
@customer_controller.route("/verify-otp", methods=["POST"])
def verify_otp():
    try:
        customerId = request.json.get("customerId")
        if not customerId:
            return jsonify({"message": "customer ID not provided."}), 400

        input_otp = request.json.get("otp")
        if not input_otp:
            return jsonify({"message": "OTP not provided."}), 400

        db = current_app.config['db']
        collection = db.customer

        customer = collection.find_one({"_id": ObjectId(customerId)})
        if not customer:
            return jsonify({"message": "customer not found."}), 404

        otp_created_at = customer.get("otpCreatedAt")
        if otp_created_at:
            otp_created_at = otp_created_at.replace(tzinfo=None)
            current_time = datetime.utcnow()
            time_difference = current_time - otp_created_at

            if time_difference > timedelta(minutes=10):
                return jsonify({"message": "OTP has expired."}), 400

        if customer["otp"] == input_otp:
            # Update otpVerified menjadi true
            collection.update_one(
                {"_id": ObjectId(customerId)},
                {"$set": {"otpVerified": True, "updatedAt": datetime.utcnow()}}
            )
            return jsonify({"message": "OTP verified successfully."}), 200
        else:
            return jsonify({"message": "OTP Salah"}), 400

    except Exception as e:
        print(f"Error in verify_otp: {e}")
        return jsonify({"errorMessage": str(e)}), 500

@customer_controller.route("/customer/<string:customerId>", methods=["GET"])
def get_customer_by_id(customerId):
    try:
        db = current_app.config['db']
        collection = db.customer

        customer = collection.find_one({"_id": ObjectId(customerId)})

        if customer:
            return jsonify({
                "message": "Success get customer",
                "data": {
                    "customerId": str(customer["_id"]),
                    "name": customer["name"],
                    "email": customer["email"],
                    "phone": customer["phone"],
                    "createdAt": customer["createdAt"].isoformat() + 'Z',
                    "updatedAt": customer["updatedAt"].isoformat() + 'Z'
                }
            }), 200
        else:
            return jsonify({"message": "customer not found"}), 404
    except Exception as e:
        print(e)
        return jsonify({"errorMessage": str(e)}), 500

@customer_controller.route("/customer", methods=["GET"])
@role_required(["IT", "Business Development", "Manager Accounting", "Assistant Manager Accounting", "Head Accounting", "GRO"])
def get_customer():
    try:
        db = current_app.config['db']
        collection = db.customer

        customers = collection.find()

        customers_list = []

        for customer in customers:
            customers_list.append({
                "customerId": str(customer["_id"]),
                "name": customer["name"],
                "email": customer["email"],
                "phone": customer["phone"],
                "status": customer["status"],
                "createdAt": customer["createdAt"].isoformat() + 'Z',
                "updatedAt": customer["updatedAt"].isoformat() + 'Z'
            })

        return jsonify({
            "message": "Success get customer",
            "data": customers_list
        }), 200
    except Exception as e:
        print(e)
        return jsonify({"errorMessage": str(e)}), 500
    
@customer_controller.route("/customer/<string:customerId>", methods=["PUT"])
def update_customer(customerId):
    try:
        name = request.json["name"]
        email = request.json["email"]
        phone = request.json["phone"]
        
        db = current_app.config['db']
        collection = db.customer

        customer = collection.find_one({"_id": ObjectId(customerId)})

        if customer:
            collection.update_one({"_id": ObjectId(customerId)}, 
                {
                    "$set": {
                        "name": name, 
                        "email": email, 
                        "phone": phone, 
                    }
                }
            )
            
            return jsonify({
                "message": "customer updated",
                "data": {
                    "customerId": str(customer["_id"]), 
                    "name": name, 
                    "email": email, 
                    "phone": phone, 
                }
            }), 200
        else:
            return jsonify({"message": "customer not found"}), 404
    except Exception as e:
        print(e)
        return jsonify({"errorMessage": str(e)}), 500