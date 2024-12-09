from flask import Blueprint, request, jsonify, current_app
import requests

categoryItemMenu_controller = Blueprint("categoryItemMenu_controller", __name__)


@categoryItemMenu_controller.route("/category_item_menu", methods=["GET"])
def get_categoryItemMenu():
    try:
        api = current_app.api
        response = api.fetch_table('CategoryItemMenu')
        keys = [
            "ID", "RowID", "CategoryName", "CreatedAt", "UpdatedAt", "Order", 
            "Status", "IDBranch", "CategoryItemID", "Nol", 
            "BranchCode", "BranchID", "BranchName", "CategoryImage"
        ]
        data = [dict(zip(keys, item)) for item in response]
        return jsonify({
            "message": "Success get categoryItemMenu",
            "data": data
        }), 200
    except requests.exceptions.RequestException as e:
        return jsonify({'errorMessage': str(e)}), 500
    
@categoryItemMenu_controller.route("/category_item_menu/<string:BranchCode>", methods=["GET"])
def get_categoryItemMenu_by_id(BranchCode):
    try:
        api = current_app.api
        response = api.fetch_table('CategoryItemMenu')
        keys = [
            "ID", "RowID", "CategoryName", "CreatedAt", "UpdatedAt", "Order", 
            "Status", "IDBranch", "CategoryItemID", "Nol", 
            "BranchCode", "BranchID", "BranchName", "CategoryImage"
        ]
        data = [dict(zip(keys, item)) for item in response]

        filtered_items = [item for item in data if item['BranchCode'] == BranchCode]

        if filtered_items:
            return jsonify({
            "message": "Success get categoryItemMenu by ID",
            "data": filtered_items
        }), 200
        else:
            return jsonify({'errorMessage': 'Category items not found'}), 404
    except requests.exceptions.RequestException as e:
        return jsonify({'errorMessage': str(e)}), 500
    
@categoryItemMenu_controller.route("/upload_category_url/<string:CategoryItemID>", methods=["POST"])
def upload_categoryItemMenu(CategoryItemID):
    new_record = request.get_json()
    
    if not new_record:
        return jsonify({'error': 'No data provided'}), 400

    new_record['CategoryItemID'] = CategoryItemID
    records = [new_record]
    
    try:
        api = current_app.api
        response = api.add_records('ImageCategoryUploaded', records)
        if response:
            return jsonify({"message": "Data berhasil diinput", "data": records}), 201
        else:
            return jsonify({"message": "Gagal input data"}), 400
    except requests.exceptions.RequestException as e:
        return jsonify({'error': str(e)}), 500