import logging
from os import environ
from werkzeug.middleware.proxy_fix import ProxyFix

from fslc_stream.db.context import db
from fslc_stream.auth import teardown_payload
from fslc_stream.types import StreamServerFlask
from fslc_stream.api import blueprint as api_blueprint

app = StreamServerFlask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = environ["SQLALCHEMY_DATABASE_URI"]

db.init_app(app)

if __name__ != '__main__':
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)

app.wsgi_app = ProxyFix(
    app.wsgi_app, x_for=1, x_proto=1, x_host=1
)

app.register_blueprint(api_blueprint, url_prefix="/api")

app.teardown_appcontext(teardown_payload)
