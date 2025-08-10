from flask import Blueprint

#from fslc_stream.rtmp_callbacks import blueprint as rtmp_blueprint
from fslc_stream.stream import blueprint as stream_blueprint
from fslc_stream.event import blueprint as event_blueprint


blueprint = Blueprint("apis", __name__)

#blueprint.register_blueprint(rtmp_blueprint, url_prefix="/rtmp")
blueprint.register_blueprint(stream_blueprint, url_prefix="/stream")
blueprint.register_blueprint(event_blueprint, url_prefix="/event")
