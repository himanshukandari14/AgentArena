from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Invoice, Ticket


def verify_billing_escalation(
    db: Session,
    customer_id: int,
) -> dict:
    # 1. Check that the customer has an overdue invoice.
    overdue_invoice = db.scalar(
        select(Invoice).where(
            Invoice.customer_id == customer_id,
            Invoice.status == "overdue",
        )
    )

    if overdue_invoice is None:
        return {
            "passed": False,
            "reason": "No overdue invoice found.",
        }

    # 2. Find unresolved tickets for that customer.
    tickets = db.scalars(
        select(Ticket).where(
            Ticket.customer_id == customer_id,
            Ticket.status.in_(["open", "pending"]),
        )
    ).all()

    if not tickets:
        return {
            "passed": False,
            "reason": "No unresolved tickets found.",
        }

    # 3. Check that every unresolved ticket is assigned to Billing.
    incorrect_tickets = [
        ticket.id
        for ticket in tickets
        if ticket.assigned_team != "Billing"
    ]

    if incorrect_tickets:
        return {
            "passed": False,
            "reason": (
                "Tickets not assigned to Billing: "
                f"{incorrect_tickets}"
            ),
        }

    # 4. Everything is correct.
    return {
        "passed": True,
        "reason": "All unresolved tickets assigned to Billing.",
    }