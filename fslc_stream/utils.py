import sqlite3
from functools import wraps
import typing
import os

from flask import g

DATABASE = os.environ.get("STREAM_SERVER_DATABASE", "./export/db.sqlite")

def with_database(f: typing.Callable):
    @wraps(f)
    def wrapped(*args, **kwargs):
        if "db" not in g:
            g.db = sqlite3.connect(DATABASE)

        result = f(*args, **kwargs)

        db = g.pop("db", None)
        if db is not None:
            db.close()

        return result

    return wrapped

