import pytest
import pytest_asyncio
from decimal import Decimal
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.database import Base
from app.models.customer import Customer
from app.models.account import Account, AccountType, AccountStatus
from app.models.payment import Payment, PaymentStatus, PaymentMethod
from app.models.user import User, Role
from app.services.customer_service import CustomerService
from app.services.account_service import AccountService
from app.services.payment_service import PaymentService
from app.services.auth_service import AuthService
from app.services.audit_service import AuditService
from app.schemas.customer import CustomerCreate, AccountCreate
from app.schemas.payment import PaymentCreate

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

@pytest.mark.asyncio
async def test_customer_creation_and_retrieval(db_session: AsyncSession):
    cust_service = CustomerService(db_session)
    data = CustomerCreate(
        first_name="Jane",
        last_name="Doe",
        email="jane.doe@examplebank.com",
        phone="+1234567890"
    )
    cust = await cust_service.create_customer(data)
    assert cust.id is not None
    assert cust.email == "jane.doe@examplebank.com"
    
    retrieved = await cust_service.get_customer(cust.id)
    assert retrieved is not None
    assert retrieved.first_name == "Jane"

@pytest.mark.asyncio
async def test_account_creation_and_balance(db_session: AsyncSession):
    cust_service = CustomerService(db_session)
    acc_service = AccountService(db_session)
    
    cust = await cust_service.create_customer(
        CustomerCreate(first_name="Alice", last_name="Smith", email="alice@examplebank.com")
    )
    
    acc_data = AccountCreate(
        customer_id=cust.id,
        account_type="CHECKING",
        currency="USD",
        daily_limit=10000.0
    )
    acc = await acc_service.create_account(acc_data)
    assert acc.id is not None
    assert acc.balance == Decimal("0.00")
    assert acc.status == AccountStatus.ACTIVE
    
    # Update balance
    updated = await acc_service.update_balance(acc.id, Decimal("500.00"))
    assert updated.balance == Decimal("500.00")

@pytest.mark.asyncio
async def test_payment_initiation(db_session: AsyncSession):
    cust_service = CustomerService(db_session)
    acc_service = AccountService(db_session)
    pay_service = PaymentService(db_session)
    
    cust = await cust_service.create_customer(
        CustomerCreate(first_name="Bob", last_name="Taylor", email="bob@examplebank.com")
    )
    acc_from = await acc_service.create_account(
        AccountCreate(customer_id=cust.id, account_type="CHECKING", currency="USD")
    )
    await acc_service.update_balance(acc_from.id, Decimal("1000.00"))

    acc_to = await acc_service.create_account(
        AccountCreate(customer_id=cust.id, account_type="SAVINGS", currency="USD")
    )
    
    payment_data = PaymentCreate(
        source_account_id=acc_from.id,
        destination_account_id=acc_to.id,
        amount=250.00,
        currency="USD",
        payment_method="INTERNAL",
        description="Transfer to savings"
    )
    payment = await pay_service.initiate_payment(payment_data)
    assert payment.id is not None
    assert payment.status in [PaymentStatus.PENDING, PaymentStatus.COMPLETED]
    assert payment.amount == Decimal("250.00")

@pytest.mark.asyncio
async def test_auth_service_hashing_and_tokens(db_session: AsyncSession):
    auth_service = AuthService(db_session)
    
    pw = "SecureBankingPassword123!"
    hashed = auth_service.hash_password(pw)
    assert auth_service.verify_password(pw, hashed) is True
    assert auth_service.verify_password("WrongPassword", hashed) is False
    
    token = auth_service.create_access_token(data={"sub": "test_user_id", "role": "ADMIN"})
    payload = auth_service.decode_token(token)
    assert payload is not None
    assert payload["sub"] == "test_user_id"
    assert payload["role"] == "ADMIN"

@pytest.mark.asyncio
async def test_audit_service_logging(db_session: AsyncSession):
    audit_service = AuditService(db_session)
    entry = await audit_service.log(
        action="TEST_ACTION",
        resource_type="ACCOUNT",
        resource_id="ACC-12345",
        actor="USER-999",
        description="Test audit log entry"
    )
    assert entry.id is not None
    assert entry.action == "TEST_ACTION"
    
    entries = await audit_service.list_entries(action="TEST_ACTION")
    assert len(entries) >= 1
    assert entries[0].resource_id == "ACC-12345"
