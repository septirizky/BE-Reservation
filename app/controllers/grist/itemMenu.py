from flask import Blueprint, request, jsonify, current_app
import requests

itemMenu_controller = Blueprint("itemMenu_controller", __name__)

@itemMenu_controller.route("/item_menu", methods=["GET"])
def get_itemMenu():
    try:
        api = current_app.api
        response = api.fetch_table('ItemMenu')
        keys = [
            "ID", "RowID", "MenuName", "Description", "MenuPrice", "MenusID", 
            "CreatedAt", "UpdatedAt", "Status", "Order", "MenusCode", "MenusKind", 
            "MenuSoldOut", "MenusSellLimit","Nol", "IDCategory", "IDBranch", 
            "i_id", "CookingCharge", "MenuPackageDetail", "MenuPackage", "TaxFree",
            "CategoryItemID", "BranchCode", "CategoryName", "BranchName", "MenusImage"
        ]
        data = [dict(zip(keys, item)) for item in response]
        return jsonify({
            "message": "Success get itemMenu",
            "data": data
        }), 200
    except requests.exceptions.RequestException as e:
        return jsonify({'errorMessage': str(e)}), 500
    
@itemMenu_controller.route("/item_menu/<string:BranchCode>", methods=["GET"])
def get_itemMenu_by_id(BranchCode):
    try:
        api = current_app.api
        response = api.fetch_table('ItemMenu')
        keys = [
            "ID", "RowID", "MenuName", "Description", "MenuPrice", "MenusID", 
            "CreatedAt", "UpdatedAt", "Status", "Order", "MenusCode", "MenusKind", 
            "MenuSoldOut", "MenusSellLimit","Nol", "IDCategory", "IDBranch", 
            "i_id", "CookingCharge", "MenuPackageDetail", "MenuPackage", "TaxFree",
            "CategoryItemID", "BranchCode", "CategoryName", "BranchName", "MenusImage"
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
    
@itemMenu_controller.route("/upload_menu_url/<string:MenusID>", methods=["POST"])
def upload_menu(MenusID):
    new_record = request.get_json()
    
    if not new_record:
        return jsonify({'error': 'No data provided'}), 400

    new_record['MenusID'] = MenusID
    records = [new_record]
    
    try:
        api = current_app.api
        response = api.add_records('ImageItemUploaded', records)
        if response:
            return jsonify({"message": "Data berhasil diinput", "data": records}), 201
        else:
            return jsonify({"message": "Gagal input data"}), 400
    except requests.exceptions.RequestException as e:
        return jsonify({'error': str(e)}), 500