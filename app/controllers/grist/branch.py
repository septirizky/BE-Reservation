from flask import Blueprint, jsonify, current_app
import requests

branch_controller = Blueprint("branch_controller", __name__)

@branch_controller.route("/branch_category", methods=["GET"])
def get_branch_category():
    try:
        api = current_app.api
        response = api.fetch_table('BranchCategory')
        keys = [
            "ID", "RowID", "BranchCategoryCode", "BranchCategoryName", "BranchCategoryID"
        ]
        data = [dict(zip(keys, item)) for item in response]
        return jsonify({
            "message": "Success get branch category",
            "data": data
        }), 200
    except requests.exceptions.RequestException as e:
        return jsonify({'errorMessage': str(e)}), 500
    
@branch_controller.route("/branch_category/<string:BranchCategoryName>", methods=["GET"])
def get_branch_category_by_id(BranchCategoryName):
    try:
        api = current_app.api
        response = api.fetch_table('Branch')
        keys = [
            "ID", "RowID", "BranchName", "BranchPhone", "BranchID", 
            "BranchNotes", "CreatedAt", "UpdatedAt", "Status", "IDCategory", 
            "BranchCode","BranchWeekDayOpen", "BranchWeekEndOpen", "BranchWeekDayClosed",
            "BranchImage", "BranchMinimumPurchase", "BranchWeekEndClosed", 
            "BranchAddress", "BranchCategoryName", "BranchCategoryID"
        ]
        data = [dict(zip(keys, item)) for item in response]
        filtered_items = [item for item in data if item['BranchCategoryName'] == BranchCategoryName]

        if filtered_items:
            return jsonify({
            "message": "Success get Branch Category by ID",
            "data": filtered_items
        }), 200
        else:
            return jsonify({'errorMessage': 'items not found'}), 404
    except requests.exceptions.RequestException as e:
        return jsonify({'errorMessage': str(e)}), 500

@branch_controller.route("/branch", methods=["GET"])
def get_branch():
    try:
        api = current_app.api
        response = api.fetch_table('Branch')
        keys = [
            "ID", "RowID", "BranchName", "BranchPhone", "BranchID", 
            "BranchNotes", "CreatedAt", "UpdatedAt", "Status", "IDCategory", 
            "BranchCode","BranchWeekDayOpen", "BranchWeekEndOpen", "BranchWeekDayClosed",
            "BranchImage", "BranchMinimumPurchase", "BranchWeekEndClosed", 
            "BranchAddress", "BranchCategoryName", "BranchCategoryID"
        ]
        data = [dict(zip(keys, item)) for item in response]
        return jsonify({
            "message": "Success get branch",
            "data": response
        }), 200
    except requests.exceptions.RequestException as e:
        return jsonify({'errorMessage': str(e)}), 500
    
@branch_controller.route("/branch/<string:BranchCode>", methods=["GET"])
def get_branch_by_id(BranchCode):
    try:
        api = current_app.api
        response = api.fetch_table('Branch')
        keys = [
            "ID", "RowID", "BranchName", "BranchPhone", "BranchID", 
            "BranchNotes", "CreatedAt", "UpdatedAt", "Status", "IDCategory", 
            "BranchCode","BranchWeekDayOpen", "BranchWeekEndOpen", "BranchWeekDayClosed",
            "BranchImage", "BranchMinimumPurchase", "BranchWeekEndClosed", 
            "BranchAddress", "BranchCategoryName", "BranchCategoryID"
        ]
        data = [dict(zip(keys, item)) for item in response]
        filtered_items = [item for item in data if item['BranchCode'] == BranchCode]

        if filtered_items:
            return jsonify({
            "message": "Success get itemMenu by ID",
            "data": filtered_items
        }), 200
        else:
            return jsonify({'errorMessage': 'items not found'}), 404
    except requests.exceptions.RequestException as e:
        return jsonify({'errorMessage': str(e)}), 500
    
@branch_controller.route("/branch_quota/<string:BranchCode>", methods=["GET"])
def get_branch_quota(BranchCode):
    try:
        api = current_app.api
        response = api.fetch_table('BranchQuota')
        keys = [
            "ID", "RowID", "IDBranch", "BranchQuotaTime", "BranchQuotaPax", 
            "BranchQuotaID", "BranchName", "BranchCode"
        ]
        data = [dict(zip(keys, item)) for item in response]
        filtered_items = [item for item in data if item['BranchCode'] == BranchCode]

        if filtered_items:
            return jsonify({
            "message": "Success get branch quota by branch",
            "data": filtered_items
        }), 200
        else:
            return jsonify({'errorMessage': 'items not found'}), 404
    except requests.exceptions.RequestException as e:
        return jsonify({'errorMessage': str(e)}), 500