from functools import wraps
import typing
import json
from flask import Blueprint, current_app, g, request, make_response, redirect, url_for
from os import environ
import requests

from fslc_stream.types import AuthorizationLevel, DiscordAuthError

blueprint = Blueprint('discord_oauth', __name__)

GUILD_ID = environ["DISCORD_GUILD_ID"]

STREAMING_ROLES = environ["DISCORD_STREAMING_ROLES"].split(",")
ADMIN_ROLES = environ["DISCORD_ADMIN_ROLES"].split(",")

def make_access_token_response(discord_response: requests.Response):
    token_json = json.loads(discord_response.text)

    token = token_json.get("access_token")

    if token is None:
        raise DiscordAuthError("Could not get access token", token_json)

    resp = redirect(request.host_url)
    resp.set_cookie("access_token", token)
    resp.set_cookie("refresh_token", token)

    return resp

@blueprint.route("/")
def login():
    refresh_token = request.cookies.get("refresh_token")
    if refresh_token is not None:
        token_request_result = requests.post(
            "https://discord.com/api/oauth2/token",
            data={
                "client_id": environ["DISCORD_CLIENT_ID"],
                "client_secret": environ["DISCORD_CLIENT_SECRET"],
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
            }
        )

        try:
            return make_access_token_response(token_request_result)
        except DiscordAuthError as e:
            pass

    return redirect(
        "https://discord.com/api/oauth2/authorize"
        f"?client_id={environ.get('DISCORD_CLIENT_ID')}"
        f"&redirect_uri={url_for('discord_oauth.callback', **request.args)}"
        f"&response_type=code"
        f"&scope=identify guilds guilds.members.read"
    )

@blueprint.route("/callback/")
def callback():
    code: str | None = request.args.get("code")
    if code is None:
        return make_response("No authorization code supplied.", 500)

    token_request_result = requests.post(
        "https://discord.com/api/oauth2/token",
        data={
            "client_id": environ["DISCORD_CLIENT_ID"],
            "client_secret": environ["DISCORD_CLIENT_SECRET"],
            "grant_type": "authorization_code",
            "redirect_uri": f"{request.host_url}login/callback",
            "scope": "identify guilds guilds.members.read",
            "code": code,
        }
    )

    try:
        return make_access_token_response(token_request_result)
    except DiscordAuthError as e:
        return make_response("Error: ", e.error_str + ". Discord says: " + str(e.discord_response))

def requires_authorization(level: AuthorizationLevel = AuthorizationLevel.USER):
    def decorator(f: typing.Callable):
        @wraps(f)
        def wrapped(*args, **kwargs):
            access_token = request.cookies.get("access_token")
            if access_token is None:
                return redirect(url_for("discord_oauth.login", next=request.url))

            headers = {
                "Authorization": f"Bearer {access_token}",
            }

            guild_result = requests.get(
                f"https://discord.com/api/users/@me/guilds/{GUILD_ID}/member",
                headers=headers
            )
            if not guild_result.ok:
                return make_response("Please join the USU FSLC server to proceed.", 403)

            guild = json.loads(guild_result.text)

            request.guild_member = guild

            if level >= AuthorizationLevel.STREAMER:
                roles = STREAMING_ROLES if level == AuthorizationLevel.STREAMER else ADMIN_ROLES

                for role in guild["roles"]:
                    if role in roles:
                        break
                else:
                    return make_response("You do not have sufficient roles.", 403)

            return f(*args, **kwargs)

        return wrapped

    return decorator
