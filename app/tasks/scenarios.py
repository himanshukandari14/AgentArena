from sqlalchemy import delete, select

from app.db.session import SessionLocal
from app.models import Customer, Invoice, Ticket


def create_billing_escalation_scenario() -> None:
    db = SessionLocal()

    try:
        customer = db.scalar(
            select(Customer)
            .where(Customer.email == "scenario@acme.com")
        )

        if customer is None:
            customer = Customer(
                name="Scenario Customer",
                email="scenario@acme.com",
                company="Acme Corporation",
            )

            db.add(customer)
            db.flush()

        # Remove previous scenario data.
        db.execute(
            delete(Invoice).where(
                Invoice.customer_id == customer.id
            )
        )

        db.execute(
            delete(Ticket).where(
                Ticket.customer_id == customer.id
            )
        )

        invoice = Invoice(
            customer_id=customer.id,
            amount=12500,
            status="overdue",
        )

        ticket = Ticket(
            customer_id=customer.id,
            subject="Urgent billing issue",
            description=(
                "Customer has an overdue invoice and "
                "requires billing assistance."
            ),
            status="open",
            priority="high",
            assigned_team="General Support",
        )

        db.add(invoice)
        db.add(ticket)

        db.commit()

        print("Billing escalation scenario created.")
        print(f"Customer ID: {customer.id}")
        print(f"Ticket ID: {ticket.id}")
        print(f"Invoice ID: {invoice.id}")

    finally:
        db.close()


if __name__ == "__main__":
    create_billing_escalation_scenario()