"""
Payment service — payment initiation, processing simulation, and status tracking.
Includes simulated failures for incident generation.
"""

import logging
import random
import string
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.events import Event, get_event_bus
from app.models.payment import Payment, PaymentMethod, PaymentStatus
from app.schemas.payment import PaymentCreate

logger = logging.getLogger(__name__)


class PaymentService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.event_bus = get_event_bus()

    @staticmethod
    def _generate_reference() -> str:
        return f"PAY-{''.join(random.choices(string.digits, k=10))}"

    async def initiate_payment(
        self, data: PaymentCreate, correlation_id: str | None = None
    ) -> Payment:
        """Initiate a new payment."""
        payment = Payment(
            payment_reference=self._generate_reference(),
            source_account_id=data.source_account_id,
            destination_account_id=data.destination_account_id,
            amount=Decimal(str(data.amount)),
            currency=data.currency,
            payment_method=PaymentMethod(data.payment_method),
            description=data.description,
            status=PaymentStatus.PENDING,
            correlation_id=correlation_id or str(uuid4()),
        )
        self.db.add(payment)
        await self.db.flush()

        # Publish event
        await self.event_bus.publish(
            Event(
                topic="payment.initiated",
                payload={
                    "payment_id": payment.id,
                    "reference": payment.payment_reference,
                    "amount": float(payment.amount),
                    "status": payment.status.value,
                },
                correlation_id=payment.correlation_id,
                source_service="payment-service",
            )
        )

        logger.info(f"Payment initiated: {payment.payment_reference} amount={payment.amount}")

        # If external banking rail (WIRE / ACH) is used, authorize through partner bank
        if payment.payment_method in (PaymentMethod.WIRE, PaymentMethod.ACH):
            from app.services.external_bank_client import ExternalBankClient, ExternalBankingOutageError
            ext_client = ExternalBankClient()
            desc = (payment.description or "").upper()
            test_user = "user_bank_down" if "FAULT_EXT_OUTAGE" in desc else "user_good"
            if "FAULT_RATE_LIMIT" in desc:
                test_user = "user_rate_limit"

            try:
                auth_res = await ext_client.authorize_external_transfer(
                    amount=float(payment.amount),
                    source_account_id=payment.source_account_id,
                    destination_account_id=payment.destination_account_id,
                    test_user=test_user,
                )
                payment.status = PaymentStatus.COMPLETED
                logger.info(f"Payment cleared via external rail {auth_res.get('institution')}: {payment.payment_reference}")
            except ExternalBankingOutageError as e:
                payment.status = PaymentStatus.FAILED
                payment.error_message = e.message
                await self.db.flush()
                logger.error(f"Outbound API call to external payment processor failing with HTTP {e.status_code}: {e.message}")
                raise e

        return payment

    async def process_payment(self, payment_id: str) -> Payment:
        """Simulate payment processing. May fail for incident simulation."""
        payment = await self.get_payment(payment_id)
        if not payment:
            raise ValueError(f"Payment not found: {payment_id}")

        payment.status = PaymentStatus.PROCESSING
        await self.db.flush()

        # Simulate processing — 95% success in normal operation
        success = random.random() < 0.95

        if success:
            payment.status = PaymentStatus.COMPLETED
            logger.info(f"Payment completed: {payment.payment_reference}")
        else:
            payment.status = PaymentStatus.FAILED
            payment.error_message = random.choice([
                "Database connection timeout",
                "Insufficient funds",
                "Payment gateway unavailable",
                "Transaction limit exceeded",
                "Account validation failed",
            ])
            logger.error(
                f"Payment failed: {payment.payment_reference} — {payment.error_message}"
            )

        await self.db.flush()

        # Publish result event
        await self.event_bus.publish(
            Event(
                topic=f"payment.{'completed' if success else 'failed'}",
                payload={
                    "payment_id": payment.id,
                    "reference": payment.payment_reference,
                    "status": payment.status.value,
                    "error": payment.error_message,
                },
                correlation_id=payment.correlation_id,
                source_service="payment-service",
            )
        )

        return payment

    async def get_payment(self, payment_id: str) -> Payment | None:
        result = await self.db.execute(select(Payment).where(Payment.id == payment_id))
        return result.scalar_one_or_none()

    async def get_payment_by_reference(self, reference: str) -> Payment | None:
        result = await self.db.execute(
            select(Payment).where(Payment.payment_reference == reference)
        )
        return result.scalar_one_or_none()

    async def list_payments(
        self,
        status: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[Payment]:
        query = select(Payment).offset(skip).limit(limit).order_by(Payment.created_at.desc())
        if status:
            query = query.where(Payment.status == PaymentStatus(status))
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def count_payments(self, status: str | None = None) -> int:
        query = select(Payment)
        if status:
            query = query.where(Payment.status == PaymentStatus(status))
        result = await self.db.execute(query)
        return len(result.scalars().all())
