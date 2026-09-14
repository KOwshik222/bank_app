"""
Transaction API routes.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.payment import TransactionResponse
from app.services.transaction_service import TransactionService

router = APIRouter(prefix="/api/transactions", tags=["Transactions"])


@router.get("/", response_model=list[TransactionResponse])
async def list_transactions(
    account_id: str | None = None,
    transaction_type: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    service = TransactionService(db)
    txns = await service.list_transactions(
        account_id=account_id, transaction_type=transaction_type, skip=skip, limit=limit
    )
    return [TransactionResponse.model_validate(t) for t in txns]


@router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(transaction_id: str, db: AsyncSession = Depends(get_db)):
    service = TransactionService(db)
    txn = await service.get_transaction(transaction_id)
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return TransactionResponse.model_validate(txn)
