from flask import Blueprint, request, jsonify, current_app
from bson import ObjectId
from datetime import datetime

reservation_controller = Blueprint("reservation_controller", __name__)

def format_date(date_str):
    return datetime.strptime(date_str, '%d %b %Y').strftime('%Y-%m-%d')

def format_time(time_str):
    return datetime.strptime(time_str, '%H:%M').strftime('%H:%M')

@reservation_controller.route("/reservation", methods=["POST"])
def create_reservation():
    try:
        customer = request.json["customer"]
        branchCode = request.json["branchCode"]
        branchName = request.json["branchName"]
        reservationCode = request.json.get("reservationCode", None)
        date = format_date(request.json["date"]) 
        time = format_time(request.json["time"])
        guest = request.json["guest"]
        status = request.json.get("status", "PENDING")
        amount = request.json.get("amount", None)
        tax = request.json.get("tax", None)
        cookingCharge = request.json.get("cookingCharge", None)
        totalAmount = request.json.get("totalAmount", None)
        mdr = 0.015
        isDisbursed = request.json.get("isDisbursed", False)
        note = request.json.get("note", None)
        items = request.json.get("items", None)
        tableAreaName = request.json.get("tableAreaName", None)
        tableName = request.json.get("tableName", None)
        arrivalStatus = request.json.get("arrivalStatus", None)
        
        db = current_app.config['db']
        collection = db.reservation
       
        new_reservation = {
        "customer": customer,
        "branchCode": branchCode,
        "branchName": branchName,
        "reservationCode": reservationCode,
        "date": date,
        "time": time,
        "guest": guest,
        "status": status,
        "amount": amount,
        "tax": tax,
        "cookingCharge": cookingCharge,
        "totalAmount": totalAmount,
        "mdr": mdr,
        "isDisbursed": isDisbursed,
        "note": note,
        "items": items,
        "tableAreaName": tableAreaName,
        "tableName": tableName,
        "arrivalStatus": arrivalStatus,
        "createdAt": datetime.utcnow(),
        "updatedAt": datetime.utcnow()
        }

        inserted_id = collection.insert_one(new_reservation).inserted_id
        new_reservation = collection.find_one({"_id": inserted_id})
        
        return jsonify({
            "message": "Reservation created successfully",
            "data": {
                "reservationId": str(new_reservation["_id"]),
                "customer": new_reservation["customer"],
                "branchCode": new_reservation["branchCode"],
                "branchName": new_reservation["branchName"],
                "reservationCode": new_reservation["reservationCode"],
                "date": new_reservation["date"],
                "time": new_reservation["time"],
                "guest": new_reservation["guest"],
                "status": new_reservation["status"],
                "amount": new_reservation["amount"],
                "tax": new_reservation["tax"],
                "cookingCharge": new_reservation["cookingCharge"],
                "totalAmount": new_reservation["totalAmount"],
                "mdr": new_reservation["mdr"],
                "isDisbursed": new_reservation["isDisbursed"],
                "note": new_reservation["note"],
                "items": new_reservation["items"],
                "tableAreaName": new_reservation["tableAreaName"],
                "tableName": new_reservation["tableName"],
                "arrivalStatus": new_reservation["arrivalStatus"],
                "createdAt": new_reservation["createdAt"].isoformat() + 'Z',
                "updatedAt": new_reservation["updatedAt"].isoformat() + 'Z'
            }
        }), 201

    except Exception as e:
        print(e)
        return jsonify({"errorMessage": str(e)}), 500
    
