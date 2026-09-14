"""
Customer service — CRUD for synthetic banking customers.
"""

import logging
import random
import string

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.customer import Customer
from app.schemas.customer import CustomerCreate, CustomerUpdate

logger = logging.getLogger(__name__)


class CustomerService:
    def __init__(self, db: AsyncSession):
        self.db = db

    @staticmethod
    def _generate_customer_number() -> str:
        """Generate a unique customer number like CUST-100234."""
        digits = "".join(random.choices(string.digits, k=6))
        return f"CUST-{digits}"

    async def create_customer(self, data: CustomerCreate) -> Customer:
        customer = Customer(
            customer_number=self._generate_customer_number(),
            first_name=data.first_name,
            last_name=data.last_name,
            email=data.email,
            phone=data.phone,
            address=data.address,
            city=data.city,
            state=data.state,
            zip_code=data.zip_code,
            country=data.country,
        )
        self.db.add(customer)
        await self.db.flush()
        logger.info(f"Customer created: {customer.customer_number}")
        return customer

    async def get_customer(self, customer_id: str) -> Customer | None:
        result = await self.db.execute(select(Customer).where(Customer.id == customer_id))
        return result.scalar_one_or_none()

    async def get_customer_by_number(self, customer_number: str) -> Customer | None:
        result = await self.db.execute(
            select(Customer).where(Customer.customer_number == customer_number)
        )
        return result.scalar_one_or_none()

    async def list_customers(
        self, skip: int = 0, limit: int = 50, active_only: bool = True
    ) -> list[Customer]:
        query = select(Customer).offset(skip).limit(limit).order_by(Customer.created_at.desc())
        if active_only:
            query = query.where(Customer.is_active == True)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_customer(self, customer_id: str, data: CustomerUpdate) -> Customer | None:
        customer = await self.get_customer(customer_id)
        if not customer:
            return None
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(customer, field, value)
        await self.db.flush()
        return customer

    async def count_customers(self) -> int:
        result = await self.db.execute(select(Customer))
        return len(result.scalars().all())
