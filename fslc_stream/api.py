from dataclasses import astuple
import time
import secrets
from flask import Blueprint, current_app, request, make_response, jsonify, abort, g
from fslc_stream.auth import requires_authorization
from fslc_stream.types import AuthorizationLevel, StreamInfo, StreamServerFlask
from fslc_stream.utils import with_database

blueprint = Blueprint("stream_api", __name__)

@blueprint.post("/new")
@requires_authorization(AuthorizationLevel.STREAMER)
@with_database
def new_stream():
    data = request.json
    if data is None:
        return abort(400)

    guild: dict = g.guild_member

    key = f"fslc_{guild['user']['id']}_{secrets.token_hex(24)}"
    new_stream = StreamInfo(
        key,
        int(time.time()),
        None,
        None,
        data["name"],
        data["presenter"],
        data["description"]
    )
    g.db.execute("INSERT INTO streams VALUES(?, ?, ?, ?, ?, ?, ?)", astuple(new_stream))
    g.db.commit()
    return jsonify({ "key": key })
