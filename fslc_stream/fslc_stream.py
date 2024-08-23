import typing
import json
import secrets
from urllib.parse import urlparse
from os import environ
from flask import Flask, request, make_response, redirect
import requests

GUILD_ID = environ["DISCORD_GUILD_ID"]
STREAMING_ROLES = environ["DISCORD_STREAMING_ROLES"].split(",")

class DiscordAuthError(Exception):
    error_str: str
    discord_response: dict[str, typing.Any]
    def __init__(self, error_str: str, discord_response: dict[str, typing.Any]):
        self.error_str = error_str
        self.discord_response = discord_response

app = Flask(__name__)

def make_access_token_response(discord_response: requests.Response):
    token_json = json.loads(discord_response.text)

    token = token_json.get("access_token")

    if token is None:
        raise DiscordAuthError("Could not get access token", token_json)

    resp = redirect(request.host_url)
    resp.set_cookie("access_token", token)
    resp.set_cookie("refresh_token", token)

    return resp

@app.route("/")
def root():
    return redirect("/new")

@app.route("/login/")
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
        f"&redirect_uri={request.host_url}login/callback"
        f"&response_type=code"
        f"&scope=identify guilds guilds.members.read"
    )

@app.route("/login/callback/")
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

@app.route("/new/")
def new_stream():
    access_token = request.cookies.get("access_token")
    if access_token is None:
        return redirect("/login")

    headers = {
        "Authorization": f"Bearer {access_token}",
    }

    guild_result = requests.get(
        f"https://discord.com/api/users/@me/guilds/{GUILD_ID}/member",
        headers=headers
    )
    guild = json.loads(guild_result.text)

    # return make_response(guild_result.text, 200, { "Content-Type": "application/json" })

    for role in guild["roles"]:
        if role in STREAMING_ROLES:
            key = f"fslc_{guild['user']['id']}_{secrets.token_hex(24)}"
            return make_response(f"Yay, you're authorized. Here's your stream key:<br><br>{key}")

    return make_response("You are not authorized! Go back!", 403)

if __name__ == "__main__":
    app.run("0.0.0.0", 8080)
