from uuid import UUID
from flask import Blueprint, make_response, request
from sqlalchemy import select

from fslc_stream.auth import requires_authorization
from fslc_stream.db.context import db
from fslc_stream.db.models import Event, SerializationError, Stream
from fslc_stream.types import AuthorizationLevel
from fslc_stream.utils import parse_datetime_permissive


blueprint = Blueprint("stream_api", __name__)


@blueprint.post("/")
@requires_authorization(AuthorizationLevel.STREAMER)
def new_event():
    data = request.json
    if data is None:
        return make_response("Please pass a JSON object.", 400)

    try:
        event = Event.from_json(data)
    except SerializationError as e:
        return make_response(e.msg, 400)

    db.session.add(event)
    db.session.commit()

    return event.as_json()


@blueprint.get("/")
@requires_authorization(AuthorizationLevel.USER)
def get_events():
    query = select(Event) \
        .order_by(Event.starts_at)

    if "from" in request.args:
        from_time = request.args["from"]
        try:
            from_time = float(from_time)
        except ValueError:
            pass
        from_dt = parse_datetime_permissive(from_time)

        query = query.where(Event.starts_at >= from_dt)

    if "to" in request.args:
        to_time = request.args["to"]
        try:
            to_time = float(to_time)
        except ValueError:
            pass
        to_dt = parse_datetime_permissive(to_time)

        query = query.where(Event.ends_at <= to_dt)

    events = [e.as_json() for e in db.session.scalars(query)]

    if len(events) == 0:
        return make_response("No events in time frame.", 404)
    return events


@blueprint.get("/<uuid:uuid>/")
def get_event(uuid: UUID):
    with_streams = "with-streams" in request.args
    query = select(Event).where(Event.id == uuid)
    event = db.session.scalars(query).first()

    if event is None:
        return make_response("No such event.", 404)
    return event.as_json(with_streams)


@blueprint.get("/<uuid:uuid>/stream/")
def get_streams(uuid: UUID):
    query = select(Stream).where(Stream.event_id == uuid)
    stream = [s.as_json() for s in db.session.scalars(query)]
    if len(stream) == 0:
        return make_response("Event does not exist or has no streams.", 404)
    return stream


@blueprint.post("/<uuid:uuid>/stream")
@requires_authorization(AuthorizationLevel.STREAMER)
def add_stream(uuid: UUID):
    allow_callback_properties = "allow-callback-properties" in request.args
    data = request.json
    if data is None:
        return make_response("Please pass a JSON object.", 400)

    try:
        stream = Stream.from_json(
            data | { "event_id": uuid },
            allow_callback_properties
        )
    except SerializationError as e:
        return make_response(e.msg, 400)

    db.session.add(stream)
    db.session.commit()

    return make_response(stream.as_json())
