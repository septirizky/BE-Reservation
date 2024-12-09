from flask import Blueprint, request, jsonify, current_app
import requests

itemPackage_controller = Blueprint("itemPackage_controller", __name__)

@itemPackage_controller.route("/item_package", methods=["GET"])
def get_itemPackage():
    try:
        api = current_app.api
        response = api.fetch_table('ItemMenuPackage')
        keys = [
            "ID", "RowID", "ItemPackageDetailID", "IDMenus", "IDPaket", 
            "IDBranch", "IDOptionPackage", "AltMenuName", "IDItemOptionPackage",
            "ItemPackageDetailPrice", "PackageID", "PackageName", "ItemPackageDetail", 
            "BranchName", "ItemChild_i_id", "OptionPackage", "MaxChoosen", "BranchCode", 
            "ItemOptionPackage", "Package_op_id", "MinChoosen", "AutoInsert", "ItemPackage_i_id" 
        ]
        data = [dict(zip(keys, item)) for item in response]
        return jsonify({
            "message": "Success get item package",
            "data": data
        }), 200
    except requests.exceptions.RequestException as e:
        return jsonify({'errorMessage': str(e)}), 500
    
@itemPackage_controller.route("/item_package/<string:BranchCode>", methods=["GET"])
def get_itemPackage_by_id(BranchCode):
    try:
        api = current_app.api
        response = api.fetch_table('ItemMenuPackage')
        keys = [
            "ID", "RowID", "ItemPackageDetailID", "IDMenus", "IDPaket", 
            "IDBranch", "IDOptionPackage", "AltMenuName", "IDItemOptionPackage",
            "PackageID", "PackageName", "ItemPackageDetail", "BranchName",  
            "OptionPackage", "ItemPackage_i_id", "MaxChoosen", "BranchCode", 
            "ItemOptionPackage", "ItemChild_i_id", "Package_op_id", "MinChoosen"
        ]
        data = [dict(zip(keys, item)) for item in response]

        filtered_items = [item for item in data if item['BranchCode'] == BranchCode]

        if filtered_items:
            return jsonify({
            "message": "Success get item package by Branch",
            "data": filtered_items
        }), 200
        else:
            return jsonify({'errorMessage': 'items not found'}), 404
    except requests.exceptions.RequestException as e:
        return jsonify({'errorMessage': str(e)}), 500