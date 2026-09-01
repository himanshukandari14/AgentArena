from contextlib import asynccontextmanager
import os
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.api.customers import router as customers_router
from app.api.invoices import router as invoices_router
from app.api.orders import router as orders_router
from app.api.tickets import router as tickets_router
from app.api.runs import router as runs_router
from app.api.metrics import router as metrics_router
from app.db.init_db import init_db


from app.telemetry import init_telemetry


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    init_telemetry("agent-forge")
    yield


from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="AgentArena",
    description="AI agent training and evaluation environment",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Route endpoints
app.include_router(customers_router)
app.include_router(tickets_router)
app.include_router(orders_router)
app.include_router(invoices_router)
app.include_router(runs_router)
app.include_router(metrics_router)

# Mount Dashboard Static Web UI
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/dashboard", StaticFiles(directory=static_dir, html=True), name="dashboard")


@app.get("/")
def root_redirect():
    return RedirectResponse(url="/dashboard")


@app.get("/health")
def health_check():
    return {"status": "ok"}