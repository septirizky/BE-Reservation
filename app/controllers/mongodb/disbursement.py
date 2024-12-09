from flask import Blueprint, request, jsonify, current_app
import requests
import os
from datetime import datetime
from app.middleware import role_required
from bson import ObjectId

def serialize_disbursement(disbursement):
    disbursement["_id"] = str(disbursement["_id"])  # Konversi ObjectId ke string
    return disbursement

disbursement_controller = Blueprint("disbursement_controller", __name__)

XENDIT_API_KEY = os.getenv('XENDIT_API_KEY')

@disbursement_controller.route("/create_disbursement", methods=["POST"])
@role_required(["IT", "Business Development", "Manager Accounting", "Assistant Manager Accounting", "Head Accounting", "Accounting"])
def create_disbursement():
    try:
        db = current_app.config['db']
        collection = db.disbursements
        data = request.json
        
        print("Received data:", data)

        external_id = data.get("external_id")
        userId = data.get("userId")
        amount = data.get("amount")
        bank_code = data.get("bank_code")
        account_holder_name = data.get("account_holder_name")
        account_number = data.get("account_number")
        description = data.get("description")

        if not all([amount, bank_code, account_holder_name, account_number]):
            return jsonify({"error": "Missing required fields"}), 400

        url = "https://api.xendit.co/disbursements"
        payload = {
            "external_id": external_id,
            "amount": amount,
            "bank_code": bank_code,
            "account_holder_name": account_holder_name,
            "account_number": account_number,
            "description": description,
        }
        headers = {
            "Authorization": f"Basic {XENDIT_API_KEY}",
            "Content-Type": "application/json",
        }
        response = requests.post(url, headers=headers, json=payload)
        response_data = response.json()

        if response.status_code == 200:
            # Simpan data disbursement ke MongoDB
            disbursement_data = {
                "external_id": external_id,
                "userId": userId,
                "amount": amount,
                "bank_code": bank_code,
                "account_holder_name": account_holder_name,
                "account_number": account_number,
                "description": description,
                "status": response_data.get("status"),  # Status awal dari Xendit
                "createdAt": datetime.utcnow(),
                "updatedAt": datetime.utcnow()
            }
            inserted_id = collection.insert_one(disbursement_data).inserted_id

            # Ambil data terbaru dari database untuk dikembalikan
            saved_disbursement = collection.find_one({"_id": inserted_id})
            serialized_disbursement = serialize_disbursement(saved_disbursement)

            return jsonify({
                "message": "Disbursement created successfully and saved to DB",
                "data": serialized_disbursement
            }), 200
        else:
            return jsonify({"error": "Failed to create disbursement", "details": response_data}), response.status_code
    except Exception as e:
        return jsonify({"error": f"Error in create_disbursement: {e}"}), 500
    
@disbursement_controller.route("/webhook_disbursement", methods=["POST"])
def webhook_disbursement():
    try:
        db = current_app.config['db']
        collection_disbursement = db.disbursements
        collection_summary = db.reservation_summary

        # Ambil data dari webhook
        data = request.json
        
        disbursement_id = data.get("id")
        external_id = data.get("external_id")
        bank_code = data.get("bank_code")
        account_holder_name = data.get("account_holder_name")
        amount = data.get("amount")
        description = data.get("disbursement_description")
        status = data.get("status")
        is_instant = data.get("is_instant")

        # Validasi data webhook
        if not external_id or not status:
            return jsonify({"error": "Invalid webhook data"}), 400
        
        disbursement_data = {
            "disbursement_id": disbursement_id,
            "external_id": external_id,
            "bank_code": bank_code,
            "account_holder_name": account_holder_name,
            "amount": amount,
            "description": description,
            "status": status,
            "is_instant": is_instant
        }

        # Perbarui status disbursement di MongoDB
        result = collection_disbursement.update_one(
            {"external_id": external_id},
            {"$set": disbursement_data}
        )

        if result.modified_count > 0:
            collection_summary.update_one(
                {"external_id": external_id},
                {"$set": {"status": status}}
            )
            
            return jsonify({"message": "Disbursement status updated"}), 200
        else:
            print(f"Disbursement {external_id} not found or already updated")
            return jsonify({"message": "No changes made"}), 200

    except Exception as e:
        return jsonify({"error": f"Error in webhook: {e}"}), 500

@disbursement_controller.route("/get_disbursements", methods=["GET"])
@role_required(["IT", "Business Development", "Manager Accounting", "Assistant Manager Accounting", "Head Accounting", "Accounting"])
def get_disbursements():
    try:
        db = current_app.config['db']
        collection = db.disbursements

        # Ambil semua data disbursement dari MongoDB
        disbursements = collection.find()
        disbursement_list = []
        for disbursement in disbursements:
            disbursement_list.append({
                "external_id": disbursement.get("external_id"),
                "amount": disbursement.get("amount"),
                "bank_code": disbursement.get("bank_code"),
                "account_holder_name": disbursement.get("account_holder_name"),
                "account_number": disbursement.get("account_number"),
                "description": disbursement.get("description"),
                "status": disbursement.get("status"),
                "createdAt": disbursement.get("createdAt"),
                "updatedAt": disbursement.get("updatedAt"),
            })

        return jsonify({"message": "Disbursements fetched successfully", "data": disbursement_list}), 200
    except Exception as e:
        return jsonify({"error": f"Error fetching disbursements: {e}"}), 500
