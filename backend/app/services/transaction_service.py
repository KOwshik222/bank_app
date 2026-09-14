"""
Transaction service — financial transaction recording and event publishing.
"""

import logging
import random
import string
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.events import Event, get_event_bus
from app.models.transaction import Transaction, TransactionStatus, TransactionType

logger = logging.getLogger(__name__)


class TransactionService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.event_bus = get_event_bus()

    @staticmethod
    def _generate_reference() -> str:
        return f"TXN-{''.join(random.choices(string.digits, k=10))}"

    async def record_transaction(
        self,
        account_id: str,
        transaction_type: str,
        amount: float,
        description: str | None = None,
        payment_id: str | None = None,
        balance_after: float | None = None,
        correlation_id: str | None = None,
        source_service: str | None = None,
    ) -> Transaction:
        """Record a financial transaction."""
        txn = Transaction(
            transaction_reference=self._generate_reference(),
            account_id=account_id,
            transaction_type=TransactionType(transaction_type),
            amount=Decimal(str(amount)),
            description=description,
            payment_id=payment_id,
            balance_after=Decimal(str(balance_after)) if balance_after else None,
            correlation_id=correlation_id or str(uuid4()),
            source_service=source_service or "transaction-service",
            status=TransactionStatus.COMPLETED,
        )
        self.db.add(txn)
        await self.db.flush()

        # Publish event
        await self.event_bus.publish(
            Event(
                topic="transaction.recorded",
                payload={
                    "transaction_id": txn.id,
                    "reference": txn.transaction_reference,
                    "type": txn.transaction_type.value,
                    "amount": float(txn.amount),
                    "account_id": account_id,
                },
                correlation_id=txn.correlation_id,
                source_service="transaction-service",
            )
        )

        logger.info(
            f"Transaction recorded: {txn.transaction_reference} "
            f"type={txn.transaction_type.value} amount={txn.amount}"
        )
        return txn

    async def get_transaction(self, transaction_id: str) -> Transaction | None:
        result = await self.db.execute(
            select(Transaction).where(Transaction.id == transaction_id)
        )
        return result.scalar_one_or_none()

    async def list_transactions(
        self,
        account_id: str | None = None,
        transaction_type: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[Transaction]:
        query = (
            select(Transaction).offset(skip).limit(limit).order_by(Transaction.created_at.desc())
        )
        if account_id:
            query = query.where(Transaction.account_id == account_id)
        if transaction_type:
            query = query.where(Transaction.transaction_type == TransactionType(transaction_type))
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def count_transactions(self) -> int:
        result = await self.db.execute(select(Transaction))
        return len(result.scalars().all())
