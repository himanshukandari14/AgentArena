from mcp.server.fastmcp import FastMCP
from sqlalchemy import select

from app.db.session import SessionLocal
from app.models import Customer, Invoice, Ticket


mcp = FastMCP("AgentArena")


@mcp.tool()
def search_customers(
    company: str | None = None,
    email: str | None = None,
) -> list[dict]:
    """Search customers by company or email."""

    db = SessionLocal()

    try:
        query = select(Customer)

        if company:
            query = query.where(
                Customer.company.ilike(f"%{company}%")
            )

        if email:
            query = query.where(
                Customer.email.ilike(f"%{email}%")
            )

        customers = db.scalars(query).all()

        return [
            {
                "id": customer.id,
                "name": customer.name,
                "email": customer.email,
                "company": customer.company,
            }
            for customer in customers
        ]

    finally:
        db.close()


@mcp.tool()
def search_tickets(
    customer_id: int | None = None,
    status: str | None = None,
) -> list[dict]:
    """Search support tickets."""

    db = SessionLocal()

    try:
        query = select(Ticket)

        if customer_id is not None:
            query = query.where(
                Ticket.customer_id == customer_id
            )

        if status is not None:
            query = query.where(
                Ticket.status == status
            )

        tickets = db.scalars(query).all()

        return [
            {
                "id": ticket.id,
                "customer_id": ticket.customer_id,
                "subject": ticket.subject,
                "status": ticket.status,
                "priority": ticket.priority,
                "assigned_team": ticket.assigned_team,
            }
            for ticket in tickets
        ]

    finally:
        db.close()


@mcp.tool()
def search_overdue_invoices(
    customer_id: int | None = None,
) -> list[dict]:
    """Find overdue invoices.

If customer_id is provided, return overdue invoices for that customer.
If customer_id is omitted, return all overdue invoices.
Prefer the no-argument form when identifying all customers with overdue invoices.
"""

    db = SessionLocal()

    try:
        query = select(Invoice).where(
            Invoice.status == "overdue"
        )

        if customer_id is not None:
            query = query.where(
                Invoice.customer_id == customer_id
            )

        invoices = db.scalars(query).all()

        return [
            {
                "id": invoice.id,
                "customer_id": invoice.customer_id,
                "amount": float(invoice.amount),
                "status": invoice.status,
            }
            for invoice in invoices
        ]

    finally:
        db.close()


@mcp.tool()
def update_ticket(
    ticket_id: int,
    status: str | None = None,
    priority: str | None = None,
    assigned_team: str | None = None,
) -> dict:
    """Update a support ticket."""

    db = SessionLocal()

    try:
        ticket = db.get(Ticket, ticket_id)

        if ticket is None:
            return {
                "success": False,
                "error": "Ticket not found",
            }

        if status is not None:
            ticket.status = status

        if priority is not None:
            ticket.priority = priority

        if assigned_team is not None:
            ticket.assigned_team = assigned_team

        db.commit()
        db.refresh(ticket)

        return {
            "success": True,
            "ticket": {
                "id": ticket.id,
                "customer_id": ticket.customer_id,
                "status": ticket.status,
                "priority": ticket.priority,
                "assigned_team": ticket.assigned_team,
            },
        }

    finally:
        db.close()

@mcp.tool()
def search_actionable_tickets(
    customer_id: int,
) -> list[dict]:
    """Find open or pending tickets for a customer."""

    db = SessionLocal()

    try:
        query = (
            select(Ticket)
            .where(Ticket.customer_id == customer_id)
            .where(Ticket.status.in_(["open", "pending"]))
        )

        tickets = db.scalars(query).all()

        return [
            {
                "id": ticket.id,
                "customer_id": ticket.customer_id,
                "subject": ticket.subject,
                "status": ticket.status,
                "priority": ticket.priority,
                "assigned_team": ticket.assigned_team,
            }
            for ticket in tickets
        ]

    finally:
        db.close()

@mcp.tool()
def find_tickets_needing_billing(
) -> list[dict]:
    """Find open or pending tickets belonging to customers with overdue invoices
    that are not currently assigned to the Billing team.
    """

    db = SessionLocal()

    try:
        query = (
            select(Ticket)
            .join(
                Invoice,
                Invoice.customer_id == Ticket.customer_id,
            )
            .where(
                Invoice.status == "overdue",
                Ticket.status.in_(["open", "pending"]),
                Ticket.assigned_team != "Billing",
            )
        )

        tickets = db.scalars(query).unique().all()

        return [
            {
                "id": ticket.id,
                "customer_id": ticket.customer_id,
                "subject": ticket.subject,
                "status": ticket.status,
                "priority": ticket.priority,
                "assigned_team": ticket.assigned_team,
            }
            for ticket in tickets
        ]

    finally:
        db.close()


if __name__ == "__main__":
    import os

    mcp_port = os.getenv("MCP_PORT")
    if mcp_port:
        # SSE transport — used inside Docker sandbox containers.
        # host/port are settings on the FastMCP instance, not run() kwargs.
        # Disable DNS rebinding protection so host machine can reach the container.
        from mcp.server.transport_security import TransportSecuritySettings

        mcp.settings.host = "0.0.0.0"
        mcp.settings.port = int(mcp_port)
        mcp.settings.transport_security = TransportSecuritySettings(
            enable_dns_rebinding_protection=False,
            allowed_hosts=["*"],
            allowed_origins=["*"],
        )
        mcp.run(transport="sse")
    else:
        # stdio transport — used for local development
        mcp.run()