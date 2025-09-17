from datetime import datetime
from typing import Any, List, Optional
from uuid import UUID
from secrets import token_hex
import sqlalchemy as sa
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from fslc_stream.utils import parse_datetime_permissive

class SerializationError(Exception):
    msg: str

    def __init__(self, msg: str):
        self.msg = msg

class Base(DeclarativeBase):
    pass

class Event(Base):
    __tablename__ = "event"

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        server_default=sa.text("gen_random_uuid()")
    )
    create_time: Mapped[datetime] = mapped_column(server_default=sa.text("now()"))
    start_time: Mapped[datetime]
    end_time: Mapped[datetime]
    location: Mapped[Optional[str]] = mapped_column(sa.String(64))
    title: Mapped[str] = mapped_column(sa.String(128))
    description: Mapped[Optional[str]]

    streams: Mapped[List["Stream"]] = relationship(back_populates="event", passive_deletes=True)

    def as_json(self, with_streams=False) -> dict[str, Any]:
        result = {
            "id": str(self.id),
            "create_time": self.create_time.timestamp(),
            "start_time": self.start_time.timestamp(),
            "end_time": self.end_time.timestamp(),
            "location": self.location,
            "title": self.title,
            "description": self.description,
        }

        if with_streams:
            result["streams"] = [s.as_json() for s in self.streams]

        return result

    @staticmethod
    def from_json(data: dict[str, Any]) -> "Event":
        if "title" not in data:
            raise SerializationError("No title specified.")

        title = data["title"]

        if "start" not in data:
            raise SerializationError("No start time specified.")

        try:
            start_dt = parse_datetime_permissive(data["start"])
        except ValueError:
            raise SerializationError("Failed to parse start time")

        if "end" in data:
            try:
                end_dt = parse_datetime_permissive(data["end"])
            except ValueError:
                raise SerializationError("Failed to parse start time")
        else:
            end_dt = start_dt

        return Event(
            start_time=start_dt,
            end_time=end_dt,
            location=data.get("location", None),
            title=title,
            description=data.get("description", None),
        )

class Stream(Base):
    __tablename__ = "stream"

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        server_default=sa.text("gen_random_uuid()")
    )
    create_time: Mapped[datetime] = mapped_column(server_default=sa.text("now()"))
    start_time: Mapped[Optional[datetime]]
    end_time: Mapped[Optional[datetime]]
    process_time: Mapped[Optional[datetime]]
    title: Mapped[str] = mapped_column(sa.String(128))
    presenter: Mapped[Optional[UUID]]
    nonmember_presenter: Mapped[Optional[str]] = mapped_column(sa.String(20))
    description: Mapped[Optional[str]]
    token: Mapped[str] = mapped_column(sa.String(32), default=lambda: token_hex(16))

    event_id: Mapped[Optional[UUID]] = mapped_column(sa.ForeignKey("event.id", ondelete="SET NULL"))
    event: Mapped["Event"] = relationship(back_populates="streams", passive_deletes=True)

    def as_json(self, with_event=False) -> dict[str, Any]:
        result = {
            "id": str(self.id),
            "create_time": self.create_time.timestamp(),
            "start_time": None if self.start_time is None else self.start_time.timestamp(),
            "end_time": None if self.end_time is None else self.end_time.timestamp(),
            "process_time": None if self.process_time is None else self.process_time.timestamp(),
            "title": self.title,
            "presenter": self.presenter if self.presenter is not None else self.nonmember_presenter,
            "description": self.description,
        }

        if with_event:
            result["event"] = self.event.as_json()
        else:
            result["event_id"] = self.event_id

        return result

    @staticmethod
    def from_json(data: dict[str, Any], allow_callback_properties=False) -> "Stream":
        """Creates a new stream from JSON input.

        This is meant to be used by routes to produce new streams which will be
        started, ended, and processed by callbacks. As such, it prevents setting
        these properties by default. If you *really* want this behavior, set the
        relevant argument.
        """
        if "title" not in data:
            raise SerializationError("No title specified.")

        title = data["title"]

        match "presenter" in data, "nonmember_presenter" in data:
            case True, True:
                raise SerializationError("Cannot have a presenter and nonmember presenter.")
            case True, False:
                presenter = {"presenter": UUID(data["presenter"])}
            case False, True:
                presenter = {"nonmember_presenter": data["nonmember_presenter"]}
            case False, False:
                raise SerializationError("Need either a presenter or nonmember presenter.")

        result = Stream(
            title=title,
            description=data.get("description", None),
            event_id=data.get("event_id", None),
            **presenter
        )

        if allow_callback_properties:
            if "start_time" in data:
                result.start_time = parse_datetime_permissive(data["start_time"])
            if "end_time" in data:
                result.end_time = parse_datetime_permissive(data["end_time"])
            if "process_time" in data:
                result.process_time = parse_datetime_permissive(data["process_time"])

        return result
