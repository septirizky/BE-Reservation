from flask import Blueprint, request, jsonify, current_app
from datetime import datetime
from app.middleware import role_required

refund_controller = Blueprint("refund_controller", __name__)

@refund_controller.route("/refund", methods=["POST"])
@role_required(["IT", "Business Development", "Manager Accounting", "Assistant Manager Accounting", "Head Accounting", "Accounting"])
def create_refund():
    try:
        db = current_app.config['db']
        refund_collection = db.refund  
        invoice_collection = db.invoice

        data = request.json
        external_id = data.get("external_id")
        bank_name = data.get("bank_name")
        account_number = data.get("account_number")
        account_holder = data.get("account_holder")
        phone = data.get("phone")

        # Periksa apakah semua field wajib diisi
        if not all([external_id, bank_name, account_number, account_holder, phone]):
            return jsonify({"message": "All fields are required"}), 400

        # Periksa apakah external_id valid
        invoice = invoice_collection.find_one({"external_id": external_id})
        if not invoice:
            return jsonify({"message": "Invoice not found"}), 404

        # Ambil reservationCode dan branchCode dari invoice
        reservationCode = invoice.get("reservationCode")
        branchCode = invoice.get("branchCode")
        if not reservationCode or not branchCode:
            return jsonify({"message": "ReservationCode or BranchCode not found in invoice"}), 404

        # Cek apakah sudah ada refund untuk invoice ini
        existing_refund = refund_collection.find_one({"external_id": external_id})
        if existing_refund:
            return jsonify({"message": "Refund already exists for this invoice"}), 400

        # Data refund baru
        refund_data = {
            "external_id": external_id,
            "reservationCode": reservationCode,
            "branchCode": branchCode, 
            "bank_name": bank_name,
            "account_number": account_number,
            "account_holder": account_holder,
            "phone": phone,
            "refund_status": "Request Refund",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }

        # Simpan data ke collection refund
        result = refund_collection.insert_one(refund_data)

        return jsonify({
            "message": "Refund request created successfully",
            "refund_id": str(result.inserted_id)
        }), 201

    except Exception as e:
        print(f"Error creating refund: {e}")
        return jsonify({"errorMessage": str(e)}), 500



@refund_controller.route("/refunds/<string:branchCode>", methods=["GET"])
@role_required(["IT", "Business Development", "Manager Accounting", "Assistant Manager Accounting", "Head Accounting"])
def get_refunds_by_branchCode(branchCode):
    try:
        db = current_app.config['db']
        refund_collection = db.refund

        # Filter refunds berdasarkan branchCode
        refunds_cursor = refund_collection.find({"branchCode": branchCode})

        # Konversi cursor ke list
        refunds_list = list(refunds_cursor)

        # Cek jika tidak ada data refund
        if not refunds_list:
            return jsonify({"message": "No refunds found for this branch"}), 404

        # Format data refund
        formatted_refunds = []
        for refund in refunds_list:
            formatted_refunds.append({
                "external_id": refund.get("external_id"),
                "reservationCode": refund.get("reservationCode"),
                "branchCode": refund.get("branchCode"),
                "bank_name": refund.get("bank_name"),
                "account_number": refund.get("account_number"),
                "account_holder": refund.get("account_holder"),
                "phone": refund.get("phone"),
                "refund_status": refund.get("refund_status"),
                "created_at": refund.get("created_at"),
            })

        return jsonify({"message": "Success", "data": formatted_refunds}), 200

    except Exception as e:
        print(f"Error fetching refunds: {e}")
        return jsonify({"errorMessage": str(e)}), 500
    
@refund_controller.route("/refund/<string:external_id>", methods=["PATCH"])
@role_required(["IT", "Business Development", "Manager Accounting", "Assistant Manager Accounting", "Head Accounting"])
def update_refund_status(external_id):
    try:
        db = current_app.config['db']
        refund_collection = db.refund
        invoice_collection = db.invoice

        data = request.json
        refund_status = data.get("refund_status")

        if not refund_status:
            return jsonify({"message": "Refund status is required"}), 400

        # Perbarui status refund di collection refund
        refund_result = refund_collection.update_one(
            {"external_id": external_id},
            {"$set": {"refund_status": refund_status, "updated_at": datetime.utcnow()}}
        )

        if refund_result.matched_count == 0:
            return jsonify({"message": "Refund not found"}), 404

        # Perbarui status refund di collection invoice (jika perlu)
        invoice_result = invoice_collection.update_one(
            {"external_id": external_id},
            {"$set": {"refund_status": refund_status}}
        )

        if invoice_result.matched_count == 0:
            return jsonify({"message": "Invoice not found"}), 404

        return jsonify({"message": "Refund status updated successfully"}), 200

    except Exception as e:
        print(f"Error updating refund status: {e}")
        return jsonify({"errorMessage": str(e)}), 500