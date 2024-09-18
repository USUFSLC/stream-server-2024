import sqlite3
import time
import threading

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
    info_tup = cursor.fetchone()

    if info_tup is None:
        return make_response("Non-existing stream.", 409)

    info = StreamInfo(*info_tup)

    current_app.logger.info("Stream Info Class: %s", info)

    cursor.execute("SELECT * FROM current_stream")
    current_stream_tup = cursor.fetchone()

    if current_stream_tup is None:
        cursor.execute("INSERT INTO current_stream VALUES(?)", (key,))
    else:
        return make_response("A stream is ongoing.", 409)

    if info.started is not None or info.ended is not None or info.processed:
        return make_response("That stream has already started.", 409)

    info.started = int(time.time())
    cursor.execute("UPDATE streams SET started = ? WHERE key = ?", (info.started, key))

    db.commit()

    return make_response("Go ahead!")

@blueprint.post("/update")
@with_database
def rtmp_update():
    db: sqlite3.Connection = g.db

    cursor = db.execute("SELECT * FROM current_stream")
    data = cursor.fetchone()
    if data is None:
        return make_response("There is no stream ongoing", 400)

    if data[0] == g.stream_key:
        return make_response("Keep going!", 200)
    else:
        return make_response("Wrong stream, bucko!", 409)

stream_end_lock = threading.Lock()

@blueprint.post("/end")
@with_database
def rtmp_end():
    key = g.stream_key
    db: sqlite3.Connection = g.db

    cursor = db.execute("SELECT * FROM streams WHERE key = ? LIMIT 1", (key,))
    info_tup = cursor.fetchone()

    if info_tup is None:
        return make_response("Non-existing stream.", 409)

    info = StreamInfo(*info_tup)

    current_app.logger.info("Stream Info Class: %s", info)

    cursor.execute("SELECT * FROM current_stream")
    current_stream_tup = cursor.fetchone()

    if current_stream_tup is not None:
        if current_stream_tup[0] != key:
            return make_response("Ending a stream that is not ongoing.", 409)
        cursor.execute("DELETE FROM current_stream")
    else:
        return make_response("A stream is ongoing.", 409)

    if info.started is None or info.ended is not None:
        return make_response("Stream has not started or has already ended.", 409)

    with stream_end_lock:
        cursor.execute("UPDATE streams SET ended = ? WHERE key = ?", (info.ended, key))
        db.commit()

    if info is None:
        return make_response("No such key.", 400)

    return make_response("It's so over...")

@blueprint.post("/done")
@with_database
def rtmp_done():
    key = g.stream_key
    db: sqlite3.Connection = g.db

    cursor = db.execute("SELECT * FROM streams WHERE key = ? LIMIT 1", (key,))
    info_tup = cursor.fetchone()

    if info_tup is None:
        return make_response("Non-existing stream.", 409)

    info = StreamInfo(*info_tup)

    current_app.logger.info("Stream Info Class: %s", info)

    if info.started is None or info.processed:
        return make_response("Stream has not started or has already been processed.", 409)

    with stream_end_lock:
        cursor.execute("UPDATE streams SET processed = ? WHERE key = ?", (1, key))
        db.commit()

    return make_response("We're so back!")
