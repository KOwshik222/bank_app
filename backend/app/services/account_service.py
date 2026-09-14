"""
Account service — account creation, balance management, and queries.
"""

import logging
import random
import string

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.account import Account, AccountStatus, AccountType
from app.schemas.customer import AccountCreate

logger = logging.getLogger(__name__)


class AccountService:
    def __init__(self, db: AsyncSession):
        self.db = db

    @staticmethod
    def _generate_account_number() -> str:
        """Generate a realistic account number like 4012-8845-7721."""
        parts = [
            "".join(random.choices(string.digits, k=4)) for _ in range(3)
        ]
        return "-".join(parts)

    async def create_account(self, data: AccountCreate) -> Account:
        account = Account(
            account_number=self._generate_account_number(),
            customer_id=data.customer_id,
            account_type=AccountType(data.account_type),
            currency=data.currency,
            daily_limit=Decimal(str(data.daily_limit)),
            balance=Decimal("0.00"),
        )
        self.db.add(account)
        await self.db.flush()
        logger.info(f"Account created: {account.account_number} type={account.account_type.value}")
        return account

    async def get_account(self, account_id: str) -> Account | None:
        result = await self.db.execute(select(Account).where(Account.id == account_id))
        return result.scalar_one_or_none()

    async def get_account_by_number(self, account_number: str) -> Account | None:
        result = await self.db.execute(
            select(Account).where(Account.account_number == account_number)
        )
        return result.scalar_one_or_none()

    async def list_accounts(
        self, customer_id: str | None = None, skip: int = 0, limit: int = 50
    ) -> list[Account]:
        query = select(Account).offset(skip).limit(limit)
        if customer_id:
            query = query.where(Account.customer_id == customer_id)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_balance(self, account_id: str, delta: Decimal) -> Account | None:
        """Adjust balance by delta (positive = credit, negative = debit)."""
        account = await self.get_account(account_id)
        if not account:
            return None
        new_balance = account.balance + delta
        if new_balance < 0 and account.account_type != AccountType.CREDIT:
            raise ValueError(f"Insufficient funds: balance={account.balance}, delta={delta}")
        account.balance = new_balance
        await self.db.flush()
        return account

    async def freeze_account(self, account_id: str) -> Account | None:
        account = await self.get_account(account_id)
        if account:
            account.status = AccountStatus.FROZEN
            await self.db.flush()
        return account

    async def count_accounts(self) -> int:
        result = await self.db.execute(select(Account))
        return len(result.scalars().all())
