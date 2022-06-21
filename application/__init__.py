from flask import Flask
# from flask import request, session, redirect
# from flask_sqlalchemy import SQLAlchemy
import os

from . import config
from logging.config import fileConfig
from flask_cors import CORS
import logging
import pprint


# LOG = logging.getLogger()

def create_app():
    from . import models, fitbit, ios_healthkit, google_fit,okta_authenticate
    
    app = Flask(__name__)
    CORS(app)
    app.secret_key = os.urandom(24)
    os.makedirs(config.SQLITE_DATABASE_LOCATION, exist_ok=True)

    if os.environ.get("INGESTION_PROD", '0') != '1':
        fileConfig('logging.cfg')
    else:
        # fileConfig('logging.cfg')
        # TO DO: use replace file based logging with gunicorn logger 
        gunicorn_logger = logging.getLogger('gunicorn.error')
        app.logger.handlers = gunicorn_logger.handlers
        app.logger.setLevel(gunicorn_logger.level)

   
    print("Setting up okta")
   
    if os.environ.get("INGESTION_PROD", "0") == '1':
        # in prod env, need to create okta config json file from env variable
        print('in dir loop')
        os.makedirs("config_json", exist_ok=True)
        #os.makedirs("config_json", exist_ok=False)
        pprint.pprint(os.environ.get("OKTA_SECRETS_JSON", "MISSING_OKTA_FILE"))
        with open("config_json/client_secrets.json", "w") as fp:
            fp.write(os.environ.get("OKTA_SECRETS_JSON", "MISSING_OKTA_FILE"))
        if "OKTA_SECRETS_JSON" not in os.environ:
            print("Missing okta secrets in environment")
            # LOG.error("Missing okta secrets in environment")
    try:
        
        okta_authenticate.init_app(app)
    except Exception as e:
        print(e)
        raise e
    # Add database URI here
    # Database url format/
    # dialect+driver://username:password@host:port/database
    # e.g., postgresql+pg8000://dbuser:kx%25jj5%2Fg@pghost10/appdb
    #   if os.environ.get("INGESTION_PROD", '0') != '1':
    # app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://{username}:{password}@{dbhost}/{dbname}".format(username=os.environ['CREDENTIALS_DB_USER'], password=os.environ['CREDENTIALS_DB_PASSWORD'],
    #                                                                                                             dbhost=os.environ['CREDENTIALS_DB_HOST'], dbname=os.environ['CREDENTIALS_DB_NAME'])
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///{}".format(os.path.join(config.SQLITE_DATABASE_LOCATION, config.SQLITE_DATABASE_NAME))

    print("Setting up sqlalchemy")
    models.init_app(app)
    
    print("Setting up data apps")
    fitbit.init_app(app)
    ios_healthkit.init_app(app)
    google_fit.init_app(app)
    
    # services.init_app(app)
    return app

# app = create_app()
