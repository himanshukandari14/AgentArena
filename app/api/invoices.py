from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Invoice
from app.schemas.invoice import InvoiceResponse

router = APIRouter(prefix="/invoices", tags=["invoices"])


@router.get("", response_model=list[InvoiceResponse])
def list_invoices(
    customer_id: int | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
):
    query = select(Invoice).order_by(Invoice.id)

    if customer_id is not None:
        query = query.where(Invoice.customer_id == customer_id)

    if status is not None:
        query = query.where(Invoice.status == status)

    return db.scalars(query).all()