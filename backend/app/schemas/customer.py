"""
Pydantic schemas for customer service.
"""

from datetime import datetime

from pydantic import BaseModel, Field


class CustomerCreate(BaseModel):
    first_name: str = Field(..., max_length=100)
    last_name: str = Field(..., max_length=100)
    email: str = Field(..., max_length=255)
    phone: str | None = None
    address: str | None = None
    city: str | None = None
    state: str | None = None
    zip_code: str | None = None
    country: str = "US"


class CustomerResponse(BaseModel):
    id: str
    customer_number: str
    first_name: str
    last_name: str
    email: str
    phone: str | None = None
    city: str | None = None
    state: str | None = None
    country: str
    is_active: bool
    risk_score: float
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class CustomerUpdate(BaseModel):
    email: str | None = None
    phone: str | None = None
    address: str | None = None
    city: str | None = None
    state: str | None = None
    zip_code: str | None = None
    is_active: bool | None = None


# ── Account Schemas ──────────────────────────────────────────────
class AccountCreate(BaseModel):
    customer_id: str
    account_type: str
    currency: str = "USD"
    daily_limit: float = 10000.00


class AccountResponse(BaseModel):
    id: str
    account_number: str
    customer_id: str
    account_type: str
    status: str
    balance: float
    currency: str
    daily_limit: float
    created_at: datetime | None = None

    model_config = {"from_attributes": True}
