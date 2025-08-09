from functools import wraps
import typing
from os import environ
from flask import current_app, g, request, make_response
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
            authorization = request.authorization
            if authorization is None or authorization.type != "bearer" or authorization.token is None:
                return make_response("Please submit a JWT with bearer authorization.", 401)

            access_token = authorization.token

            key = jwks.get_signing_key_from_jwt(access_token)
            payload = jwt.decode(
                access_token,
                key,
                audience=OIDC_CLIENT_ID,
                algorithms=["ES256"],
                options={
                    "verify_jti": False
                }
            )

            g.payload = payload

            headers = {
                "Authorization": f"Bearer {access_token}",
            }

            userinfo_result = requests.get(
                f"https://idm.linux.usu.edu/oauth2/openid/{OIDC_CLIENT_ID}/userinfo",
                headers=headers
            )

            if not userinfo_result.ok:
                return make_response("JWT is expired.", 403)

            userinfo_json = userinfo_result.json()
            auth_level = get_auth_level(userinfo_json["roles"])

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
