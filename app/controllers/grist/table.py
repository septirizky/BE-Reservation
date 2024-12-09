from flask import Blueprint, jsonify, current_app
import requests

table_controller = Blueprint("table_controller", __name__)
    
@table_controller.route("/table_area/<string:BranchCode>", methods=["GET"])
def get_table_area_branch(BranchCode):
    try:
        api = current_app.api
        response = api.fetch_table('Tables_Area')
        keys = [
            "ID", "RowID", "AreaName", "Status", "TableAreaID", 
            "IDBranch", "AreaCode", "ta_id", "CreatedAt", "UpdatedAt",   
            "Order", "BranchID", "BranchCode", "AreaImage", "BranchName"
        ]
        data = [dict(zip(keys, item)) for item in response]

        filtered_items = [item for item in data if item['BranchCode'] == BranchCode]

        if filtered_items:
            return jsonify({
            "message": "Success get table by branch",
            "data": filtered_items
        }), 200
        else:
            return jsonify({'errorMessage': 'items not found'}), 404
    except requests.exceptions.RequestException as e:
        return jsonify({'errorMessage': str(e)}), 500
    
@table_controller.route("/table_section/<string:BranchCode>", methods=["GET"])
def get_table_section_branch(BranchCode):
    try:
        api = current_app.api
        response = api.fetch_table('TablesSection')
        keys = [
            "ID", "RowID", "TableSectionID", "IDBranch", "TableSectionImage", 
            "TableSectionName", "Status", "CreatedAt", "UpdatedAt", "ts_id",
            "BranchID", "Order", "BranchName", "BranchCode"
        ]
        data = [dict(zip(keys, item)) for item in response]

        filtered_items = [item for item in data if item['BranchCode'] == BranchCode]

        if filtered_items:
            return jsonify({
            "message": "Success get table by branch",
            "data": filtered_items
        }), 200
        else:
            return jsonify({'errorMessage': 'items not found'}), 404
    except requests.exceptions.RequestException as e:
        return jsonify({'errorMessage': str(e)}), 500
    
@table_controller.route("/table/<string:TableSectionName>", methods=["GET"])
def get_table_branch(TableSectionName):
    try:
        api = current_app.api
        response = api.fetch_table('Tables')

        keys = [
            "ID", "RowID", "TableNumber", "IDTableSection", 
            "TableID", "Status", "CreatedAt", "UpdatedAt", "IDBranch", 
            "t_id", "BranchCode", "TableSectionID", "TableSectionName", "BranchName"
        ]
        data = [dict(zip(keys, item)) for item in response]

        filtered_items = [item for item in data if item['TableSectionName'] == TableSectionName]

        if filtered_items:
            return jsonify({
            "message": "Success get table by branch",
            "data": filtered_items
        }), 200
        else:
            return jsonify({'errorMessage': 'items not found'}), 404
    except requests.exceptions.RequestException as e:
        return jsonify({'errorMessage': str(e)}), 500
    
@table_controller.route("/table", methods=["GET"])
def get_table():
    try:
        api = current_app.api
        response = api.fetch_table('Tables')

        return jsonify({
            "message": "Success get table by branch",
            "data": response
        }), 200
    except requests.exceptions.RequestException as e:
        return jsonify({'errorMessage': str(e)}), 500