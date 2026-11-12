from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime

class OrderItemCreate(BaseModel):
    product_id: int
    quantity: int
    unit_price: float

class OrderCreate(BaseModel):
    user_id: int
    email: Optional[EmailStr] = None
    items: List[OrderItemCreate]

class OrderResponse(BaseModel):
    id: int
    user_id: int
    status: str
    total: float
    created_at: datetime

    class Config:
        from_attributes = True