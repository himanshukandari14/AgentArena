# AgentForge — AI Agent Training & Evaluation Environment

> **AgentForge** is an isolated, reproducible evaluation environment and benchmarking suite for AI agents operating on complex multi-step enterprise tasks.

---

## Why Agent Evaluation Environments Are Needed

Evaluating AI agents using simple static benchmarks or LLM-as-a-judge prompts is unreliable. Complex agents execute multi-step workflows, call tools, read databases, and alter external system state. 

To determine whether an agent actually succeeded:
1. The agent must operate inside a **realistic application environment**.
2. Actions must execute through a **formal tool interface** (Model Context Protocol / FastMCP).
3. Outcomes must be verified by **checking actual system state changes**, not agent prose.
4. Failures must be systematically attributed to **Model Failure**, **Environment Failure**, or **Task Failure**.

---

## Architecture Overview

```text
                           User / Evaluation Trigger
                                       │
                                       ▼
                             FastAPI REST Layer
                        (/tasks, /runs, /runs/replay)
                                       │
                        ┌──────────────┴──────────────┐
                        ▼                             ▼
                Database Engine                  Worker Engine
             (PostgreSQL / SQLite)             (Async Task Runner)
                        │                             │
                        │                             ▼
                        │                      FastMCP Server
                        │                 (Agent Tool Layer)
                        │                             │
                        │                             ▼
                        │                        AI Agent
                        │                  (LLM Tool Calling)
                        │                             │
                        ▼                             ▼
                 Verification Engine ◄──────── Agent Output / Logs
           (State & Score Calculation)
                        │
                        ▼
           Signature Failure Classifier
     (MODEL, ENVIRONMENT, or TASK Failure)
```

---

## Key Features

- **AgentDesk Application**: Enterprise backend exposing Customers, Support Tickets, Invoices, and Orders.
- **10 Task Evaluation Suite**: Structured tasks across Easy, Medium, and Hard difficulty levels.
- **Model Context Protocol (MCP) Tools**: Native FastMCP tool server providing tools like `search_customers`, `search_tickets`, `search_overdue_invoices`, and `update_ticket`.
- **Deterministic Verification Engine**: Multi-factor scoring (60% Functional, 20% State Correctness, 20% Step Economy).
- **Signature Failure Attribution**: Classifies failures into `MODEL_FAILURE`, `ENVIRONMENT_FAILURE`, and `TASK_FAILURE`.
- **Run Persistence & Trace Logging**: Captures every step, tool call, argument, and output for full auditability.
- **Replay Capability**: Rerun past runs from initial clean snapshot states.

---

## Tool / MCP Interface

Agents interact with AgentForge through FastMCP tools:

```python
search_customers(company: str | None, email: str | None)
search_tickets(customer_id: int | None, status: str | None)
search_overdue_invoices(customer_id: int | None)
update_ticket(ticket_id: int, status: str | None, priority: str | None, assigned_team: str | None)
search_actionable_tickets(customer_id: int)
find_tickets_needing_billing()
```

---

## Failure Attribution Classifier

```text
              Was run state & infrastructure healthy?
                             │
                  ┌──────────┴──────────┐
                  ▼                     ▼
                 NO                    YES
                  │                     │
      ┌───────────┴───────────┐         └─────────────────┐
      ▼                       ▼                           ▼
Environment Crash       Task Spec Error            Agent Made Error /
        │                     │                    Missed State Change
        ▼                     ▼                           ▼
ENVIRONMENT_FAILURE     TASK_FAILURE                 MODEL_FAILURE
```

---

## Local Setup & Quickstart

### Prerequisites
- Python 3.11+
- `uv` (Fast Python package installer)

### Setup Steps

```bash
# 1. Install dependencies
uv sync

# 2. Seed synthetic dataset
uv run python scripts/seed.py

# 3. Start the AgentForge API
uv run uvicorn app.main:app --reload --port 8000
```

---

## Running Tasks & Benchmark Tests

```bash
# List available evaluation tasks
curl http://localhost:8000/tasks

# Trigger a task run asynchronously
curl -X POST http://localhost:8000/runs \
     -H "Content-Type: application/json" \
     -d '{"task_id": "billing_escalation"}'

# Check run trace, score, and failure attribution
curl http://localhost:8000/runs/<run_id>

# Run pytest automated test suite
uv run pytest
```
