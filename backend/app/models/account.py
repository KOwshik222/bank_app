"""
Account model — banking accounts with types and balances.
"""

import enum
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import Enum, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, TimestampMixin


class AccountType(str, enum.Enum):
    CHECKING = "CHECKING"
    SAVINGS = "SAVINGS"
    BUSINESS = "BUSINESS"
    LOAN = "LOAN"
    CREDIT = "CREDIT"


class AccountStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    FROZEN = "FROZEN"
    CLOSED = "CLOSED"


class Account(Base, TimestampMixin):
    __tablename__ = "accounts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    account_number: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    customer_id: Mapped[str] = mapped_column(ForeignKey("customers.id"), index=True)
    account_type: Mapped[AccountType] = mapped_column(Enum(AccountType))
    status: Mapped[AccountStatus] = mapped_column(
        Enum(AccountStatus), default=AccountStatus.ACTIVE
    )
    balance: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"))
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    daily_limit: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("10000.00"))

    # Relationships
    customer = relationship("Customer", back_populates="accounts", lazy="selectin")
    transactions = relationship("Transaction", back_populates="account", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Account {self.account_number} type={self.account_type.value} balance={self.balance}>"
