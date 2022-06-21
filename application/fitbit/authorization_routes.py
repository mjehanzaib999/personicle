
from flask import jsonify
from flask import request, session, redirect
from flask import Blueprint, g
from flask.wrappers import Response
from flask_cors import CORS, cross_origin
import requests
import pprint
import base64
from datetime import datetime
import threading
import logging

from application.config import FITBIT_CONFIG, HOST_CONFIG
from application.okta.helpers import  is_authorized
from application.utils.user_credentials_manager import verify_user_connection, add_access_token
import json
import asyncio

oauth_config = FITBIT_CONFIG
host = HOST_CONFIG

LOG = logging.getLogger(__name__)

# from application.utils.user_credential_manager import add_access_token
from .data_import_module import initiate_fitbit_data_import
from application.okta.helpers import is_authorized
from application.models.base import db

fitbit_routes = Blueprint("fitbit_routes", __name__)
CORS(fitbit_routes,resources={r"/*": {"origins": "*"}})

@fitbit_routes.route('/', methods=['GET'])
def test_route():
    return "Testing connections server"

@fitbit_routes.route('/fitbit/connection', methods=['GET', 'POST'])
def fitbit_connection():
    # if not is_authorized(request):
    #     print("not_authorized")
    #     return "Unauthorized", 401
   
    session.clear()
    request_data = request.args
    print('in fitbit connection function')
    session['user_id'] = request.args.get("user_id", None)
   
    if session['user_id'] is None:
        LOG.error("Unauthorised access: Denied")
        return Response("User not logged in", 401)
    
    # print('request data',request_data)
    session['redirect_url'] = request_data.get("redirect_uri")
    # if verify_user_connection(personicle_user_id=session['user_id'], connection_name='fitbit'):
    #     print('in verify user connection')
    #     status, activities_response = initiate_fitbit_data_import(session['user_id'])
    #     if status:
    #         LOG.info("Returning {}".format({'success': True, 'response': activities_response}))
    #         return jsonify({'success': True, 'response': activities_response})
    #     else:
    #         LOG.info("Returning {}".format({'success': False, 'response': activities_response}))
    #         return jsonify({'success': False, 'response': activities_response})
    
    return redirect('/fitbit/oauth/code-callback')
    

# OAuth call back with the client token
# store this and use to get access code
@fitbit_routes.route('/fitbit/oauth/code-callback/')
def get_token():
 
    pprint.pprint("inside /code-callback")
    print("Session user_id",session['user_id'])
    print("oauth_config user_id",oauth_config['CLIENT_ID'] )

    if session['user_id'] is None:
        return Response("User not logged in", 401)
    scope = "activity%20heartrate%20location%20nutrition%20profile%20sleep%20weight"
    #scope = "%20heartrate"
    print(session.keys())
    
    if 'user_id' not in session:
        return 'Use proper channels'
    if 'request_sent' not in session:
        print("Redirect url: {}".format(host['HOST_ADDRESS'] + oauth_config['REDIRECT_URL']))
        session['request_sent'] = True
        print("request sent")
        return redirect("{}?client_id={}&redirect_uri={}&scope={}&response_type=code".format(oauth_config['AUTH_URL'],
                oauth_config['CLIENT_ID'] ,host['HOST_ADDRESS'] + oauth_config['REDIRECT_URL'], scope))
    return "Already connected"


# Store the access token in sqlite db and initiate data import
@fitbit_routes.route('/fitbit/oauth/access-token/')
def get_access_token():
    print('In access token func')
    # session['user_id'] = request.args.get("user_id", None)
    if session['user_id'] is None:
        return Response("User not logged in", 401)
    # need personicle user id in session
    user_id = session['user_id']
    code = request.args.get('code')
    # print(session['user_id'])
    print('code', code)

    message = oauth_config['CLIENT_ID'] + ':' + oauth_config['CLIENT_SECRET']
    message_bytes = message.encode('ascii')
    base64_bytes = base64.b64encode(message_bytes)
    basic_code = base64_bytes.decode('ascii')


    request_params = {'grant_type': 'authorization_code',
                      'client_id': oauth_config['CLIENT_ID'],
                      'client_secret': oauth_config['CLIENT_SECRET'],
                      'code': code,
                      'redirect_uri': host['HOST_ADDRESS'] + oauth_config['REDIRECT_URL']}
    request_headers = {'Authorization': 'Basic {}'.format(basic_code),
                    'Content-Type': 'application/x-www-form-urlencoded'
                }
    resp = requests.post(oauth_config['REQUEST_URL'], data=request_params, headers=request_headers).json()

    resp["client_token"] = code

    pprint.pprint(resp)

    action ,user_record = add_access_token(user_id, service_name='fitbit', access_token=resp['access_token'], expires_in=resp['expires_in'],
                            created_at=datetime.utcnow(), external_user_id=resp['user_id'], refresh_token=resp['refresh_token'])

    try:
        if action == 'add':
            db.session.add(user_record)
        else:
            pass
        db.session.commit()
    except Exception as e:
        print(e)
        db.session.rollback()
        return jsonify(success=False)
    
    status, activities_response = initiate_fitbit_data_import(user_id)
    print('status', status)
    if status:
        LOG.info("Returning {}".format({'success': True, 'response': activities_response}))
        return jsonify({'success': True, 'response': activities_response})
    else:
        LOG.info("Returning {}".format({'success': False, 'response': activities_response}))
        return jsonify({'success': False, 'response': activities_response})

