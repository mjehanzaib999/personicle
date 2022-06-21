import asyncio
import json

from okta_jwt_verifier import AccessTokenVerifier, IDTokenVerifier
loop = asyncio.get_event_loop()

def is_authorized(request):
    try:
        #token = request.headers.get("Authorization").split("Bearer ")[1]
        token = request.args.get("access_token", None)
        #print(config["issuer"])
        #print(is_access_token_valid(token, config["issuer"]))
        print('token',token)
        print("Access token",is_access_token_valid(token, config["issuer"]))
        print('after')
        return is_access_token_valid(token, config["issuer"])
    except Exception:
        return False


def is_access_token_valid(token, issuer):
    print("is access token valid")
    jwt_verifier = AccessTokenVerifier(issuer=issuer, audience='api://default')
    try:
        loop.run_until_complete(jwt_verifier.verify(token))
        return True
    except Exception:
        return False

def load_config(fname='config_json/client_secrets.json'):
    config = None
    with open(fname) as f:
        #print(f) ########
        config = json.load(f)
        print("config", config)
    return config


config = load_config()
