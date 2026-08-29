from pydantic import BaseModel, ConfigDict


class TicketUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str | None = None
    priority: str | None = None
    assigned_team: str | None = None


class TicketResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    customer_id: int
    subject: str
    description: str
    status: str
    priority: str
    assigned_team: str | None