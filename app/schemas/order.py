from pydantic import BaseModel, ConfigDict


class OrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    customer_id: int
    amount: float
    status: str