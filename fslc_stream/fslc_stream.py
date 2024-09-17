import typing
import logging
from time import time
import json
import secrets
from urllib.parse import urlparse
from os import environ
from flask import Flask, current_app, render_template, request, make_response, jsonify, redirect
from werkzeug.middleware.proxy_fix import ProxyFix
import requests

from fslc_stream.types import DiscordAuthError, StreamServerFlask, AuthorizationLevel

from fslc_stream.auth import blueprint as auth_blueprint, requires_authorization
from fslc_stream.rtmp_callbacks import blueprint as rtmp_blueprint
from fslc_stream.api import blueprint as api_blueprint

app = StreamServerFlask(__name__, template_folder="./templates")

if __name__ != '__main__':
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)

app.wsgi_app = ProxyFix(
    app.wsgi_app, x_for=1, x_proto=1, x_host=1
)

app.register_blueprint(auth_blueprint, url_prefix="/login")
app.register_blueprint(rtmp_blueprint, url_prefix="/rtmp")
app.register_blueprint(api_blueprint, url_prefix="/api")

@app.route("/")
def root():
    return redirect("/new")

@app.route("/new/")
@requires_authorization(AuthorizationLevel.STREAMER)
def new_stream():
    return render_template("new-stream.html")

@app.route("/watch/")
@requires_authorization(AuthorizationLevel.STREAMER)
def watch_stream():
    return render_template("watch-stream.html")
