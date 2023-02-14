from flask import Blueprint, request, make_response
from google.cloud import datastore
import constants
import functions as func

client = datastore.Client()
bp = Blueprint('boats', __name__, url_prefix='/boats')


@bp.route('', methods=['POST', 'GET', 'DELETE'])
def boats_get_post_delete1():
    if request.method == 'DELETE':
        return func.custom_json_response({"Error": "Method not allowed at this endpoint"}, 405)

    if request.method == 'POST':
        # checks if Accept header is application/json
        if str(request.accept_mimetypes) != 'application/json':
            return func.custom_json_response({"Error": "Accept header must be application/json"}, 406)

        # get jwt and verify it
        sub_prop = func.get_jwt()
        if sub_prop is None:
            return func.custom_json_response({"Error": "JWT token is either missing or invalid"}, 401)

        # checks if missing attributes are missing
        content = request.get_json()
        if len(content) < 3:
            return {"Error": "The request object is missing at least one of the required attributes"}, 400

        # create a boat
        new_boat = datastore.entity.Entity(key=client.key(constants.boats6))
        new_boat.update({"name": content["name"], "type": content["type"],
                         "length": content["length"], "loads": [], "owner": sub_prop})
        client.put(new_boat)
        self = request.base_url + '/' + str(new_boat.key.id)
        return func.custom_json_response({"id": new_boat.key.id, "name": content["name"], "type": content["type"],
                                          "length": content["length"], "loads": [], "owner": new_boat["owner"],
                                          "self": self}, 201)

    elif request.method == 'GET':
        # checks if Accept header is application/json
        if str(request.accept_mimetypes) != 'application/json':
            return func.custom_json_response({"Error": "Accept header must be application/json"}, 406)

        # checks if JWT is valid/missing
        sub_prop = func.get_jwt()
        if sub_prop is None:
            return func.custom_json_response({"Error": "JWT token is either missing or invalid"}, 401)

        # find how many boats are owned by an owner
        query01 = client.query(kind=constants.boats6)
        all_boats = list(query01.add_filter('owner', '=', sub_prop).fetch())
        total_boats = len(all_boats)

        # set pagination
        query = client.query(kind=constants.boats6)
        q_limit = int(request.args.get('limit', '5'))
        q_offset = int(request.args.get('offset', '0'))
        # select boats that are owned by current owner
        l_iterator = query.add_filter('owner', '=', sub_prop).fetch(limit=q_limit, offset=q_offset)
        pages = l_iterator.pages
        results = list(next(pages))
        if l_iterator.next_page_token:
            next_offset = q_offset + q_limit
            next_url = request.base_url + "?limit=" + str(q_limit) + "&offset=" + str(next_offset)
        else:
            next_url = None

        # add boat id and boat self and load self properties to response
        for e in results:
            e["id"] = e.key.id
            e["self"] = request.base_url + '/' + str(e["id"])
            for i in e["loads"]:
                i["self"] = request.host_url + 'loads/' + str(i["id"])
        output = {"boats": results, "total_number_of_boats": total_boats}
        if next_url:
            output["next"] = next_url
        return func.custom_json_response(output, 200)

    else:
        return 'Method not recognized'


