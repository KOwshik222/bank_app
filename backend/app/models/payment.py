"""
Payment model — payment initiation, processing, and status tracking.
"""

import enum
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import Enum, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base, TimestampMixin


class PaymentStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    REFUNDED = "REFUNDED"


class PaymentMethod(str, enum.Enum):
    ACH = "ACH"
    WIRE = "WIRE"
    INTERNAL = "INTERNAL"
    CARD = "CARD"
    REAL_TIME = "REAL_TIME"


class Payment(Base, TimestampMixin):
    __tablename__ = "payments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    payment_reference: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    source_account_id: Mapped[str] = mapped_column(ForeignKey("accounts.id"), index=True)
    destination_account_id: Mapped[str | None] = mapped_column(
        ForeignKey("accounts.id"), nullable=True
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2))
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus), default=PaymentStatus.PENDING
    )
    payment_method: Mapped[PaymentMethod] = mapped_column(Enum(PaymentMethod))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    correlation_id: Mapped[str | None] = mapped_column(String(36), index=True, nullable=True)

    def __repr__(self) -> str:
        return f"<Payment {self.payment_reference} {self.amount} {self.status.value}>"
