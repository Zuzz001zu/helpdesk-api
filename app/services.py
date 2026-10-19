from datetime import UTC, datetime

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models import Priority, Status, Ticket
from app.schemas import TicketCreate, TicketUpdate
from app.sla import ACTIVE_STATUSES, can_transition, due_date


class TransitionError(ValueError):
    pass


def create_ticket(db: Session, data: TicketCreate) -> Ticket:
    now = datetime.now(UTC)
    ticket = Ticket(
        **data.model_dump(),
        created_at=now,
        updated_at=now,
        due_at=due_date(data.priority, now),
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return ticket


def list_tickets(
    db: Session,
    *,
    status: Status | None = None,
    priority: Priority | None = None,
    assignee: str | None = None,
    q: str | None = None,
    overdue: bool | None = None,
    limit: int = 20,
    offset: int = 0,
) -> tuple[list[Ticket], int]:
    query = select(Ticket)
    if status:
        query = query.where(Ticket.status == status)
    if priority:
        query = query.where(Ticket.priority == priority)
    if assignee:
        query = query.where(Ticket.assignee == assignee)
    if q:
        pattern = f"%{q}%"
        query = query.where(or_(Ticket.title.ilike(pattern), Ticket.description.ilike(pattern)))
    if overdue is not None:
        late = Ticket.status.in_(ACTIVE_STATUSES) & (Ticket.due_at < datetime.now(UTC))
        query = query.where(late if overdue else ~late)

    total = db.scalar(select(func.count()).select_from(query.subquery()))
    rows = db.scalars(query.order_by(Ticket.due_at, Ticket.id).limit(limit).offset(offset)).all()
    return list(rows), total


def update_ticket(db: Session, ticket: Ticket, data: TicketUpdate) -> Ticket:
    changes = data.model_dump(exclude_unset=True)

    new_status = changes.pop("status", None)
    if new_status and new_status != ticket.status:
        if not can_transition(Status(ticket.status), new_status):
            raise TransitionError(f"Cannot move ticket from '{ticket.status}' to '{new_status}'")
        ticket.status = new_status
        if new_status == Status.resolved:
            ticket.resolved_at = datetime.now(UTC)
        elif new_status == Status.open:
            ticket.resolved_at = None

    new_priority = changes.get("priority")
    if new_priority and new_priority != ticket.priority:
        # The SLA clock keeps its start time, only the target changes.
        ticket.due_at = due_date(new_priority, ticket.created_at)

    for field, value in changes.items():
        setattr(ticket, field, value)

    db.commit()
    db.refresh(ticket)
    return ticket
