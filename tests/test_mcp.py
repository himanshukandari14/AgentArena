from app.mcp.server import (
    search_customers,
    search_tickets,
    search_overdue_invoices,
    update_ticket,
)


def test_mcp_search_customers():
    results = search_customers()
    assert isinstance(results, list)


def test_mcp_search_tickets():
    tickets = search_tickets()
    assert isinstance(tickets, list)


def test_mcp_search_overdue_invoices():
    invoices = search_overdue_invoices()
    assert isinstance(invoices, list)


def test_mcp_update_ticket():
    # Attempt updating ticket ID 1
    result = update_ticket(ticket_id=1, status="open", priority="high")
    assert isinstance(result, dict)
    assert "success" in result
