"""
Pydantic schemas for payment service.
"""

from datetime import datetime

from pydantic import BaseModel, Field


class PaymentCreate(BaseModel):
    source_account_id: str
    destination_account_id: str | None = None
    amount: float = Field(..., gt=0)
    currency: str = "USD"
    payment_method: str
    description: str | None = None


class PaymentResponse(BaseModel):
    id: str
    payment_reference: str
    source_account_id: str
    destination_account_id: str | None = None
    amount: float
    currency: str
    status: str
    payment_method: str
    description: str | None = None
    error_message: str | None = None
    correlation_id: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


# ── Transaction Schemas ──────────────────────────────────────────
class TransactionResponse(BaseModel):
    id: str
    transaction_reference: str
    account_id: str
    transaction_type: str
    status: str
    amount: float
    currency: str
    balance_after: float | None = None
    description: str | None = None
    payment_id: str | None = None
    correlation_id: str | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}
