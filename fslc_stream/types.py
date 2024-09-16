from dataclasses import dataclass
from enum import IntEnum
import os
import typing
from sqlite3 import Connection
import sqlite3
from flask import Flask

class DiscordAuthError(Exception):
    error_str: str
    discord_response: dict[str, typing.Any]
    def __init__(self, error_str: str, discord_response: dict[str, typing.Any]):
        self.error_str = error_str
        self.discord_response = discord_response

@dataclass
class StreamInfo:
    """
    Object representing a stream
    """

    key: str
    """
    The stream key itself, of the form ``fslc_[discord_user_id]_[random_bytes]``
    """
    created: int
    """
    The UNIX timestamp, in seconds, at which the key was created
    """
    started: int
    """
    The UNIX timestamp, in seconds, at which the stream was started
    """
    duration: int
    """
    The length of the stream in seconds
    """
    name: str
    """
    The human-readable name/title of the stream
    """
    presenter: str
    """
    The name of the presenter
    """
    description: str
    """
    A blurb about the contents of the meeting
    """

class StreamServerFlask(Flask):
    streams: list[StreamInfo]
    sql_handle: Connection

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # update database to most recent version
        # create it first if necessary
        dbname = os.environ.get("STREAM_SERVER_DATABASE", "./export/db.sqlite")
        os.makedirs(os.path.dirname(dbname), exist_ok=True)
        initdb = not os.path.exists(dbname)
        # theoretically this makes the connection threadsafe with a single connection object
        sqlite3.threadsafety = 3
        self.sql_handle = sqlite3.connect(dbname, check_same_thread=False)

        if initdb:
            with open("schema.sql") as f:
                self.sql_handle.executescript(f.read());

        cursor = self.sql_handle.execute("SELECT * from streams ORDER BY started")
        self.streams = [StreamInfo(*el) for el in cursor.fetchall()];

class AuthorizationLevel(IntEnum):
    USER = 0
    STREAMER = 50
    ADMIN = 100
