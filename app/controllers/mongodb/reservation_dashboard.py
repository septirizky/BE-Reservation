from flask import Blueprint, request, jsonify, current_app
from datetime import datetime
from app.middleware import role_required

reservation_dashboard_controller = Blueprint("reservation_dashboard_controller", __name__)
    
@reservation_dashboard_controller.route("/reservation_summary", methods=["POST"])
@role_required(["IT", "Business Development", "Manager Accounting", "Assistant Manager Accounting", "Head Accounting", "GRO"])
def create_reservation_summary():
    try:
        db = current_app.config['db']
        collection = db.reservation_summary 

        data = request.json

        if not all(key in data for key in ["date", "branchCode", "totalReservations", "totalAmountBeforeMdr", "totalAmountAfterMdr", "reservationCodes"]):
            return jsonify({"error": "Missing required fields"}), 400

        # Cek apakah kombinasi date, branchCode, dan reservationCodes sudah ada
        existing_summary = collection.find_one({
            "date": data["date"],
            "branchCode": data["branchCode"],
            "reservationCodes": {"$all": data["reservationCodes"]}  # Cek apakah semua reservationCodes sudah ada
        })

        if existing_summary:
            print(f"Duplicate summary found for date {data['date']} and branch {data['branchCode']}")
            return jsonify({"message": "Reservation summary already exists"}), 200

        # Siapkan data summary
        summary_data = {
            "external_id": data.get("external_id"),
            "userId": data.get("userId"),
            "date": data.get("date"),
            "branchCode": data.get("branchCode"),
            "branchName": data.get("branchName"),
            "totalReservations": data.get("totalReservations"),
            "totalAmountBeforeMdr": data.get("totalAmountBeforeMdr"),
            "totalAmountAfterMdr": data.get("totalAmountAfterMdr"),
            "status": data.get("status", "PENDING"),
            "reservationCodes": data.get("reservationCodes"), 
            "createdAt": datetime.utcnow(),
            "updatedAt": datetime.utcnow()  
        }

        collection.insert_one(summary_data)

        return jsonify({"message": "Reservation summary created successfully"}), 201

    except Exception as e:
        return jsonify({"error": f"Error creating reservation summary: {str(e)}"}), 500

@reservation_dashboard_controller.route("/update_reservation_posted", methods=["POST"])
@role_required(["IT", "Business Development", "Manager Accounting", "Assistant Manager Accounting", "Head Accounting", "GRO"])
def update_reservation_posted():
    try:
        db = current_app.config['db']
        collection = db.reservation
        
        data = request.json
        reservation_codes = data.get("reservationCodes", [])

        if not reservation_codes:
            return jsonify({"error": "Missing reservation codes"}), 400

        # Update `isPosted` menjadi true untuk semua reservationCode yang dikirim
        collection.update_many(
            {"reservationCode": {"$in": reservation_codes}},
            {"$set": {"isPosted": "false"}}
        )

        return jsonify({"message": "Reservations updated successfully"}), 200

    except Exception as e:
        return jsonify({"error": f"Error updating reservations: {str(e)}"}), 500
    
@reservation_dashboard_controller.route("/reservation_summary/<string:branchCode>", methods=["GET"])
@role_required(["IT", "Business Development", "Manager Accounting", "Assistant Manager Accounting", "Head Accounting", "GRO"])
def get_reservation_summary(branchCode):
    try:
        db = current_app.config['db']
        collection = db.reservation_summary

        summaries = collection.find({"branchCode": branchCode})

        summary_list = []
        for summary in summaries:
            summary_list.append({
                "external_id": summary.get("external_id"),
                "userId": summary.get("userId"),
                "date": summary.get("date"),
                "branchCode": summary.get("branchCode"),
                "branchName": summary.get("branchName"),
                "totalReservations": summary.get("totalReservations"),
                "totalAmountBeforeMdr": summary.get("totalAmountBeforeMdr"),
                "totalAmountAfterMdr": summary.get("totalAmountAfterMdr"),
                "status": summary.get("status"),
                "createdAt": summary.get("createdAt").isoformat() + 'Z' if summary.get("createdAt") else None,
                "updatedAt": summary.get("updatedAt").isoformat() + 'Z' if summary.get("updatedAt") else None
            })

        if summary_list:
            return jsonify({
                "message": "Success get reservation summary",
                "data": summary_list
            }), 200
        else:
            return jsonify({"message": "No reservation summary found for this branch"}), 404

    except Exception as e:
        print(f"Error fetching reservation summary for branchCode {branchCode}: {e}")
        return jsonify({"errorMessage": str(e)}), 500
    
@reservation_dashboard_controller.route("/reservation_dashboard/<string:branchCode>", methods=["GET"])
@role_required(["IT", "Business Development", "Manager Accounting", "Assistant Manager Accounting", "Head Accounting", "GRO"])
def get_reservations_dashboard(branchCode):
    try:
        db = current_app.config['db']
        collection = db.reservation

        reservations = collection.find({"branchCode":branchCode})

        reservation_list = []
        for reservation in reservations:
            reservation_list.append({
                "reservationId": str(reservation["_id"]),
                "customer": reservation.get("customer"),
                "branchCode": reservation.get("branchCode"),
                "branchName": reservation.get("branchName"),
                "reservationCode": reservation.get("reservationCode", ""),
                "date": reservation.get("date"),
                "time": reservation.get("time"),
                "guest": reservation.get("guest"),
                "status": reservation.get("status"),
                "amount": reservation.get("amount", 0),
                "tax": reservation.get("tax", 0),
                "cookingCharge": reservation.get("cookingCharge", 0),
                "totalAmount": reservation.get("totalAmount", 0),
                "mdr": reservation.get("mdr", 0),
                "isDisbursed": reservation.get("isDisbursed", False),
                "note": reservation.get("note"),
                "items": reservation.get("items", []),
                "isPosted": reservation.get("isPosted", None),
                "tableAreaName": reservation.get("tableAreaName", None),
                "tableName": reservation.get("tableName", None),
                "arrivalStatus": reservation.get("arrivalStatus", None),
                "createdAt": reservation["createdAt"].isoformat() + 'Z',
                "updatedAt": reservation["updatedAt"].isoformat() + 'Z'
            })

        if reservation_list:
            return jsonify({
                "message": "Success get reservations",
                "data": reservation_list
            }), 200
        else:
            return jsonify({"message": "No reservations found for this branch"}), 404

    except Exception as e:
        print(e)
        return jsonify({"errorMessage": str(e)}), 500