from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.models import Customer, Invoice, Order, Ticket


def verify_billing_escalation(db: Session) -> dict:
    """Task 1: Verify all open/pending tickets of customers with overdue invoices are assigned to Billing."""
    # Find customers with overdue invoices
    overdue_customer_ids = db.scalars(
        select(Invoice.customer_id)
        .where(Invoice.status == "overdue")
        .distinct()
    ).all()

    if not overdue_customer_ids:
        return {"passed": True, "score": 1.0, "reason": "No overdue invoices found."}

    # Check open/pending tickets for these customers
    target_tickets = db.scalars(
        select(Ticket).where(
            Ticket.customer_id.in_(overdue_customer_ids),
            Ticket.status.in_(["open", "pending"]),
        )
    ).all()

    if not target_tickets:
        return {"passed": True, "score": 1.0, "reason": "No unresolved tickets for overdue customers."}

    unassigned = [t.id for t in target_tickets if t.assigned_team != "Billing"]

    if unassigned:
        score = (len(target_tickets) - len(unassigned)) / len(target_tickets)
        return {
            "passed": False,
            "score": round(score, 2),
            "reason": f"Tickets not assigned to Billing: {unassigned}",
        }

    return {"passed": True, "score": 1.0, "reason": "All required tickets successfully assigned to Billing."}


def verify_vip_escalation(db: Session) -> dict:
    """Task 2: Verify open tickets for customers with total spend > 10,000 have priority 'urgent'."""
    vip_customers = db.scalars(
        select(Order.customer_id)
        .group_by(Order.customer_id)
        .having(func.sum(Order.total_amount) > 10000)
    ).all()

    if not vip_customers:
        return {"passed": True, "score": 1.0, "reason": "No VIP customers identified."}

    tickets = db.scalars(
        select(Ticket).where(
            Ticket.customer_id.in_(vip_customers),
            Ticket.status == "open",
        )
    ).all()

    if not tickets:
        return {"passed": True, "score": 1.0, "reason": "No open tickets for VIP customers."}

    non_urgent = [t.id for t in tickets if t.priority != "urgent"]
    if non_urgent:
        score = (len(tickets) - len(non_urgent)) / len(tickets)
        return {
            "passed": False,
            "score": round(score, 2),
            "reason": f"VIP open tickets not set to urgent: {non_urgent}",
        }

    return {"passed": True, "score": 1.0, "reason": "All VIP open tickets escalated to urgent."}


def verify_stale_ticket_cleanup(db: Session) -> dict:
    """Task 3: Verify low priority open tickets are closed."""
    low_open_tickets = db.scalars(
        select(Ticket).where(
            Ticket.priority == "low",
            Ticket.status == "open",
        )
    ).all()

    if low_open_tickets:
        return {
            "passed": False,
            "score": 0.0,
            "reason": f"Found {len(low_open_tickets)} low priority tickets still open.",
        }

    return {"passed": True, "score": 1.0, "reason": "All low priority tickets closed."}


def verify_ticket_priority_alignment(db: Session) -> dict:
    """Task 4: Verify tickets with 'CRITICAL' in subject have priority 'urgent'."""
    critical_tickets = db.scalars(
        select(Ticket).where(Ticket.subject.ilike("%CRITICAL%"))
    ).all()

    if not critical_tickets:
        return {"passed": True, "score": 1.0, "reason": "No critical subject tickets found."}

    misaligned = [t.id for t in critical_tickets if t.priority != "urgent"]
    if misaligned:
        score = (len(critical_tickets) - len(misaligned)) / len(critical_tickets)
        return {
            "passed": False,
            "score": round(score, 2),
            "reason": f"Critical tickets not priority urgent: {misaligned}",
        }

    return {"passed": True, "score": 1.0, "reason": "All critical tickets assigned urgent priority."}


def verify_unassigned_routing(db: Session) -> dict:
    """Task 5: Verify unassigned tickets are assigned to appropriate teams."""
    unassigned = db.scalars(
        select(Ticket).where(
            Ticket.assigned_team.in_(["Unassigned", None, ""])
        )
    ).all()

    if unassigned:
        return {
            "passed": False,
            "score": 0.0,
            "reason": f"{len(unassigned)} tickets remain unassigned.",
        }

    return {"passed": True, "score": 1.0, "reason": "All tickets properly routed."}


