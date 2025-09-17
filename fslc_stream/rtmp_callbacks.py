from datetime import datetime
import threading

from flask import Blueprint, request, make_response, g
from sqlalchemy import and_, select

from fslc_stream.db.models import Stream
from fslc_stream.db.context import db

blueprint = Blueprint("rtmp_callbacks", __name__)

def get_stream_by_key(key: str) -> Stream | None:
    print(key)
    stream_id, token = key.split('.')

    query = select(Stream).where(and_(
        Stream.id == stream_id,
        Stream.token == token,
    ))
    stream = db.session.scalar(query)

    return stream


@blueprint.before_request
def needs_valid_name():
    if request.method != "POST":
        return

    g.stream_key = key = request.form.get("name")
    if key is None:
        return make_response("You shouldn't be making requests here as a user.", 400)


@blueprint.teardown_request
def delete_key(_):
    if "key" in g:
        g.pop("key")


@blueprint.post("/start")
def rtmp_start():
    stream = get_stream_by_key(g.stream_key)

    if stream is None:
        return make_response("Invalid key.", 400)

    if stream.start_time is not None:
        return make_response("Stream already started.", 409)

    stream.start_time = datetime.now()

    db.session.add(stream)
    db.session.commit()

    return make_response("Go ahead!")

@blueprint.post("/update")
def rtmp_update():
    stream = get_stream_by_key(g.stream_key)

    if stream is None:
        return make_response("Invalid key.", 400)

    if stream.start_time is None:
        return make_response("Stream has not started.", 409)

    if stream.end_time is None:
        return make_response("Keep going!", 200)
    return make_response("Stream ended.", 409)

stream_end_lock = threading.Lock()

@blueprint.post("/end")
def rtmp_end():
    stream = get_stream_by_key(g.stream_key)

    if stream is None:
        return make_response("Invalid key.", 400)

    if stream.end_time is not None:
        return make_response("Stream already ended", 409)

    stream.end_time = datetime.now()
    db.session.add(stream)

    with stream_end_lock:
        db.session.commit()

    return make_response("It's so over...")

@blueprint.post("/done")
def rtmp_done():
    stream = get_stream_by_key(g.stream_key)

    if stream is None:
        return make_response("Invalid key.", 400)

    if stream.process_time is not None:
        return make_response("Stream already processed", 409)

    stream.process_time = datetime.now()
    db.session.add(stream)

    with stream_end_lock:
        db.session.commit()

    return make_response("We're so back!")
