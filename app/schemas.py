from datetime import UTC, datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, EmailStr, Field, computed_field

from app.models import Priority, Status
from app.sla import is_overdue

T = TypeVar("T")


class TicketCreate(BaseModel):
    title: str = Field(min_length=3, max_length=200, examples=["Outlook keeps asking for password"])
    description: str = Field(default="", max_length=5000)
    requester_email: EmailStr
    category: str = Field(default="general", max_length=50, examples=["email"])
    priority: Priority = Priority.medium


class TicketUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
    category: str | None = Field(default=None, max_length=50)
    priority: Priority | None = None
    status: Status | None = None
    assignee: str | None = Field(default=None, max_length=100)


class TicketRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str
    requester_email: str
    category: str
    priority: Priority
    status: Status
    assignee: str | None
    created_at: datetime
    updated_at: datetime
    due_at: datetime
    resolved_at: datetime | None

    @computed_field
    @property
    def overdue(self) -> bool:
        return is_overdue(self.status, self.due_at, datetime.now(UTC))


class CommentCreate(BaseModel):
    author: str = Field(min_length=1, max_length=100)
    body: str = Field(min_length=1, max_length=5000)
    internal: bool = Field(default=False, description="Hidden from the requester")


class CommentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ticket_id: int
    author: str
    body: str
    internal: bool
    created_at: datetime


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    limit: int
    offset: int


class Stats(BaseModel):
    total: int
    by_status: dict[str, int]
    by_priority: dict[str, int]
    overdue: int
    avg_resolution_hours: float | None
