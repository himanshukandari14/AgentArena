from dataclasses import dataclass
from typing import Callable

from sqlalchemy.orm import Session

from app.tasks.verifiers import (
    verify_billing_escalation,
    verify_vip_escalation,
    verify_stale_ticket_cleanup,
    verify_ticket_priority_alignment,
    verify_unassigned_routing,
    verify_duplicate_ticket_close,
    verify_overdue_invoice_reminder,
    verify_order_refund_escalation,
    verify_engineering_bug_routing,
    verify_enterprise_account_audit,
)


@dataclass(frozen=True)
class TaskDefinition:
    id: str
    name: str
    description: str
    difficulty: str  # easy, medium, hard
    timeout_seconds: int
    verifier: Callable[[Session], dict]


TASKS: dict[str, TaskDefinition] = {
    "billing_escalation": TaskDefinition(
        id="billing_escalation",
        name="Billing Escalation",
        description="Find open/pending tickets for customers with overdue invoices and assign them to the Billing team.",
        difficulty="easy",
        timeout_seconds=60,
        verifier=verify_billing_escalation,
    ),
    "vip_escalation": TaskDefinition(
        id="vip_escalation",
        name="VIP Customer Ticket Escalation",
        description="Find open tickets belonging to high-value customers (spend > $10,000) and set priority to urgent.",
        difficulty="easy",
        timeout_seconds=60,
        verifier=verify_vip_escalation,
    ),
    "stale_ticket_cleanup": TaskDefinition(
        id="stale_ticket_cleanup",
        name="Stale Low Priority Ticket Cleanup",
        description="Find all open tickets with low priority and close them.",
        difficulty="medium",
        timeout_seconds=90,
        verifier=verify_stale_ticket_cleanup,
    ),
    "ticket_priority_alignment": TaskDefinition(
        id="ticket_priority_alignment",
        name="Critical Ticket Priority Alignment",
        description="Search for tickets containing 'CRITICAL' in their subject and elevate priority to urgent.",
        difficulty="easy",
        timeout_seconds=60,
        verifier=verify_ticket_priority_alignment,
    ),
    "unassigned_routing": TaskDefinition(
        id="unassigned_routing",
        name="Unassigned Ticket Routing",
        description="Find unassigned tickets and route them to their respective departmental teams.",
        difficulty="medium",
        timeout_seconds=90,
        verifier=verify_unassigned_routing,
    ),
    "duplicate_ticket_close": TaskDefinition(
        id="duplicate_ticket_close",
        name="Duplicate Ticket Deduplication",
        description="Find duplicate open tickets from the same customer with identical subjects and close duplicates.",
        difficulty="medium",
        timeout_seconds=120,
        verifier=verify_duplicate_ticket_close,
    ),
    "overdue_invoice_reminder": TaskDefinition(
        id="overdue_invoice_reminder",
        name="Overdue Invoice Status Update",
        description="Mark support tickets of customers with overdue invoices as pending_payment.",
        difficulty="medium",
        timeout_seconds=90,
        verifier=verify_overdue_invoice_reminder,
    ),
    "order_refund_escalation": TaskDefinition(
        id="order_refund_escalation",
        name="Refunded Order Escalation",
        description="Find open tickets associated with refunded orders and escalate to Tier 3 Support with urgent priority.",
        difficulty="hard",
        timeout_seconds=150,
        verifier=verify_order_refund_escalation,
    ),
    "engineering_bug_routing": TaskDefinition(
        id="engineering_bug_routing",
        name="Engineering Bug Ticket Routing",
        description="Locate open tickets referencing API or Bug issues and assign them to the Engineering team.",
        difficulty="hard",
        timeout_seconds=120,
        verifier=verify_engineering_bug_routing,
    ),
    "enterprise_account_audit": TaskDefinition(
        id="enterprise_account_audit",
        name="Enterprise Account Ticket Audit",
        description="Identify enterprise customers (Inc/Corp) and assign all open tickets to Enterprise Account Team with urgent priority.",
        difficulty="hard",
        timeout_seconds=180,
        verifier=verify_enterprise_account_audit,
    ),
}


def get_task(task_id: str) -> TaskDefinition:
    if task_id not in TASKS:
        raise KeyError(f"Task '{task_id}' not found in registered task suite.")
    return TASKS[task_id]


def list_tasks() -> list[dict]:
    return [
        {
            "id": t.id,
            "name": t.name,
            "description": t.description,
            "difficulty": t.difficulty,
            "timeout_seconds": t.timeout_seconds,
        }
        for t in TASKS.values()
    ]