# AgentForge — AI Agent Training & Evaluation Environment

> **AgentForge** is an isolated, reproducible evaluation environment for AI agents operating on complex multi-step enterprise tasks — built to demonstrate the same class of engineering problems found in agent training infrastructure.

---

## Why Agent Evaluation Environments Are Needed

Evaluating AI agents using static benchmarks or LLM-as-a-judge prompts is fundamentally unreliable. Real agents execute multi-step workflows, call tools, read databases, and alter external system state.

To determine whether an agent actually succeeded:

1. The agent must operate inside a **realistic application environment**
2. Actions must execute through a **formal tool interface** (MCP / FastMCP)
3. Outcomes must be verified by **checking actual system state**, not agent prose
4. Failures must be systematically attributed to **Model**, **Environment**, or **Task** failure

---

## Architecture

```text
                     User / API Client
                            │
                            ▼
                  FastAPI REST Layer
             (/tasks  /runs  /runs/replay)
                            │
              ┌─────────────┴─────────────┐
              ▼                           ▼
       SQLite Database             Async Worker
      (runs, tool calls,         (asyncio task queue)
       scores, traces)                   │
                                         ▼
                              ┌─────────────────────┐
                              │  Docker Sandbox      │
                              │  ─────────────────  │
                              │  Fresh SQLite copy   │
                              │  MCP SSE Server      │
                              │  CPU: 1.0 core       │
                              │  RAM: 512 MB         │
                              │  Timeout enforced    │
                              └─────────────────────┘
                                         │
                              ┌──────────┴──────────┐
                              ▼                     ▼
                          AI Agent           Verifier Engine
                    (LLM + MCP tools)    (state checks + score)
                                                    │
                                                    ▼
                                       Failure Attribution
                                  MODEL / ENVIRONMENT / TASK
```

---

## Environment Isolation — Key Design

Every task run gets a **fresh Docker container** from the `agentforge-sandbox` image:

```text
POST /runs  →  worker picks up job
                    ↓
         docker run agentforge-sandbox:latest
              ├── Restore seeded DB snapshot
              ├── Start MCP SSE server (port 9000)
              ├── 1.0 CPU limit
              └── 512 MB memory limit
                    ↓
         Agent connects via HTTP/SSE
         Tool calls hit the container's isolated DB
                    ↓
         Verifier checks container's final state
                    ↓
         Container destroyed (pass / fail / crash / timeout)
```

This ensures:
- Every run starts from an **identical known state** (baked-in seed snapshot)
- Runs cannot interfere with each other even under concurrency
- Crashed or timed-out containers are force-killed automatically
- Every run records its `container_id` and `env_version` for replay

---

## Task Suite (10 Tasks)

| ID | Name | Difficulty |
|----|------|-----------|
| `billing_escalation` | Billing Escalation | Easy |
| `vip_escalation` | VIP Customer Ticket Escalation | Easy |
| `ticket_priority_alignment` | Critical Ticket Priority Alignment | Easy |
| `stale_ticket_cleanup` | Stale Low Priority Ticket Cleanup | Medium |
| `unassigned_routing` | Unassigned Ticket Routing | Medium |
| `duplicate_ticket_close` | Duplicate Ticket Deduplication | Medium |
| `overdue_invoice_reminder` | Overdue Invoice Status Update | Medium |
| `order_refund_escalation` | Refunded Order Escalation | Hard |
| `engineering_bug_routing` | Engineering Bug Ticket Routing | Hard |
| `enterprise_account_audit` | Enterprise Account Ticket Audit | Hard |

---

## MCP Tool Interface

The agent interacts exclusively through FastMCP tools:

```python
search_customers(company: str | None, email: str | None) → list[dict]
search_tickets(customer_id: int | None, status: str | None) → list[dict]
search_overdue_invoices(customer_id: int | None) → list[dict]
update_ticket(ticket_id: int, status, priority, assigned_team) → dict
search_actionable_tickets(customer_id: int) → list[dict]
find_tickets_needing_billing() → list[dict]
```

---

## Verification & Scoring

The verifier never trusts the agent's output — it queries the database directly:

```text
Expected: ticket.assigned_team = "Billing"
Actual:   ticket.assigned_team = "Billing"   → PASS

Functional correctness   60%
State correctness         20%
Step economy              20%
```

Scoring is **deterministic** — the same run replayed produces the same score.

---

## Failure Attribution

```text
        Was infrastructure healthy during run?
                       │
           ┌───────────┴───────────┐
           ▼                       ▼
          NO                      YES
           │                       │
  ┌────────┴────────┐     ┌────────┴────────┐
  ▼                 ▼     ▼                 ▼
Docker crash   Task spec  Agent missed   Agent wrong
DB failure     invalid    a state change  tool call
     │              │          │              │
     ▼              ▼          └──────────────┘
ENVIRONMENT_   TASK_                 │
 FAILURE       FAILURE          MODEL_FAILURE
```

---

## Run Lifecycle & Reliability

**Run states:** `queued → running → passed | failed | timed_out`

