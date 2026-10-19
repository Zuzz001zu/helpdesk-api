from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import services
from app.database import get_db
from app.schemas import Stats

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("", response_model=Stats, summary="Ticket counts, overdue tickets and resolution time")
def read_stats(db: Session = Depends(get_db)):
    return services.get_stats(db)
