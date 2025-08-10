from uuid import UUID
from flask import Blueprint, g, request, make_response
from sqlalchemy import and_, select
from fslc_stream.auth import requires_authorization
from fslc_stream.db.context import db
from fslc_stream.db.models import SerializationError, Stream
from fslc_stream.types import AuthorizationLevel


blueprint = Blueprint("stream_api", __name__)


# TODO: turn this or /api/event/uuid/stream into a redirect to the other
@blueprint.post("/")
@requires_authorization(AuthorizationLevel.STREAMER)
def new_stream():
    allow_callback_properties = "allow-callback-properties" in request.args
    data = request.json
    if data is None:
        return make_response("Please pass a JSON object.", 400)

    try:
        stream = Stream.from_json(
            data,
            allow_callback_properties
        )
    except SerializationError as e:
        return make_response(e.msg, 400)

    db.session.add(stream)
    db.session.commit()

    return make_response(stream.as_json())


@blueprint.get("/live/")
def current_streams():
    query = select(Stream).where(and_(Stream.started_at != None, Stream.ended_at == None))

    return [s.as_json() for s in db.session.scalars(query)]

@blueprint.get("/<uuid:uuid>/")
def get_stream(uuid: UUID):
    query = select(Stream).where(Stream.id == uuid)
    stream = db.session.scalar(query)

    if stream is None:
        return make_response("No such stream.", 404)
    return stream.as_json()

@blueprint.get("/<uuid:uuid>/token/")
@requires_authorization(AuthorizationLevel.STREAMER)
def get_stream_token(uuid: UUID):
    auth_level: AuthorizationLevel = g.auth_level
    user_id: UUID = UUID(g.payload["sub"])

    query = select(Stream).where(Stream.id == uuid)
    stream = db.session.scalar(query)

    if stream is None:
        return make_response("No such stream.", 404)

    if auth_level == AuthorizationLevel.STREAMER and stream.presenter != user_id:
        return make_response("You are not a presenter for this stream.", 403)

    if stream.started_at is not None:
        return make_response("This stream has already been started.", 409)

    if stream.token is None:
        return make_response("This stream has no token.", 404)

    return {"token": str(uuid) + "." + stream.token}
