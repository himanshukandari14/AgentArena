import random
from datetime import datetime, timedelta

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models import Customer, Invoice, Order, Ticket


CUSTOMERS = [
    ("Acme Corporation", "acme.com"),
    ("Globex Corporation", "globex.com"),
    ("Soylent Corp", "soylent.com"),
    ("Initech", "initech.com"),
    ("Umbrella Health", "umbrella.com"),
    ("Stark Industries", "stark.com"),
    ("Wayne Enterprises", "wayne.com"),
    ("Wonka Industries", "wonka.com"),
    ("Hooli", "hooli.com"),
    ("Massive Dynamic", "massivedynamic.com"),
]


FIRST_NAMES = [
    "John",
    "Sarah",
    "Michael",
    "David",
    "Emily",
    "Daniel",
    "James",
    "Olivia",
    "Robert",
    "Sophia",
]

LAST_NAMES = [
    "Smith",
    "Johnson",
    "Williams",
    "Brown",
    "Jones",
    "Miller",
    "Davis",
    "Wilson",
    "Taylor",
    "Anderson",
]


TICKET_SUBJECTS = [
    "Unable to process invoice",
    "Payment failed",
    "Account access issue",
    "Duplicate charge",
    "Missing order",
    "Incorrect billing amount",
    "API integration issue",
    "Password reset problem",
    "Subscription problem",
    "Refund request",
]


TEAMS = [
    "General Support",
    "Billing",
    "Technical Support",
    "Enterprise Support",
]


def random_date(days_back: int = 180) -> datetime:
    return datetime.utcnow() - timedelta(
        days=random.randint(0, days_back)
    )


from app.db.init_db import init_db


def seed() -> None:
    init_db()
    db = SessionLocal()

    try:
        # Prevent accidental duplicate seeding.
        existing_customer = db.scalar(select(Customer).limit(1))

        if existing_customer:
            print("Database already contains data. Skipping seed.")
            return

        customers = []

        for i in range(30):
            company_name, domain = random.choice(CUSTOMERS)

            customer = Customer(
                name=f"{random.choice(FIRST_NAMES)} "
                f"{random.choice(LAST_NAMES)}",
                email=f"customer{i + 1}@{domain}",
                company=company_name,
                created_at=random_date(),
            )

            customers.append(customer)

        db.add_all(customers)
        db.flush()

        tickets = []

        for _ in range(60):
            customer = random.choice(customers)

            ticket = Ticket(
                customer_id=customer.id,
                subject=random.choice(TICKET_SUBJECTS),
                description=(
                    "Customer reported an issue that requires "
                    "investigation by the support team."
                ),
                status=random.choice(
                    ["open", "open", "open", "pending", "resolved"]
                ),
                priority=random.choice(
                    ["low", "medium", "high"]
                ),
                assigned_team=random.choice(TEAMS),
                created_at=random_date(),
            )

            tickets.append(ticket)

        db.add_all(tickets)

        orders = []

        for _ in range(50):
            customer = random.choice(customers)

            order = Order(
                customer_id=customer.id,
                amount=round(random.uniform(100, 25000), 2),
                status=random.choice(
                    ["completed", "completed", "pending", "cancelled"]
                ),
                created_at=random_date(),
            )

            orders.append(order)

        db.add_all(orders)

        invoices = []

        for _ in range(50):
            customer = random.choice(customers)

            invoice = Invoice(
                customer_id=customer.id,
                amount=round(random.uniform(100, 15000), 2),
                status=random.choice(
                    ["paid", "paid", "unpaid", "overdue"]
                ),
                created_at=random_date(),
            )

            invoices.append(invoice)

        db.add_all(invoices)

        db.commit()

        print("Database seeded successfully.")
        print(f"Customers: {len(customers)}")
        print(f"Tickets: {len(tickets)}")
        print(f"Orders: {len(orders)}")
        print(f"Invoices: {len(invoices)}")

    finally:
        db.close()


if __name__ == "__main__":
    seed()