@bp.route('/<boat_id>', methods=['GET', 'PUT', 'PATCH', 'DELETE'])
def boats_get_put_patch_delete(boat_id):
    if request.method == 'DELETE':
        # verifies JWT provided
        sub_prop = func.get_jwt()
        # check if JWT is invalid or missing
        if sub_prop is None:
            return func.custom_json_response({"Error": "JWT token is either missing or invalid"}, 401)

        # checks if the boat exists
        boat_key = client.key(constants.boats6, int(boat_id))
        boat = client.get(key=boat_key)
        if boat is None:
            return func.custom_json_response({"Error": "No boat with this boat_id exists"}, 404)

        # check if sub is the same, shows boat's owner
        if boat['owner'] != sub_prop:
            return func.custom_json_response({"Error": "Boat is owned by someone else"}, 403)

        # deletes boat and removes all loads in the boat
        for i in boat['loads']:
            load_key = client.key(constants.loads1, int(i['id']))
            load = client.get(key=load_key)
            load['carrier'] = None
            client.put(load)
        client.delete(boat_key)
        return func.custom_json_response('', 204)

    elif request.method == 'PUT':
        # verifies JWT provided
        sub_prop = func.get_jwt()
        # check if JWT is invalid or missing
        if sub_prop is None:
            return func.custom_json_response({"Error": "JWT token is either missing or invalid"}, 401)

        # checks if Accept header is application/json
        if str(request.accept_mimetypes) != 'application/json':
            return func.custom_json_response({"Error": "Accept header must be application/json"}, 406)

        # checks if boat key exists
        boat_key = client.key(constants.boats6, int(boat_id))
        boat = client.get(key=boat_key)
        if boat is None:
            return func.custom_json_response({"Error": "No boat with this boat_id exists"}, 404)

        # checks of there are missing attributes
        content = request.get_json()
        if len(content) != 3:
            return func.custom_json_response(
                {"Error": "The request object is missing or has more attributes than required"}, 400)

        # check if sub is the same, shows boat's owner
        if boat['owner'] != sub_prop:
            return func.custom_json_response({"Error": "Boat is owned by someone else"}, 403)

        # updates boat content in the datastore
        boat.update({"name": content["name"], "type": content["type"],
                     "length": content["length"]})
        client.put(boat)

        # returns response to client
        self = request.base_url
        response = {"id": boat.key.id, "name": content["name"], "type": content["type"],
                    "length": content["length"], "loads": boat["loads"], "owner": boat["owner"], "self": self}
        return func.custom_json_response(response, 200)

    elif request.method == 'PATCH':
        # verifies JWT provided
        sub_prop = func.get_jwt()
        # check if JWT is invalid or missing
        if sub_prop is None:
            return func.custom_json_response({"Error": "JWT token is either missing or invalid"}, 401)

        # checks if Accept header is application/json
        if str(request.accept_mimetypes) != 'application/json':
            return func.custom_json_response({"Error": "Accept header must be application/json"}, 406)

        # checks if boat key exists
        boat_key = client.key(constants.boats6, int(boat_id))
        boat = client.get(key=boat_key)
        if boat is None:
            return func.custom_json_response({"Error": "No boat with this boat_id exists"}, 404)

        # checks of there are missing attributes
        content = request.get_json()
        if len(content) == 0 or len(content) > 3:
            return func.custom_json_response(
                {"Error": "The request object is missing or has more attributes than required"}, 400)

        # check if sub is the same, shows boat's owner
        if boat['owner'] != sub_prop:
            return func.custom_json_response({"Error": "Boat is owned by someone else"}, 403)

        # updates boat content in the datastore
        for key, val in content.items():
            boat.update({key: val})
            client.put(boat)

        # returns response to client
        self = request.base_url
        response = {"id": boat.key.id, "name": boat["name"], "type": boat["type"],
                    "length": boat["length"], "loads": boat["loads"], "owner": boat["owner"], "self": self}
        return func.custom_json_response(response, 200)

    elif request.method == 'GET':
        sub_prop = func.get_jwt()
        if sub_prop is None:
            return func.custom_json_response({"Error": "JWT token is either missing or invalid"}, 401)

        # checks if Accept header is application/json
        if str(request.accept_mimetypes) != 'application/json':
            return func.custom_json_response({"Error": "Accept header must be application/json"}, 406)

        # checks if boat id exists
        boat_key = client.key(constants.boats6, int(boat_id))
        boat = client.get(key=boat_key)
        if boat is None:
            return func.custom_json_response({"Error": "No boat with this boat_id exists"}, 404)

        # add boat id and self to the response
        if boat['owner'] == sub_prop:
            boat["id"] = boat.key.id
            boat["self"] = request.host_url + 'boats/' + str(boat["id"])
            if len(boat["loads"]) != 0:
                for i in boat["loads"]:
                    i["self"] = request.host_url + 'loads/' + str(i["id"])
            return func.custom_json_response(boat, 200)
        else:
            return func.custom_json_response({"Error": "Cannot view this boat. Boat is owned by someone else"}, 403)
    else:
        return 'Method not recognized'


@bp.route('/<boat_id>/loads/<load_id>', methods=['PUT', 'DELETE'])
def add_delete_load_to_boat(boat_id, load_id):
    if request.method == 'PUT':
        # add a load to a boat
        boat_key = client.key(constants.boats6, int(boat_id))
        boat = client.get(key=boat_key)
        load_key = client.key(constants.loads1, int(load_id))
        load = client.get(key=load_key)
        if (boat is None) or (load is None):
            return {"Error": "The specified boat and/or load does not exist"}, 404
        if load['carrier'] is not None:
            return {"Error": "The load is already loaded on another boat"}, 403
        boat['loads'].append({"id": load.id})
        load['carrier'] = {"id": boat.id}
        client.put(boat)
        client.put(load)
        return func.custom_json_response('', 204)

    if request.method == 'DELETE':
        # remove a load from a boat
        load_on_boat = False
        boat_key = client.key(constants.boats6, int(boat_id))
        boat = client.get(key=boat_key)
        load_key = client.key(constants.loads1, int(load_id))
        load = client.get(key=load_key)
        if (boat is None) or (load is None):
            return func.custom_json_response({"Error": "The specified boat and/or load does not exist"}, 404)
        for i in boat['loads']:
            if i['id'] == int(load_id):
                load_on_boat = True
                boat['loads'].remove(i)
        if load_on_boat is False:
            return func.custom_json_response({"Error": "This load is not assigned to this boat, and therefore cannot be removed"}, 403)
        load['carrier'] = None
        client.put(boat)
        client.put(load)
        return func.custom_json_response('', 204)
