"""
Payment API routes.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.payment import PaymentCreate, PaymentResponse
from app.services.payment_service import PaymentService

router = APIRouter(prefix="/api/payments", tags=["Payments"])


@router.post("/", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
async def initiate_payment(data: PaymentCreate, db: AsyncSession = Depends(get_db)):
    """Initiate a new payment."""
    service = PaymentService(db)
    payment = await service.initiate_payment(data)
    return PaymentResponse.model_validate(payment)


@router.post("/{payment_id}/process", response_model=PaymentResponse)
async def process_payment(payment_id: str, db: AsyncSession = Depends(get_db)):
    """Process a pending payment (simulate processing)."""
    service = PaymentService(db)
    try:
        payment = await service.process_payment(payment_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return PaymentResponse.model_validate(payment)


@router.get("/", response_model=list[PaymentResponse])
async def list_payments(
    status_filter: str | None = Query(None, alias="status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    service = PaymentService(db)
    payments = await service.list_payments(status=status_filter, skip=skip, limit=limit)
    return [PaymentResponse.model_validate(p) for p in payments]


@router.get("/{payment_id}", response_model=PaymentResponse)
async def get_payment(payment_id: str, db: AsyncSession = Depends(get_db)):
    service = PaymentService(db)
    payment = await service.get_payment(payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return PaymentResponse.model_validate(payment)