@reservation_controller.route("/reservation_branch/<string:branchCode>", methods=["GET"])
def get_reservations_by_branchCode(branchCode):
    try:
        db = current_app.config['db']
        collection = db.reservation

        # Ambil query parameter
        branch_name = request.args.get("branchName")
        date = request.args.get("date")
        status = request.args.get("status")

        # Buat query dasar
        query = {"branchCode": branchCode}

        # Tambahkan filter jika parameter ada
        if branch_name:
            query["branchName"] = branch_name
        if date:
            query["date"] = date
        if status:
            query["status"] = status

        reservations = collection.find(query)

        reservation_list = []
        for reservation in reservations:
            reservation_list.append({
                "reservationId": str(reservation["_id"]),
                "customer": reservation.get("customer", {
                    "name": "N/A",
                    "phone": "N/A",
                    "email": "N/A"
                }),
                "branchCode": reservation["branchCode"],
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
    
@reservation_controller.route("/reservation/<string:reservationId>", methods=["GET"])
def get_reservation_by_id(reservationId):
    try:
        db = current_app.config['db']
        collection_reservation = db.reservation

        reservation = collection_reservation.find_one({"_id": ObjectId(reservationId)})
        
        if not reservation:
            return jsonify({"message": "Reservation not found"}), 404
        
        reservation_details = {
            "reservationId": str(reservation["_id"]),
            "customer": reservation.get("customer", []),
            "branchCode": reservation.get("branchCode"),
            "branchName": reservation.get("branchName"),
            "reservationCode": reservation.get("reservationCode", ""),
            "date": reservation.get("date"),
            "time": reservation.get("time"),
            "guest": reservation.get("guest"),
            "amount": reservation.get("amount", 0),
            "tax": reservation.get("tax", 0),
            "cookingCharge": reservation.get("cookingCharge", 0),
            "totalAmount": reservation.get("totalAmount", 0),
            "mdr": reservation.get("mdr", 0),
            "isDisbursed": reservation.get("isDisbursed", False),
            "note": reservation.get("note"),
            "items": reservation.get("items", []),
            "tableAreaName": reservation.get("tableAreaName", None),
            "tableName": reservation.get("tableName", None),
            "createdAt": reservation["createdAt"].isoformat() + 'Z' if reservation.get("createdAt") else None,
            "updatedAt": reservation["updatedAt"].isoformat() + 'Z' if reservation.get("updatedAt") else None
        }
        
        return jsonify({
            "message": "Success get reservation",
            "data": reservation_details
        }), 200

    except Exception as e:
        print(f"Error retrieving reservation: {e}")
        return jsonify({"errorMessage": str(e)}), 500

@reservation_controller.route("/reservation/<string:reservationId>", methods=["PUT"])
def update_reservation(reservationId):
    try:
        db = current_app.config['db']
        collection = db.reservation
        
        updated_data = {
            "customer": request.json.get("customer"),
            "branchCode": request.json.get("branchCode"),
            "branchName": request.json.get("branchName"),
            "reservationCode": request.json.get("reservationCode", None),
            "guest": request.json.get("guest"),
            "status": request.json.get("status", "PENDING"),
            "amount": request.json.get("amount", None),
            "tax": request.json.get("tax", None),
            "cookingCharge": request.json.get("cookingCharge", None),
            "totalAmount": request.json.get("totalAmount", None),
            "mdr": request.json.get("mdr", None),
            "isDisbursed": request.json.get("isDisbursed", False),
            "note": request.json.get("note", None),
            "items": request.json.get("items", None),
            "tableAreaName": request.json.get("tableAreaName", None),
            "tableName": request.json.get("tableName", None),
            "arrivalStatus": request.json.get("arrivalStatus", None),
            "updatedAt": datetime.utcnow()
        }

        date = request.json.get("date")
        if date:
            try:
                updated_data["date"] = format_date(date)
            except ValueError:
                return jsonify({"errorMessage": "Invalid date format"}), 400

        time = request.json.get("time")
        if time:
            try:
                updated_data["time"] = format_time(time)
            except ValueError:
                return jsonify({"errorMessage": "Invalid time format"}), 400

        updated_data = {k: v for k, v in updated_data.items() if v is not None}
 
        result = collection.update_one({"_id": ObjectId(reservationId)}, {"$set": updated_data})
        
        if result.matched_count == 0:
            return jsonify({"message": "Reservation not found"}), 404
        
        updated_reservation = collection.find_one({"_id": ObjectId(reservationId)})
        
        return jsonify({
            "message": "Reservation updated successfully",
            "data": {
                "reservationId": str(updated_reservation["_id"]),
                "customer": updated_reservation["customer"],
                "branchCode": updated_reservation["branchCode"],
                "branchName": updated_reservation["branchName"],
                "reservationCode": updated_reservation["reservationCode"],
                "date": updated_reservation["date"],
                "time": updated_reservation["time"],
                "guest": updated_reservation["guest"],
                "status": updated_reservation["status"],
                "amount": updated_reservation["amount"],
                "tax": updated_reservation["tax"],
                "cookingCharge": updated_reservation["cookingCharge"],
                "totalAmount": updated_reservation["totalAmount"],
                "mdr": updated_reservation["mdr"],
                "isDisbursed": updated_reservation["isDisbursed"],
                "note": updated_reservation["note"],
                "items": updated_reservation["items"],
                "tableAreaName": updated_reservation["tableAreaName"],
                "tableName": updated_reservation["tableName"],
                "arrivalStatus": updated_reservation["arrivalStatus"],
                "createdAt": updated_reservation["createdAt"].isoformat() + 'Z',
                "updatedAt": updated_reservation["updatedAt"].isoformat() + 'Z'
            }
        }), 200

    except Exception as e:
        print(f"Error updating reservation: {e}")
        return jsonify({"errorMessage": str(e)}), 500


@reservation_controller.route("/reservation/<string:reservationId>", methods=["DELETE"])
def delete_reservation(reservationId):
    try:
        db = current_app.config['db']
        collection = db.reservation
        
        result = collection.delete_one({"_id": ObjectId(reservationId)})
        
        if result.deleted_count == 0:
            return jsonify({"message": "Reservation not found"}), 404
        
        return jsonify({"message": "Reservation deleted successfully"}), 200

    except Exception as e:
        print(e)
        return jsonify({"errorMessage": str(e)}), 500