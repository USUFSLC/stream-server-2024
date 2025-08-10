from datetime import datetime
from typing import Any, List, Optional
from uuid import UUID
from secrets import token_hex
from sqlalchemy import ForeignKey, String, text
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
        server_default=text("gen_random_uuid()")
    )
    created_at: Mapped[datetime] = mapped_column(server_default=text("now()"))
    starts_at: Mapped[datetime]
    ends_at: Mapped[datetime]
    location: Mapped[Optional[str]] = mapped_column(String(64))
    title: Mapped[str] = mapped_column(String(128))
    description: Mapped[Optional[str]]

    streams: Mapped[List["Stream"]] = relationship(back_populates="event", passive_deletes=True)

    def as_json(self, with_streams=False) -> dict[str, Any]:
        result = {
            "id": str(self.id),
            "created_at": self.created_at.timestamp(),
            "starts_at": self.starts_at.timestamp(),
            "ends_at": self.ends_at.timestamp(),
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

        start_dt = parse_datetime_permissive(data["start"])

        if "end" in data:
            end_dt = parse_datetime_permissive(data["end"])
        else:
            end_dt = start_dt

        return Event(
            starts_at=start_dt,
            ends_at=end_dt,
            location=data.get("location", None),
            title=title,
            description=data.get("description", None),
        )

class Stream(Base):
    __tablename__ = "stream"

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        server_default=text("gen_random_uuid()")
    )
    created_at: Mapped[datetime] = mapped_column(server_default=text("now()"))
    started_at: Mapped[Optional[datetime]]
    ended_at: Mapped[Optional[datetime]]
    processed_at: Mapped[Optional[datetime]]
    title: Mapped[str]
    presenter: Mapped[Optional[UUID]]
    nonmember_presenter: Mapped[Optional[str]] = mapped_column(String(20))
    description: Mapped[Optional[str]]
    token: Mapped[str] = mapped_column(default=lambda: token_hex(16))

    event_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("event.id", ondelete="SET NULL"))
    event: Mapped["Event"] = relationship(back_populates="streams", passive_deletes=True)

    def as_json(self, with_event=False) -> dict[str, Any]:
        result = {
            "id": str(self.id),
            "created_at": self.created_at.timestamp(),
            "started_at": None if self.started_at is None else self.started_at.timestamp(),
            "ended_at": None if self.ended_at is None else self.ended_at.timestamp(),
            "processed_at": None if self.processed_at is None else self.processed_at.timestamp(),
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
            if "started_at" in data:
                result.started_at = parse_datetime_permissive(data["started_at"])
            if "ended_at" in data:
                result.ended_at = parse_datetime_permissive(data["ended_at"])
            if "processed_at" in data:
                result.processed_at = parse_datetime_permissive(data["processed_at"])

        return result
