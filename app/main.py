from fastapi import FastAPI

from app.api.customers import router as customers_router
from app.api.invoices import router as invoices_router
from app.api.orders import router as orders_router
from app.api.tickets import router as tickets_router
from app.api.runs import router as runs_router
from app.db.init_db import init_db

app = FastAPI(
    title="AgentForge",
    description="AI agent training and evaluation environment",
    version="0.1.0",
)


@app.on_event("startup")
def startup():
    init_db()


app.include_router(customers_router)
app.include_router(tickets_router)
app.include_router(orders_router)
app.include_router(invoices_router)
app.include_router(runs_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}