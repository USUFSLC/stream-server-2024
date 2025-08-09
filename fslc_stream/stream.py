from dataclasses import astuple
import dataclasses
import sqlite3
import time
import secrets
from flask import Blueprint, request, make_response, jsonify, abort, g
from sqlalchemy import select
from fslc_stream.auth import requires_authorization
from fslc_stream.types import AuthorizationLevel, StreamInfo
from fslc_stream.db.context import db
from fslc_stream.db.models import Event, Stream

blueprint = Blueprint("stream_api", __name__)

@blueprint.post("/")
@requires_authorization(AuthorizationLevel.STREAMER)
def new_stream():
    data = request.json
    if data is None:
        return make_response("Please pass a JSON object.", 400)

    key = f"fslc_{guild['user']['id']}_{secrets.token_hex(24)}"
    new_stream = StreamInfo(
        key,
        int(time.time()),
        None,
        None,
        0,
        data["name"],
        data["presenter"],
        data["description"]
    )
    g.db.execute("INSERT INTO streams VALUES(?, ?, ?, ?, ?, ?, ?, ?)", astuple(new_stream))
    g.db.commit()
    return jsonify({ "key": key })

@blueprint.route("/current-stream")
def current_stream():
    db: sqlite3.Connection = g.db

    cursor = db.execute("SELECT * from current_stream LIMIT 1")
    key = cursor.fetchone()
    if key is None:
        return jsonify({"error": "no stream ongoing"}), 404

    key = key[0];

    cursor.execute("SELECT * from streams where key = ? LIMIT 1", (key,))
    info_tup = cursor.fetchone()

    if info_tup is None:
        return make_response("Non-existing stream.", 409)

    info = StreamInfo(*info_tup)

    return jsonify(dataclasses.asdict(info))
