from datetime import UTC, datetime, timedelta

import pytest

from app.models import Priority, Status
from app.sla import can_transition, due_date, is_overdue

START = datetime(2026, 3, 2, 9, 0, tzinfo=UTC)


@pytest.mark.parametrize(
    ("priority", "hours"),
    [(Priority.critical, 4), (Priority.high, 8), (Priority.medium, 24), (Priority.low, 72)],
)
def test_due_date_depends_on_priority(priority, hours):
    assert due_date(priority, START) == START + timedelta(hours=hours)


@pytest.mark.parametrize(
    ("current", "new", "allowed"),
    [
        (Status.open, Status.in_progress, True),
        (Status.in_progress, Status.resolved, True),
        (Status.resolved, Status.open, True),
        (Status.resolved, Status.closed, True),
        (Status.open, Status.closed, False),
        (Status.closed, Status.open, False),
        (Status.open, Status.open, True),
    ],
)
def test_transitions(current, new, allowed):
    assert can_transition(current, new) is allowed


def test_only_active_tickets_can_be_overdue():
    past = START - timedelta(hours=1)
    assert is_overdue(Status.open, past, START)
    assert is_overdue(Status.in_progress, past, START)
    assert not is_overdue(Status.resolved, past, START)
    assert not is_overdue(Status.open, START + timedelta(hours=1), START)
