from datetime import datetime, timedelta

from app.models import Priority, Status

# Target resolution time per priority, in hours.
SLA_HOURS = {
    Priority.critical: 4,
    Priority.high: 8,
    Priority.medium: 24,
    Priority.low: 72,
}

# Which status changes are allowed. Resolved tickets can be reopened,
# closed tickets are final.
TRANSITIONS = {
    Status.open: {Status.in_progress, Status.resolved},
    Status.in_progress: {Status.open, Status.resolved},
    Status.resolved: {Status.closed, Status.open},
    Status.closed: set(),
}

ACTIVE_STATUSES = (Status.open, Status.in_progress)


def due_date(priority: Priority, start: datetime) -> datetime:
    return start + timedelta(hours=SLA_HOURS[priority])


def can_transition(current: Status, new: Status) -> bool:
    return new == current or new in TRANSITIONS[current]


def is_overdue(status: str, due_at: datetime, now: datetime) -> bool:
    return status in ACTIVE_STATUSES and now > due_at
