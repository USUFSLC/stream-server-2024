import sqlite3
import time

from flask import Blueprint, abort, current_app, request, make_response, redirect, g
import requests

from fslc_stream.types import StreamInfo, StreamServerFlask
from fslc_stream.utils import with_database

current_app: StreamServerFlask

blueprint = Blueprint("rtmp_callbacks", __name__)

@blueprint.before_request
def needs_valid_name():
    if request.method != "POST":
        return

    g.stream_key = key = request.form.get("name")
    if key is None:
        return make_response("You shouldn't be making requests here as a user.", 400)

@blueprint.teardown_request
def delete_key(exception):
    if "key" in g:
        g.pop("key")

@blueprint.post("/start")
@with_database
def rtmp_start():
    key = g.stream_key

    db: sqlite3.Connection = g.db
    cursor = db.execute("SELECT * FROM streams WHERE key = ? LIMIT 1", (key,))
    info = StreamInfo(*cursor.fetchone()[0])

    info.started = int(time.time())
    cursor.execute("UPDATE streams SET started = ? WHERE key = ?", (info.started, key))

    cursor.execute("SELECT * FROM current_stream")
    if cursor.fetchone() is None:
        cursor.execute("INSERT INTO current_stream VALUES(?)", (key,))
    else:
        return make_response("A stream is ongoing.", 409)

    if info.started is not None or info.duration is not None:
        return make_response("That stream has already started.", 409)

    db.commit()

    if info is None:
        return make_response("No such key.", 400)

    return make_response("Go ahead!")

@blueprint.post("/update")
@with_database
def rtmp_update():
    db: sqlite3.Connection = g.db

    cursor = db.execute("SELECT * FROM current_stream")
    data = cursor.fetchone()
    if data is None:
        return make_response("There is no stream ongoing", 400)

    if data[0][0] == g.stream_key:
        return make_response("Keep going!", 200)
    else:
        return make_response("Wrong stream, bucko!", 409)
