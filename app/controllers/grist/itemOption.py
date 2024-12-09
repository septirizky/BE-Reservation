from flask import Blueprint, jsonify, current_app
import requests

itemOption_controller = Blueprint("itemOption_controller", __name__)


@itemOption_controller.route("/item_option", methods=["GET"])
def get_itemOption():
    try:
        api = current_app.api
        response = api.fetch_table("ItemOption")
        keys = [
            "ID", "RowID", "IDBranch", "IDOption", "IDCategory", "ItemOptionID", 
            "IDMenu", "CreatedAt", "UpdatedAt", "BranchName", "BranchID", 
            "OptionName", "OptionsID", "CategoryMenuName", "CategoryItemID", 
            "MenuName", "MenusID", "OptionText", "op_id"
        ]
        data = [dict(zip(keys, item)) for item in response]
        return jsonify({
            "message": "Success get itemOption",
            "data": data
        }), 200
    except requests.exceptions.RequestException as e:
        return jsonify({'errorMessage': str(e)}), 500
    

@itemOption_controller.route("/option_category/<string:CategoryItemID>", methods=["GET"])
def get_itemOption_categoryId(CategoryItemID):
    try:
        api = current_app.api
        response = api.fetch_table("ItemOption")
        keys = [
            "ID", "RowID", "IDBranch", "IDOption", "IDCategory", "ItemOptionID", 
            "IDMenu", "CreatedAt", "UpdatedAt", "BranchName", "BranchID", 
            "OptionName", "OptionsID", "CategoryMenuName", "CategoryItemID", 
            "MenuName", "MenusID", "OptionText", "op_id"
        ]
        data = [dict(zip(keys, item)) for item in response]

        filtered_items = [item for item in data if item['CategoryItemID'] == CategoryItemID]

        if filtered_items:
            return jsonify({
            "message": "Success get itemOption by CategoryMenuName",
            "data": filtered_items
        }), 200
        else:
            return jsonify({'errorMessage': 'items not found'}), 404
    except requests.exceptions.RequestException as e:
        return jsonify({'errorMessage': str(e)})
    

@itemOption_controller.route("/option_menu/<string:MenusID>", methods=["GET"]) 
def get_itemOption_menuId(MenusID):
    try:
        api = current_app.api
        response = api.fetch_table("ItemOption")
        keys = [
            "ID", "RowID", "IDBranch", "IDOption", "IDCategory", "ItemOptionID", 
            "IDMenu", "CreatedAt", "UpdatedAt", "BranchName", "BranchID", 
            "OptionName", "OptionsID", "CategoryMenuName", "CategoryItemID", 
            "MenuName", "MenusID", "OptionText", "op_id"
        ]
        data = [dict(zip(keys, item)) for item in response]

        filtered_items = [item for item in data if item['MenusID'] == MenusID]

        if filtered_items:
            return jsonify({
            "message": "Success get itemOption by MenuName",
            "data": filtered_items
        }), 200
        else:
            return jsonify({'errorMessage': 'items not found'}), 404
    except requests.exceptions.RequestException as e:
        return jsonify({'errorMessage': str(e)})