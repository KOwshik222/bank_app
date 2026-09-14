"""
Seed script — populates the banking application database with synthetic data:
- System users (Admin, Incident Manager, Support Engineer)
- Customers & Accounts
- Initial Transactions
- Baseline Incidents
"""

import asyncio
import os
import sys
from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

# Ensure backend directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.database import async_session_factory, init_db
from app.models.user import Role, User
from app.models.customer import Customer
from app.models.account import Account, AccountType, AccountStatus
from app.models.payment import Payment
from app.models.transaction import Transaction, TransactionType, TransactionStatus
from app.models.incident import Incident, IncidentSeverity, IncidentStatus, IncidentCategory
from app.models.audit import AuditEntry
from app.services.auth_service import AuthService
from simulator.data_generator import (
    generate_customer_data,
    generate_account_data,
    generate_transaction_data,
)
from simulator.incident_scenarios import INCIDENT_SCENARIOS


async def seed_all():
    print("Initializing database tables...")
    await init_db()

    async with async_session_factory() as db:
        print("Checking/seeding system users...")
        for u_data in [
            {
                "username": "admin",
                "email": "admin@bank.com",
                "hashed_password": AuthService.hash_password("Admin@123!"),
                "full_name": "System Administrator",
                "role": Role.ADMIN,
            },
            {
                "username": "inc_manager",
                "email": "manager@bank.com",
                "hashed_password": AuthService.hash_password("Manager@123!"),
                "full_name": "Incident Manager",
                "role": Role.INCIDENT_MANAGER,
            },
            {
                "username": "support_eng",
                "email": "support@bank.com",
                "hashed_password": AuthService.hash_password("Support@123!"),
                "full_name": "L2/L3 Support Engineer",
                "role": Role.SUPPORT_ENGINEER,
            },
        ]:
            from sqlalchemy import select
            existing = await db.execute(select(User).where(User.username == u_data["username"]))
            if not existing.scalar_one_or_none():
                db.add(User(**u_data, is_active=True))
        await db.flush()

        print("Seeding synthetic customers...")
        raw_customers = generate_customer_data(count=30)
        customer_ids = []

        for i, rc in enumerate(raw_customers):
            cust_id = str(uuid4())
            customer = Customer(
                id=cust_id,
                customer_number=f"CUST-{10000 + i}",
                email=rc["email"],
                phone=rc.get("phone", "555-0100"),
                first_name=rc["first_name"],
                last_name=rc["last_name"],
                address=rc.get("address", "100 Financial Way"),
                city=rc.get("city", "New York"),
                state=rc.get("state", "NY"),
                zip_code=rc.get("zip_code", "10001"),
                country="US",
                is_active=True,
                risk_score=rc.get("risk_score", 0.15),
            )
            db.add(customer)
            customer_ids.append(cust_id)
        await db.flush()

        print("Seeding customer accounts...")
        raw_accounts = generate_account_data(customer_ids=customer_ids)
        account_ids = []
        for idx, ra in enumerate(raw_accounts):
            acc_id = str(uuid4())
            account = Account(
                id=acc_id,
                customer_id=ra["customer_id"],
                account_number=f"ACC-{10000000 + idx}",
                account_type=AccountType(ra.get("account_type", "CHECKING")),
                status=AccountStatus.ACTIVE,
                balance=Decimal(str(ra["balance"])),
                currency=ra.get("currency", "USD"),
                daily_limit=Decimal(str(ra.get("daily_limit", 10000))),
            )
            db.add(account)
            account_ids.append(acc_id)
        await db.flush()

        print("Seeding transactions...")
        raw_txs = generate_transaction_data(account_ids=account_ids, days=5, per_day_range=(5, 15))
        for rt in raw_txs:
            tx = Transaction(
                id=str(uuid4()),
                account_id=rt["account_id"],
                transaction_reference="TXN-" + str(uuid4())[:8].upper(),
                transaction_type=TransactionType(rt.get("transaction_type", "TRANSFER")),
                amount=Decimal(str(rt["amount"])),
                currency="USD",
                status=TransactionStatus(rt.get("status", "COMPLETED")),
                description=rt.get("description", "Banking operation"),
                source_service="payment-service",
            )
            db.add(tx)
        await db.flush()

        print("Seeding initial incident scenarios...")
        for i, sc in enumerate(INCIDENT_SCENARIOS[:5]):
            inc_num = f"INC-{10001 + i}"
            existing_inc = await db.execute(select(Incident).where(Incident.incident_number == inc_num))
            if not existing_inc.scalar_one_or_none():
                inc = Incident(
                    incident_number=inc_num,
                    title=sc["title"],
                    description=sc["description"],
                    severity=IncidentSeverity(sc["severity"]),
                    category=IncidentCategory(sc["category"]),
                    affected_service=sc["affected_service"],
                    status=IncidentStatus.OPEN if i == 0 else IncidentStatus.RESOLVED,
                    reported_by="automated-monitoring-system",
                    root_cause=sc["expected_root_cause"] if i != 0 else None,
                    recommended_remediation=sc["expected_remediation"] if i != 0 else None,
                    root_cause_confidence=sc["expected_confidence"] if i != 0 else None,
                )
                db.add(inc)

        print("Logging initial audit trail...")
        audit_entry = AuditEntry(
            action="system.seed",
            description="Database seeded with initial banking records, users, and scenarios",
            actor="seed_script",
            actor_type="system",
        )
        db.add(audit_entry)

        await db.commit()
        print("Successfully seeded all data!")


if __name__ == "__main__":
    asyncio.run(seed_all())
