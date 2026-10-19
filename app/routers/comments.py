from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app import services
from app.database import get_db
from app.deps import require_api_key
from app.models import Ticket
from app.routers.tickets import get_ticket_or_404
from app.schemas import CommentCreate, CommentRead

router = APIRouter(prefix="/tickets/{ticket_id}/comments", tags=["comments"])


@router.get("", response_model=list[CommentRead], summary="List comments of a ticket")
def list_comments(include_internal: bool = True, ticket: Ticket = Depends(get_ticket_or_404)):
    if include_internal:
        return ticket.comments
    return [c for c in ticket.comments if not c.internal]


@router.post(
    "",
    response_model=CommentRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_api_key)],
    summary="Add a comment or an internal note",
)
def add_comment(
    data: CommentCreate,
    ticket: Ticket = Depends(get_ticket_or_404),
    db: Session = Depends(get_db),
):
    return services.add_comment(db, ticket, data)
