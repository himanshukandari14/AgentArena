import random
from datetime import datetime, timedelta
from sqlalchemy import select, delete
from app.db.init_db import init_db
from app.db.session import SessionLocal
from app.models import Customer, Invoice, Order, Ticket

CUSTOMERS = [
    ("Acme Corp", "acme.com"),
    ("Globex Corp", "globex.com"),
    ("Soylent Inc", "soylent.com"),
    ("Initech", "initech.com"),
    ("Umbrella Corp", "umbrella.com"),
    ("Stark Industries", "stark.com"),
    ("Wayne Enterprises", "wayne.com"),
    ("Cyberdyne Systems", "cyberdyne.com"),
    ("Aperture Science", "aperture.com"),
    ("Massive Dynamic", "massivedynamic.com"),
]

TEAMS = ["Support", "Billing", "Engineering", "Sales", "Enterprise Account Team"]
PRIORITIES = ["low", "medium", "high", "urgent"]
TICKET_STATUSES = ["open", "pending", "closed"]
ORDER_STATUSES = ["completed", "pending", "refunded", "cancelled"]
INVOICE_STATUSES = ["paid", "overdue", "pending"]


def random_date(days_back: int = 60) -> datetime:
    return datetime.utcnow() - timedelta(
        days=random.randint(0, days_back)
    )


def seed(force: bool = False) -> None:
    init_db()
    db = SessionLocal()

    try:
        if force:
            db.execute(delete(Ticket))
            db.execute(delete(Invoice))
            db.execute(delete(Order))
            db.execute(delete(Customer))
            db.commit()

        existing_customer = db.scalar(select(Customer).limit(1))
        if existing_customer and not force:
            return

        random.seed(42)  # Deterministic seed for environment reproducibility

        customers = []
        for i in range(30):
            company_name, domain = random.choice(CUSTOMERS)
            customer = Customer(
                name=f"Contact {i+1}",
                email=f"user{i+1}@{domain}",
                company=company_name,
                created_at=random_date(90),
            )
            customers.append(customer)

        db.add_all(customers)
        db.commit()

        for customer in customers:
            db.refresh(customer)

        # Synthetic Tickets
        tickets = []
        for i in range(60):
            cust = random.choice(customers)
            t = Ticket(
                customer_id=cust.id,
                subject=f"Issue {i+1} regarding {cust.company}",
                description=f"Synthetic customer support ticket description for issue {i+1} at {cust.company}.",
                status=random.choice(TICKET_STATUSES),
                priority=random.choice(PRIORITIES),
                assigned_team=random.choice(TEAMS),
                created_at=random_date(45),
            )
            tickets.append(t)

        db.add_all(tickets)

        # Synthetic Orders
        orders = []
        for _ in range(50):
            cust = random.choice(customers)
            o = Order(
                customer_id=cust.id,
                amount=round(random.uniform(50, 15000), 2),
                status=random.choice(ORDER_STATUSES),
                created_at=random_date(60),
            )
            orders.append(o)

        db.add_all(orders)

        # Synthetic Invoices
        invoices = []
        for _ in range(50):
            cust = random.choice(customers)
            inv = Invoice(
                customer_id=cust.id,
                amount=round(random.uniform(100, 8000), 2),
                status=random.choice(INVOICE_STATUSES),
                created_at=random_date(60),
            )
            invoices.append(inv)

        db.add_all(invoices)
        db.commit()
        print("Database seeded successfully.")

    finally:
        db.close()


if __name__ == "__main__":
    seed(force=True)