def verify_duplicate_ticket_close(db: Session) -> dict:
    """Task 6: Verify duplicate tickets for the same customer are closed."""
    # Find customers with multiple open tickets with identical subjects
    subquery = (
        select(Ticket.customer_id, Ticket.subject)
        .where(Ticket.status == "open")
        .group_by(Ticket.customer_id, Ticket.subject)
        .having(func.count(Ticket.id) > 1)
    ).all()

    if subquery:
        return {
            "passed": False,
            "score": 0.0,
            "reason": f"Duplicate open tickets still exist for customer-subject pairs: {subquery}",
        }

    return {"passed": True, "score": 1.0, "reason": "No open duplicate tickets remaining."}


def verify_overdue_invoice_reminder(db: Session) -> dict:
    """Task 7: Verify overdue invoice customers have tickets marked 'pending_payment'."""
    overdue_customers = db.scalars(
        select(Invoice.customer_id).where(Invoice.status == "overdue").distinct()
    ).all()

    if not overdue_customers:
        return {"passed": True, "score": 1.0, "reason": "No overdue invoices found."}

    tickets = db.scalars(
        select(Ticket).where(Ticket.customer_id.in_(overdue_customers))
    ).all()

    invalid = [t.id for t in tickets if t.status != "pending_payment"]
    if invalid:
        score = (len(tickets) - len(invalid)) / len(tickets)
        return {
            "passed": False,
            "score": round(score, 2),
            "reason": f"Overdue customer tickets not set to pending_payment: {invalid}",
        }

    return {"passed": True, "score": 1.0, "reason": "All overdue customer tickets set to pending_payment."}


def verify_order_refund_escalation(db: Session) -> dict:
    """Task 8: Verify refunded order customer tickets escalated to Tier 3 Support."""
    refunded_customers = db.scalars(
        select(Order.customer_id).where(Order.status == "refunded").distinct()
    ).all()

    if not refunded_customers:
        return {"passed": True, "score": 1.0, "reason": "No refunded orders found."}

    tickets = db.scalars(
        select(Ticket).where(
            Ticket.customer_id.in_(refunded_customers),
            Ticket.status == "open",
        )
    ).all()

    invalid = [t.id for t in tickets if t.assigned_team != "Tier 3 Support" or t.priority != "urgent"]
    if invalid:
        score = (len(tickets) - len(invalid)) / len(tickets)
        return {
            "passed": False,
            "score": round(score, 2),
            "reason": f"Refunded order tickets not properly escalated: {invalid}",
        }

    return {"passed": True, "score": 1.0, "reason": "Refunded order tickets successfully escalated."}


def verify_engineering_bug_routing(db: Session) -> dict:
    """Task 9: Verify tickets with 'API' or 'Bug' in subject assigned to Engineering."""
    bug_tickets = db.scalars(
        select(Ticket).where(
            (Ticket.subject.ilike("%API%")) | (Ticket.subject.ilike("%Bug%"))
        )
    ).all()

    if not bug_tickets:
        return {"passed": True, "score": 1.0, "reason": "No API/Bug tickets found."}

    misrouted = [t.id for t in bug_tickets if t.assigned_team != "Engineering"]
    if misrouted:
        score = (len(bug_tickets) - len(misrouted)) / len(bug_tickets)
        return {
            "passed": False,
            "score": round(score, 2),
            "reason": f"Bug tickets not assigned to Engineering: {misrouted}",
        }

    return {"passed": True, "score": 1.0, "reason": "All bug tickets routed to Engineering."}


def verify_enterprise_account_audit(db: Session) -> dict:
    """Task 10: Verify enterprise customer tickets assigned to Enterprise Account Team with priority urgent."""
    enterprise_customers = db.scalars(
        select(Customer.id).where(Customer.company.ilike("%Corp%") | Customer.company.ilike("%Inc%"))
    ).all()

    if not enterprise_customers:
        return {"passed": True, "score": 1.0, "reason": "No enterprise customers found."}

    tickets = db.scalars(
        select(Ticket).where(Ticket.customer_id.in_(enterprise_customers), Ticket.status == "open")
    ).all()

    invalid = [t.id for t in tickets if t.assigned_team != "Enterprise Account Team" or t.priority != "urgent"]
    if invalid:
        score = (len(tickets) - len(invalid)) / len(tickets)
        return {
            "passed": False,
            "score": round(score, 2),
            "reason": f"Enterprise tickets not escalated: {invalid}",
        }

    return {"passed": True, "score": 1.0, "reason": "All enterprise tickets escalated."}