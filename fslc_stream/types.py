from enum import IntEnum
from flask import Flask
from fslc_stream.db.context import db

class StreamServerFlask(Flask):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def init_app(self, app):
        with app.app_context():
            db.create_all()

class AuthorizationLevel(IntEnum):
    USER = 0
    STREAMER = 50
    ADMIN = 100
