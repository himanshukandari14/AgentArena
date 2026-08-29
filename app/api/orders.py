from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Order
from app.schemas.order import OrderResponse

router = APIRouter(prefix="/orders", tags=["orders"])


@router.get("", response_model=list[OrderResponse])
def list_orders(
    customer_id: int | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
):
    query = select(Order).order_by(Order.id)

    if customer_id is not None:
        query = query.where(Order.customer_id == customer_id)

    if status is not None:
        query = query.where(Order.status == status)

    return db.scalars(query).all()