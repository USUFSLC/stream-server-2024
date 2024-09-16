from dataclasses import astuple
import time
import secrets
from flask import Blueprint, current_app, request, make_response, jsonify, abort
from fslc_stream.auth import requires_authorization
from fslc_stream.types import AuthorizationLevel, StreamInfo, StreamServerFlask

current_app: StreamServerFlask

blueprint = Blueprint("stream_api", __name__)

@blueprint.post("/new")
@requires_authorization(AuthorizationLevel.STREAMER)
def new_stream():
    data = request.json
    if data is None:
        return abort(400)

    guild: dict = request.guild_member

    key = f"fslc_{guild['user']['id']}_{secrets.token_hex(24)}"
    new_stream = StreamInfo(
        key,
        int(time.time()),
        0,
        0,
        data["name"],
        data["presenter"],
        data["description"]
    )
    current_app.sql_handle.execute("INSERT INTO streams VALUES(?, ?, ?, ?, ?, ?, ?)", astuple(new_stream))
    return jsonify({ "key": key })
