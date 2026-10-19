import enum
from datetime import UTC, datetime

from sqlalchemy import DateTime, String, Text, TypeDecorator
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class UTCDateTime(TypeDecorator):
    """Stores datetimes in UTC and always returns them timezone-aware."""

    impl = DateTime(timezone=True)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None and value.tzinfo is None:
            value = value.replace(tzinfo=UTC)
        return value

    def process_result_value(self, value, dialect):
        if value is not None and value.tzinfo is None:
            value = value.replace(tzinfo=UTC)
        return value


def utcnow() -> datetime:
    return datetime.now(UTC)


class Priority(enum.StrEnum):
    critical = "critical"
    high = "high"
    medium = "medium"
    low = "low"


class Status(enum.StrEnum):
    open = "open"
    in_progress = "in_progress"
    resolved = "resolved"
    closed = "closed"


class Ticket(Base):
    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    requester_email: Mapped[str] = mapped_column(String(254), index=True)
    category: Mapped[str] = mapped_column(String(50), default="general")
    priority: Mapped[str] = mapped_column(String(20), default=Priority.medium, index=True)
    status: Mapped[str] = mapped_column(String(20), default=Status.open, index=True)
    assignee: Mapped[str | None] = mapped_column(String(100), default=None)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow, onupdate=utcnow)
    due_at: Mapped[datetime] = mapped_column(UTCDateTime, index=True)
    resolved_at: Mapped[datetime | None] = mapped_column(UTCDateTime, default=None)
