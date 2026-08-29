from pydantic import BaseModel, ConfigDict


class InvoiceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    customer_id: int
    amount: float
    status: str