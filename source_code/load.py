from flask import Blueprint, request, make_response
from google.cloud import datastore
import constants
import functions as func

client = datastore.Client()
bp = Blueprint('load', __name__, url_prefix='/loads')


@bp.route('', methods=['POST', 'GET', 'DELETE'])
def loads_get_post_delete():
    if request.method == 'DELETE':
        return func.custom_json_response({"Error": "Method not allowed at this endpoint"}, 405)

    if request.method == 'POST':
        # checks if Accept header is application/json
        if str(request.accept_mimetypes) != 'application/json':
            return func.custom_json_response({"Error": "Accept header must be application/json"}, 406)

        # check if there are missing attributes
        content = request.get_json()
        if len(content) < 3:
            return {"Error": "The request object is missing at least one of the required attributes"}, 400

        # create a load
        new_load = datastore.entity.Entity(key=client.key(constants.loads1))
        new_load.update({"volume": content["volume"], "item": content["item"],
                         "creation_date": content["creation_date"], "carrier": None})
        client.put(new_load)
        self = request.base_url + '/' + str(new_load.key.id)
        return func.custom_json_response({"id": new_load.key.id, "volume": content["volume"], "item": content["item"],
                                          "creation_date": content["creation_date"], "carrier": None, "self": self},
                                         201)

    elif request.method == 'GET':
        # checks if Accept header is application/json
        if str(request.accept_mimetypes) != 'application/json':
            return func.custom_json_response({"Error": "Accept header must be application/json"}, 406)

        # get the total number of loads
        query = client.query(kind=constants.loads1)
        total_loads = len(list(query.fetch()))

        # set up pagination
        query = client.query(kind=constants.loads1)
        q_limit = int(request.args.get('limit', '5'))
        q_offset = int(request.args.get('offset', '0'))
        l_iterator = query.fetch(limit=q_limit, offset=q_offset)
        pages = l_iterator.pages
        results = list(next(pages))
        if l_iterator.next_page_token:
            next_offset = q_offset + q_limit
            next_url = request.base_url + "?limit=" + str(q_limit) + "&offset=" + str(next_offset)
        else:
            next_url = None

        # adds id and self to the response
        for e in results:
            e["id"] = e.key.id
            e["self"] = request.base_url + '/' + str(e["id"])
            if e["carrier"] is not None:
                e["carrier"]["self"] = request.host_url + 'boats/' + str(e["carrier"]["id"])
        output = {"loads": results, "total_number_of_loads": total_loads}
        if next_url:
            output["next"] = next_url
        return func.custom_json_response(output, 200)
    else:
        return 'Method not recognized'


@bp.route('/<load_id>', methods=['GET', 'PATCH', 'PUT', 'DELETE'])
def loads_get_patch_put_delete(load_id):
    if request.method == 'DELETE':
        load_key = client.key(constants.loads1, int(load_id))
        load = client.get(key=load_key)
        if load is None:
            return {"Error": "No load with this load_id exists"}, 404

        # delete load and remove load from boat
        if load['carrier'] is not None:
            boat_key = client.key(constants.boats6, int(load['carrier']['id']))
            boat = client.get(key=boat_key)
            for i in boat['loads']:
                if i['id'] == int(load_id):
                    boat['loads'].remove(i)
                    client.put(boat)
        client.delete(load_key)
        return func.custom_json_response('', 204)

    elif request.method == 'PUT':
        # checks if Accept header is application/json
        if str(request.accept_mimetypes) != 'application/json':
            return func.custom_json_response({"Error": "Accept header must be application/json"}, 406)

        # checks if boat key exists
        load_key = client.key(constants.loads1, int(load_id))
        load = client.get(key=load_key)
        if load is None:
            return func.custom_json_response({"Error": "No load with this load_id exists"}, 404)

        # checks if there are missing attributes
        content = request.get_json()
        if len(content) != 3:
            return func.custom_json_response(
                {"Error": "The request object is missing or has more attributes than required"}, 400)

        # updates boat content in the datastore
        load.update({"volume": content["volume"], "item": content["item"],
                     "creation_date": content["creation_date"]})
        client.put(load)

        # returns response to client
        self = request.base_url
        response = {"id": load.key.id, "volume": content["volume"], "item": content["item"],
                    "creation_date": content["creation_date"], "carrier": load["carrier"], "self": self}
        if response["carrier"] is not None:
            response["carrier"]["self"] = request.host_url + 'boats/' + str(load["carrier"]["id"])
        return func.custom_json_response(response, 200)

    elif request.method == 'PATCH':
        # checks if Accept header is application/json
        if str(request.accept_mimetypes) != 'application/json':
            return func.custom_json_response({"Error": "Accept header must be application/json"}, 406)

        # checks if boat key exists
        load_key = client.key(constants.loads1, int(load_id))
        load = client.get(key=load_key)
        if load is None:
            return func.custom_json_response({"Error": "No load with this load_id exists"}, 404)

        # checks of there are missing attributes
        content = request.get_json()
        if len(content) == 0 or len(content) > 3:
            return func.custom_json_response(
                {"Error": "The request object is missing or has more attributes than required"}, 400)

        # updates boat content in the datastore
        for key, val in content.items():
            load.update({key: val})
            client.put(load)

        # returns response to client
        self = request.base_url
        response = {"id": load.key.id, "volume": load["volume"], "item": load["item"],
                    "creation_date": load["creation_date"], "carrier": load["carrier"], "self": self}
        if response["carrier"] is not None:
            response["carrier"]["self"] = request.host_url + 'boats/' + str(load["carrier"]["id"])
        return func.custom_json_response(response, 200)

    elif request.method == 'GET':
        # checks if Accept header is application/json
        if str(request.accept_mimetypes) != 'application/json':
            return func.custom_json_response({"Error": "Accept header must be application/json"}, 406)

        # check if load id exists
        load_key = client.key(constants.loads1, int(load_id))
        load = client.get(key=load_key)
        if load is None:
            return func.custom_json_response({"Error": "No load with this load_id exists"}, 404)

        # adds id and self to the response
        load["id"] = load.key.id
        load["self"] = request.host_url + 'loads/' + str(load["id"])
        if load["carrier"] is not None:
            load["carrier"]["self"] = request.host_url + 'boats/' + str(load["carrier"]["id"])
        return func.custom_json_response(load, 200)
    else:
        return 'Method not recognized'
