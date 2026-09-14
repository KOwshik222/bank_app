"""
Transaction model — all financial transaction records.
"""

import enum
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import Enum, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, TimestampMixin


class TransactionType(str, enum.Enum):
    DEPOSIT = "DEPOSIT"
    WITHDRAWAL = "WITHDRAWAL"
    TRANSFER = "TRANSFER"
    PAYMENT = "PAYMENT"
    FEE = "FEE"
    INTEREST = "INTEREST"
    REVERSAL = "REVERSAL"


class TransactionStatus(str, enum.Enum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    REVERSED = "REVERSED"


class Transaction(Base, TimestampMixin):
    __tablename__ = "transactions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    transaction_reference: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    account_id: Mapped[str] = mapped_column(ForeignKey("accounts.id"), index=True)
    transaction_type: Mapped[TransactionType] = mapped_column(Enum(TransactionType))
    status: Mapped[TransactionStatus] = mapped_column(
        Enum(TransactionStatus), default=TransactionStatus.PENDING
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2))
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    balance_after: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    payment_id: Mapped[str | None] = mapped_column(
        ForeignKey("payments.id"), nullable=True, index=True
    )
    correlation_id: Mapped[str | None] = mapped_column(String(36), index=True, nullable=True)
    source_service: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Relationships
    account = relationship("Account", back_populates="transactions", lazy="selectin")

    def __repr__(self) -> str:
        return (
            f"<Transaction {self.transaction_reference} "
            f"{self.transaction_type.value} {self.amount} {self.status.value}>"
        )
