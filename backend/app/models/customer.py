"""
Customer model — synthetic banking customer profiles.
"""

from uuid import uuid4

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, TimestampMixin


class Customer(Base, TimestampMixin):
    __tablename__ = "customers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    customer_number: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    phone: Mapped[str] = mapped_column(String(20), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    state: Mapped[str | None] = mapped_column(String(50), nullable=True)
    zip_code: Mapped[str | None] = mapped_column(String(10), nullable=True)
    country: Mapped[str] = mapped_column(String(50), default="US")
    is_active: Mapped[bool] = mapped_column(default=True)
    risk_score: Mapped[float] = mapped_column(default=0.0)  # 0.0 - 1.0

    # Relationships
    accounts = relationship("Account", back_populates="customer", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Customer {self.customer_number} {self.first_name} {self.last_name}>"

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"
