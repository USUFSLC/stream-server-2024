from os import makedirs, remove
from uuid import UUID, uuid4
import hashlib
from flask import Blueprint, current_app, make_response, request
import icalendar
from sqlalchemy import delete, select
from werkzeug.utils import secure_filename

from fslc_stream.auth import requires_authorization
from fslc_stream.db.context import db
from fslc_stream.db.models import Event, Resource, SerializationError, Stream
from fslc_stream.types import AuthorizationLevel
from fslc_stream.upload_utils import ResourceUploadError, save_resource
from fslc_stream.utils import parse_datetime_permissive


blueprint = Blueprint("event_api", __name__)


@blueprint.post("")
@requires_authorization(AuthorizationLevel.ADMIN)
def new_event():
    data = request.json
    if data is None:
        return make_response("Please pass a JSON object.", 400)

    try:
        event = Event.from_json(data)
    except SerializationError as e:
        resp = make_response(e.msg, 400)
        resp.mimetype = "text/plain"
        return resp;

    db.session.add(event)
    db.session.commit()

    return event.as_json()


@blueprint.get("")
def get_events():
    with_streams = "with-streams" in request.args
    with_resources = "with-resources" in request.args

    format = request.args.get("format", "json")

    if format not in ("json", "ics"):
        return make_response("invalid output format", 400)

    query = select(Event) \
        .order_by(Event.start_time)

    if "from" in request.args:
        from_time = request.args["from"]
        try:
            from_time = float(from_time)
        except ValueError:
            pass
        from_dt = parse_datetime_permissive(from_time)

        query = query.where(Event.start_time >= from_dt)

    if "to" in request.args:
        to_time = request.args["to"]
        try:
            to_time = float(to_time)
        except ValueError:
            pass
        to_dt = parse_datetime_permissive(to_time)

        query = query.where(Event.start_time <= to_dt)

    events = [e for e in db.session.scalars(query)]

    if len(events) == 0:
        return make_response("No events in time frame.", 404)

    if format == "json":
        return [e.as_json(with_streams, with_resources) for e in events]
    elif format == "ics":
        result = icalendar.Calendar()
        result.add("x-wr-calname", "USU FSLC Events")
        for e in events:
            result.add_component(e.as_ics())

        response = make_response(result.to_ical())
        response.headers["content-type"] = "text/calendar"
        return response
    else:
        return make_response("Somehow I didn't realize this was an illegal format before. Go back.", 400)


@blueprint.get("/<uuid:uuid>")
def get_event(uuid: UUID):
    with_streams = "with-streams" in request.args
    with_resources = "with-resources" in request.args

    format = request.args.get("format", "json")

    if format not in ("json", "ics"):
        return make_response("invalid output format", 400)

    query = select(Event).where(Event.id == uuid)
    event = db.session.scalar(query)

    if event is None:
        return make_response("No such event.", 404)

    if format == "json":
        return event.as_json(with_streams, with_resources)
    elif format == "ics":
        result = icalendar.Calendar()
        result.add_component(event.as_ics())

        response = make_response(result.to_ical())
        response.headers["content-type"] = "text/calendar"
        return response
    else:
        return make_response("Somehow I didn't realize this was an illegal format before. Go back.", 400)


@blueprint.delete("/<uuid:uuid>")
@requires_authorization(AuthorizationLevel.ADMIN)
def delete_event(uuid: UUID):
    query = delete(Event).where(Event.id == uuid)
    result = db.session.execute(query)

    if result.rowcount == 0:
        return make_response("No such event.", 404)

    db.session.commit()
    return {"ok": "deleted"}


@blueprint.patch("/<uuid:uuid>")
@requires_authorization(AuthorizationLevel.ADMIN)
def patch_event(uuid: UUID):
    data = request.json
    if not isinstance(data, dict):
        return make_response("need json object to update event", 400)

    query = select(Event).where(Event.id == uuid)
    event: Event | None = db.session.scalar(query)

    if event is None:
        return make_response("no such event", 400)

    if "location" in data:
        event.location = data["location"]
    if "title" in data:
        event.title = data["title"]
    if "description" in data:
        event.description = data["description"]
    if "start_time" in data:
        try:
            event.start_time = parse_datetime_permissive(data["start_time"])
        except ValueError:
            return make_response("invalid start time", 400)
    if "end_time" in data:
        try:
            event.end_time = parse_datetime_permissive(data["end_time"])
        except ValueError:
            return make_response("invalid end time", 400)

    db.session.commit()
    return event.as_json(with_streams=True)


@blueprint.get("/<uuid:uuid>/stream")
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


@blueprint.get("/<uuid:uuid>/resource")
def list_resources(uuid: UUID):
    query = select(Resource).where(Resource.event_id == uuid)
    scalars = db.session.scalars(query)

    return make_response([r.as_json() for r in scalars])


@blueprint.post("/<uuid:eid>/resource")
@requires_authorization(required_level=AuthorizationLevel.ADMIN)
def upload_resource(eid: UUID):
    query = select(Event).where(Event.id == eid)
    if db.session.scalar(query) is None:
        return make_response("No such event.", 400)

    current_app.logger.error(request.files)
    if len(request.files) != 1:
        return make_response("Please upload exactly one file.", 400)

    storage = next(iter(request.files.values()))

    try:
        res = save_resource(storage)
    except ResourceUploadError as e:
        return make_response(e.message, 400)

    res.event_id = eid

    db.session.add(res)
    db.session.commit()

    return make_response(res.as_json())


@blueprint.delete("/<uuid:eid>/resource/<uuid:rid>")
@requires_authorization(required_level=AuthorizationLevel.ADMIN)
def delete_resource(eid: UUID, rid: UUID):
    query = select(Resource).where(Resource.id == rid)
    res = db.session.scalar(query)
    if res is None:
        return make_response("No such resource.", 400)

    if res.event_id != eid:
        return make_response("Event is incorrect.", 400)

    dir = f"/var/stream/resources/{rid}"
    path = f"{dir}/{res.filename}"

    remove(path)
    remove(dir)

    db.session.delete(res)
    db.session.commit()

    return {"ok": "deleted"}
