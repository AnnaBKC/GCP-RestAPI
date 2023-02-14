import constants
import json
import secrets
import requests as rq
from flask import Flask, request, render_template
from google.cloud import datastore
import boat
import load
import users

app = Flask(__name__)
app.register_blueprint(boat.bp)
app.register_blueprint(load.bp)
app.register_blueprint(users.bp)
client = datastore.Client()

redirect_uri = "https://project-klemzcea.ue.r.appspot.com/oauth"
# redirect_uri = "http://localhost:8080/oauth"
scope = "profile"
google_url = f"https://accounts.google.com/o/oauth2/v2/auth"
token_URL = "https://oauth2.googleapis.com/token"
resource_URL = "https://people.googleapis.com/v1/people/me?personFields=names"


def delete_states():
    """
    Deletes all states stored at the Datastore
    """
    query = client.query(kind=constants.oauth3)
    results = list(query.fetch())
    for e in results:
        client.delete(e)


@app.route('/', methods=['POST', 'GET'])
def index():
    # deletes previous states
    delete_states()
    # generate random state
    state = secrets.token_hex(10)
    # store state in the Datastore
    new_state = datastore.entity.Entity(key=client.key(constants.oauth3))
    new_state.update({"state": state})
    client.put(new_state)
    # Google OAuth2.0 endpoint
    request_URL = f"{google_url}?access_type=offline&response_type=code&client_id={constants.client_id}" \
                  f"&redirect_uri={redirect_uri}&scope={scope}&state={state}"
    return render_template('home.html', URL=request_URL)


@app.route('/oauth', methods=['GET'])
def oauth():
    if request.method == 'GET':
        # receive google response and retrieve the access code and state
        access_code = request.args.get('code')
        state = request.args.get('state')
        query = client.query(kind=constants.oauth3)
        results = list(query.fetch())
        # verify if received state value matches state value stored in the Datastore
        if results[0]["state"] == state:
            # request access token from google
            token_response = rq.post(
                f"{token_URL}?code={access_code}&client_id={constants.client_id}&client_secret={constants.client_secret}"
                f"&redirect_uri={redirect_uri}&grant_type=authorization_code")
            access_token = token_response.json()['access_token']
            # use access token to access protected resource
            resource_res = rq.get(f"{resource_URL}", headers={"Authorization": f"Bearer {access_token}"}).content
            resources = json.loads(resource_res)
            # save sub from response
            sub_prop = resources['names'][0]['metadata']['source']['id']
            jwt = token_response.json()['id_token']

            # check if sub property as already been added in entity users
            query = client.query(kind=constants.users)
            results = list(query.fetch())
            found_sub = False
            for i in results:
                if sub_prop in i.values():
                    found_sub = True
            if found_sub is False:
                new_user = datastore.entity.Entity(key=client.key(constants.users))
                new_user.update({"user_id": sub_prop})
                client.put(new_user)

            # display JWT and user id in user page
            return render_template('userInfo.html', jwt=jwt, user_id=sub_prop)
        else:
            return "<h1>State provided does not match</h1"
    else:
        return 'Method not recognized'


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)