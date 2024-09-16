import typing
from time import time
import json
import secrets
from urllib.parse import urlparse
from os import environ
from flask import Flask, render_template, request, make_response, jsonify, redirect
import requests

from fslc_stream.types import DiscordAuthError, StreamServerFlask, AuthorizationLevel

from fslc_stream.auth import blueprint as auth_blueprint, requires_authorization
from fslc_stream.rtmp_callbacks import blueprint as rtmp_blueprint
from fslc_stream.api import blueprint as api_blueprint

app = StreamServerFlask(__name__, template_folder="./templates")
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
