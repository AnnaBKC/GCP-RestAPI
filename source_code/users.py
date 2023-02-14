from flask import Blueprint, request
from google.cloud import datastore
import constants
import functions as func


client = datastore.Client()
bp = Blueprint('users', __name__, url_prefix='/users')


@bp.route('', methods=['GET', 'DELETE'])
def get_users():
    if request.method == 'DELETE':
        return func.custom_json_response({"Error": "Method not allowed at this endpoint"}, 405)

    if request.method == 'GET':
        # checks if Accept header is application/json
        if str(request.accept_mimetypes) != 'application/json':
            return func.custom_json_response({"Error": "Accept header must be application/json"}, 406)

        # displays all users in the Entity
        query = client.query(kind=constants.users)
        results = list(query.fetch())
        return func.custom_json_response(results, 200)
    else:
        return 'Method not recognized'
