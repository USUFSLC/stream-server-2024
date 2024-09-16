import sqlite3
import time

from flask import Blueprint, abort, current_app, request, make_response, redirect, g
import requests

from fslc_stream.types import StreamInfo, StreamServerFlask
from fslc_stream.utils import with_database

current_app: StreamServerFlask

blueprint = Blueprint("rtmp_callbacks", __name__)

# these routes should only be available if you're talking directly to the server
# that should mean that only other programs running on the same network as this docker container can access it
# if you're not, i don't want you to even know they exist
# this function returns the default 404 message for everything here, even if the route isn't declared
@blueprint.before_app_request
def no_proxies():
    if "X-Forwarded-For" in request.headers:
        return abort(404)

@blueprint.route("/start", methods=["POST"])
@with_database
def rtmp_start():
    key = request.form.get("name")
    if key is None:
        return make_response("You shouldn't be making requests here as a user.", 400)

    db: sqlite3.Connection = g.db
    cursor = db.execute("SELECT * FROM streams WHERE key = ? LIMIT 1", (key,))
    info = StreamInfo(*cursor.fetchone()[0])

    info.started = int(time.time())
    db.execute("UPDATE streams SET started = ? WHERE key = ?", (info.started, key))
    db.commit()

    if info is None:
        return make_response("No such key.", 400)

    return make_response("Go ahead!")
