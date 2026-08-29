from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Customer

router = APIRouter(prefix="/customers", tags=["customers"])


@router.get("")
def list_customers(db: Session = Depends(get_db)):
    customers = db.scalars(
        select(Customer).order_by(Customer.id)
    ).all()

    return customers


@router.get("/{customer_id}")
def get_customer(
    customer_id: int,
    db: Session = Depends(get_db),
):
    customer = db.get(Customer, customer_id)

    if customer is None:
        raise HTTPException(
            status_code=404,
            detail="Customer not found",
        )

    return customer