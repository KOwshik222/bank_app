"""
Account API routes.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.customer import AccountCreate, AccountResponse
from app.services.account_service import AccountService

router = APIRouter(prefix="/api/accounts", tags=["Accounts"])


@router.post("/", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
async def create_account(data: AccountCreate, db: AsyncSession = Depends(get_db)):
    service = AccountService(db)
    account = await service.create_account(data)
    return AccountResponse.model_validate(account)


@router.get("/", response_model=list[AccountResponse])
async def list_accounts(
    customer_id: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    service = AccountService(db)
    accounts = await service.list_accounts(customer_id=customer_id, skip=skip, limit=limit)
    return [AccountResponse.model_validate(a) for a in accounts]


@router.get("/{account_id}", response_model=AccountResponse)
async def get_account(account_id: str, db: AsyncSession = Depends(get_db)):
    service = AccountService(db)
    account = await service.get_account(account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return AccountResponse.model_validate(account)
