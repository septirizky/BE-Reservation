from flask import Blueprint, jsonify, current_app
import requests

option_controller = Blueprint("option_controller", __name__)


@option_controller.route("/option", methods=["GET"])
def get_option():
    try:
        api = current_app.api
        response = api.fetch_table("Options")
        keys = [
            "ID", "RowID", "IDOptionsCategory", "OptionsCode", "OptionsHide", 
            "OptionsPriceMod", "UpdatedAt", "Status", "OptionsName", "OptionsID", 
            "IDBranch", "CreatedAt", "op_id", "BranchName", "BranchCode", 
            "OptionsCategoryName", "OptionsCategoryID", "OptionsCategoryText"
        ]
        data = [dict(zip(keys, item)) for item in response]
        return jsonify({
            "message": "Success get option",
            "data": data
        }), 200
    except requests.exceptions.RequestException as e:
        return jsonify({'errorMessage': str(e)}), 500


@option_controller.route("/option/<string:BranchCode>", methods=["GET"])
def get_option_by_id(BranchCode):
    try:
        api = current_app.api
        response = api.fetch_table("Options")
        keys = [
            "ID", "RowID", "IDOptionsCategory", "OptionsCode", "OptionsHide", 
            "OptionsPriceMod", "UpdatedAt", "Status", "OptionsName", "OptionsID", 
            "IDBranch", "CreatedAt", "op_id", "BranchName", "BranchCode", 
            "OptionsCategoryName", "OptionsCategoryID", "OptionsCategoryText"
        ]
        data = [dict(zip(keys, item)) for item in response]

        filtered_items = [item for item in data if item['BranchCode'] == BranchCode]

        if filtered_items:
            return jsonify({
            "message": "Success get option by BranchCode",
            "data": filtered_items
        }), 200
        else:
            return jsonify({'errorMessage': 'items not found'}), 404
    except requests.exceptions.RequestException as e:
        return jsonify({'errorMessage': str(e)})