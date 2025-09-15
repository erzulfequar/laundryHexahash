from pydantic import BaseModel
from typing import Optional, List

# ---------- Auth ----------
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class LoginRequest(BaseModel):
    username: str
    password: str

# ---------- Customer ----------
class CustomerBase(BaseModel):
    name: str
    phone: str
    email: Optional[str] = None

class CustomerCreate(CustomerBase):
    pass

class CustomerOut(CustomerBase):
    id: int
    branch_id: Optional[int] = None
    organization_id: Optional[int] = None

    class Config:
        orm_mode = True

# ---------- Order ----------
class OrderItemIn(BaseModel):
    article: str
    qty: int = 1
    with_wash: bool = False

class OrderCreate(BaseModel):
    customer_id: int
    weight: float
    ironing_items: List[OrderItemIn] = []
    dryclean_items: List[OrderItemIn] = []
    total_amount: float
    status: Optional[str] = "Pending"