The worker handles:
- **Worker crashes** → container still destroyed in `finally` block
- **Agent timeouts** → `asyncio.wait_for(timeout=task.timeout_seconds)` cancels run
- **Docker failures** → caught as `ENVIRONMENT_FAILURE`, run marked `failed`
- **Tool call errors** → logged per-step, counted toward scoring
- **Duplicate jobs** → idempotent run creation (unique run IDs)

---

## Replay

Any past run can be replayed from the exact same starting state:

```bash
POST /runs/replay
{ "run_id": "run_2e05e545" }
```

This spawns a new container using the same `env_version` and task definition,
restoring the identical seeded DB snapshot. The `container_id` from the original
run is stored for investigation.

---

## Observability

OpenTelemetry spans cover the full lifecycle:

| Span | Measures |
|------|---------|
| `agentforge.task_run` | Full run: run_id, task_id, status, score, failure_category |
| `agentforge.environment_prepare` | Docker spawn + SSE readiness time |
| `agentforge.agent_execution` | LLM iterations + MCP tool round-trips |
| `agentforge.verifier_eval` | State verification + failure classification |

---

## Load Test Results

All measurements made on Apple M-series, Docker Desktop, `agentforge-sandbox:latest`.

### Baseline (N=1, single isolated container)

```text
Total Elapsed Time : 27.76s
P50 Latency        : 25.16s
Throughput         : 2.2 tasks/min
Timed Out          : 0
```

### Bottleneck Found (N=3 concurrent containers)

```text
Total Elapsed Time : 67.02s
P50 Latency        : 61.49s
Timed Out          : 3 / 3  ← all tasks hit 60s limit
```

**Root cause:** 3 containers sharing 1 Docker Desktop VM fought for CPU.
LLM HTTP round-trips (to OpenRouter) slowed from ~2s to ~6s per call.
At 10+ iterations per task, the 60s per-task timeout was exceeded.

This was not infrastructure failure — the containers ran correctly. The
timeout was too tight for concurrent Docker runs on a single machine.

### Fix Applied

1. Added `timeout_multiplier` parameter to load test — concurrent runs
   use `3×` the per-task timeout to account for CPU contention
2. Documented this as expected single-machine behaviour
3. In a real multi-node deployment (separate hosts per container), the
   baseline latency would hold at ~25s regardless of concurrency

```bash
# Run the load test with fix applied
uv run python scripts/load_test.py 3   # 3 concurrent containers, 3x timeout
```

---

## Engineering Tradeoffs

| Decision | Why |
|----------|-----|
| SQLite over PostgreSQL | Simpler isolation — each container gets its own file copy with zero config |
| SSE over stdio for MCP | stdio only works for local subprocesses; SSE works over network to Docker |
| `uv sync` at image build time | Avoids repeating dependency install (~15s) on every container spawn |
| `asyncio.wait_for` for timeout | Clean cancellation without killing the event loop |
| `finally` block for cleanup | Containers are destroyed even if the worker process crashes mid-run |

**Known limitations:**
- At 10+ concurrent runs, Docker Desktop on a laptop becomes the bottleneck (port binding, CPU shares)
- The MCP SSE server uses legacy SSE transport — newer MCP versions use streamable-http
- SQLite WAL mode handles concurrent readers but each container has its own file anyway

**Future improvements:**
- Build-time snapshot compression to reduce image size
- Streamable-HTTP transport for lower MCP overhead
- Pre-warmed container pool to eliminate startup latency

---

## Local Setup

### Prerequisites

- Python 3.12+
- `uv` package manager
- Docker Desktop (running)

### 1. Install dependencies

```bash
uv sync
```

### 2. Build the sandbox image (required for task runs)

```bash
docker build -f Dockerfile.sandbox -t agentforge-sandbox:latest .
```

This bakes a seeded database snapshot into the image. Takes ~2 minutes on first build, then cached.

### 3. Configure your LLM API key

```bash
cp .env.example .env
# Add your OPENROUTER_API_KEY or OPENAI_API_KEY
```

### 4. Start the API

```bash
uv run uvicorn app.main:app --reload --port 8000
```

### 5. (Optional) Start the dashboard

```bash
cd frontend && npm install && npm run dev
```

---

## Running Tasks

```bash
# List all 10 evaluation tasks
curl http://localhost:8000/tasks

# Trigger a task run (returns immediately, executes async)
curl -X POST http://localhost:8000/runs \
     -H "Content-Type: application/json" \
     -d '{"task_id": "billing_escalation"}'
# → {"run_id": "run_2e05e545", "status": "queued"}

# Check result, score, tool calls, failure attribution
curl http://localhost:8000/runs/run_2e05e545

# Replay a past run from identical starting state
curl -X POST http://localhost:8000/runs/replay \
     -H "Content-Type: application/json" \
     -d '{"run_id": "run_2e05e545"}'
```

---

## Running Tests

```bash
uv run pytest -v
```

---

## Running the Load Test

```bash
uv run python scripts/load_test.py
```

Runs 10 concurrent task evaluations and prints p50/p95/p99 latencies and throughput.
