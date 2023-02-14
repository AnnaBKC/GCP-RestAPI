from flask import Blueprint, request, make_response
from google.auth.transport import requests
from google.cloud import datastore
from google.oauth2 import id_token
import json, constants


def custom_json_response(body_res, status_code):
    """
    :param body_res: Dictionary with string containing error message
    :param status_code: Integer containing the status code
    :return: Returns response body, status code and sets content-type header
    """
    res = make_response((json.dumps(body_res)))
    res.headers.set('Content-Type', 'application/json')
    res.status_code = status_code
    return res


def content_not_json():
    """
    :return: Returns response if request content is not in JSON format
    """
    return custom_json_response(
        {"Error": "Request body is not in JSON format. Please send request body in JSON format"},
        415)


def verify_jwt(token):
    """
    Verifies JWT using Google API Client Library
    and if JWT is valid, it returns sub attribute
    """
    try:
        # Specify the CLIENT_ID of the app that accesses the backend:
        idinfo = id_token.verify_oauth2_token(token, requests.Request(), constants.client_id)
        # ID token is valid. Get the user's Google Account ID from the decoded token.
        userid = idinfo['sub']
        print("SUB: ", userid)
        return userid
    except ValueError:
        print("Invalid JWT token")


def get_jwt():
    """
    Retrieves JWT from authorization headers.
    """
    if 'Authorization' in request.headers:
        auth_header = request.headers['Authorization'].split()
        jwt_token = auth_header[1]
        return verify_jwt(jwt_token)