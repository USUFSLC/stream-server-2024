from functools import wraps
import typing
from os import environ
from flask import g, request, make_response
import jwt
from jwt import PyJWKClient
import requests

from fslc_stream.types import AuthorizationLevel

OIDC_CLIENT_ID = environ["OIDC_CLIENT_ID"]

jwks = PyJWKClient(
    f"https://idm.linux.usu.edu/oauth2/openid/{OIDC_CLIENT_ID}/public_key.jwk",
    cache_keys=True
)

def get_auth_level(roles: list[str]) -> AuthorizationLevel:
    if "leadership" in roles:
        return AuthorizationLevel.ADMIN
    if "streamer" in roles:
        return AuthorizationLevel.STREAMER
    return AuthorizationLevel.USER

def requires_authorization(required_level: AuthorizationLevel = AuthorizationLevel.USER):
    def decorator(f: typing.Callable):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if "__Secure-idToken" in request.cookies:
                access_token = request.cookies["__Secure-idToken"]
            else:
                return make_response("Please submit a JWT in a cookie.", 401)

            key = jwks.get_signing_key_from_jwt(access_token)
            try:
                payload = jwt.decode(
                    access_token,
                    key,
                    audience=OIDC_CLIENT_ID,
                    algorithms=["ES256"],
                    options={
                        "verify_jti": False
                    }
                )
            except jwt.exceptions.ExpiredSignatureError:
                return make_response("JWT is expired.", 401)

            g.payload = payload

            auth_level = get_auth_level(payload["roles"])

            g.auth_level = auth_level

            if auth_level >= required_level:
                return f(*args, **kwargs)
            else:
                return make_response(
                    f"Insufficient roles. Need {required_level.name}, found {auth_level.name}",
                    403
                )

        return wrapped

    return decorator

def teardown_payload(_):
    if "payload" in g:
        g.pop("payload")
    if "auth_level" in g:
        g.pop("auth_level")
