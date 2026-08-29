from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Ticket
from app.schemas.ticket import TicketResponse, TicketUpdate

router = APIRouter(prefix="/tickets", tags=["tickets"])


@router.get("", response_model=list[TicketResponse])
def list_tickets(
    status: str | None = None,
    priority: str | None = None,
    customer_id: int | None = None,
    db: Session = Depends(get_db),
):
    query = select(Ticket).order_by(Ticket.id)

    if status is not None:
        query = query.where(Ticket.status == status)

    if priority is not None:
        query = query.where(Ticket.priority == priority)

    if customer_id is not None:
        query = query.where(Ticket.customer_id == customer_id)

    return db.scalars(query).all()


@router.get("/{ticket_id}", response_model=TicketResponse)
def get_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
):
    ticket = db.get(Ticket, ticket_id)

    if ticket is None:
        raise HTTPException(
            status_code=404,
            detail="Ticket not found",
        )

    return ticket


@router.patch("/{ticket_id}", response_model=TicketResponse)
def update_ticket(
    ticket_id: int,
    update: TicketUpdate,
    db: Session = Depends(get_db),
):
    ticket = db.get(Ticket, ticket_id)

    if ticket is None:
        raise HTTPException(
            status_code=404,
            detail="Ticket not found",
        )

    if update.status is not None:
        ticket.status = update.status

    if update.priority is not None:
        ticket.priority = update.priority

    if update.assigned_team is not None:
        ticket.assigned_team = update.assigned_team

    db.commit()
    db.refresh(ticket)

    return ticket