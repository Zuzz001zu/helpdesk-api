from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app import services
from app.database import get_db
from app.deps import require_api_key
from app.models import Priority, Status, Ticket
from app.schemas import Page, TicketCreate, TicketRead, TicketUpdate

router = APIRouter(prefix="/tickets", tags=["tickets"])


def get_ticket_or_404(ticket_id: int, db: Session = Depends(get_db)) -> Ticket:
    ticket = db.get(Ticket, ticket_id)
    if ticket is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    return ticket


@router.post(
    "",
    response_model=TicketRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_api_key)],
    summary="Open a new ticket",
)
def create_ticket(data: TicketCreate, db: Session = Depends(get_db)):
    return services.create_ticket(db, data)


@router.get("", response_model=Page[TicketRead], summary="List and filter tickets")
def list_tickets(
    status: Status | None = None,
    priority: Priority | None = None,
    assignee: str | None = None,
    q: str | None = Query(default=None, min_length=2, description="Search title and description"),
    overdue: bool | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    items, total = services.list_tickets(
        db,
        status=status,
        priority=priority,
        assignee=assignee,
        q=q,
        overdue=overdue,
        limit=limit,
        offset=offset,
    )
    return Page(items=items, total=total, limit=limit, offset=offset)


@router.get("/{ticket_id}", response_model=TicketRead, summary="Get one ticket")
def read_ticket(ticket: Ticket = Depends(get_ticket_or_404)):
    return ticket


@router.patch(
    "/{ticket_id}",
    response_model=TicketRead,
    dependencies=[Depends(require_api_key)],
    summary="Update a ticket, assign it or change its status",
)
def update_ticket(
    data: TicketUpdate,
    ticket: Ticket = Depends(get_ticket_or_404),
    db: Session = Depends(get_db),
):
    try:
        return services.update_ticket(db, ticket, data)
    except services.TransitionError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.delete(
    "/{ticket_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_api_key)],
    summary="Delete a ticket",
)
def delete_ticket(ticket: Ticket = Depends(get_ticket_or_404), db: Session = Depends(get_db)):
    db.delete(ticket)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
