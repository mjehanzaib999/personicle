from flask import jsonify
from flask import request, session, redirect,url_for
from flask import Blueprint
from flask_cors import CORS
from application.okta.helpers import  is_authorized

okta_routes = Blueprint("okta_routes", __name__)
CORS(okta_routes)

@okta_routes.route('/authenticate', methods=["GET", "POST"])
def authenticate():
    if not is_authorized(request):
        print('request',request)
        #print(is_authorized(request))
        return "Unauthorized", 401
   
    return jsonify({"message": True})
