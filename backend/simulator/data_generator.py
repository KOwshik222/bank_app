"""
Synthetic data generator — creates realistic banking data.
Generates customers, accounts, transactions, and deployments.
"""

import random
import string
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

# Realistic name pools
FIRST_NAMES = [
    "James", "Mary", "Robert", "Patricia", "John", "Jennifer", "Michael", "Linda",
    "David", "Elizabeth", "William", "Barbara", "Richard", "Susan", "Joseph", "Jessica",
    "Thomas", "Sarah", "Christopher", "Karen", "Charles", "Lisa", "Daniel", "Nancy",
    "Matthew", "Betty", "Anthony", "Margaret", "Mark", "Sandra", "Donald", "Ashley",
    "Steven", "Dorothy", "Paul", "Kimberly", "Andrew", "Emily", "Joshua", "Donna",
    "Kenneth", "Michelle", "Kevin", "Carol", "Brian", "Amanda", "George", "Melissa",
    "Timothy", "Deborah", "Ronald", "Stephanie", "Edward", "Rebecca", "Jason", "Sharon",
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
    "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
    "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson",
    "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson", "Walker",
    "Young", "Allen", "King", "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores",
    "Green", "Adams", "Nelson", "Baker", "Hall", "Rivera", "Campbell", "Mitchell",
]

CITIES = [
    ("New York", "NY"), ("Los Angeles", "CA"), ("Chicago", "IL"), ("Houston", "TX"),
    ("Phoenix", "AZ"), ("Philadelphia", "PA"), ("San Antonio", "TX"), ("San Diego", "CA"),
    ("Dallas", "TX"), ("San Jose", "CA"), ("Austin", "TX"), ("Jacksonville", "FL"),
    ("Fort Worth", "TX"), ("Columbus", "OH"), ("Charlotte", "NC"), ("Indianapolis", "IN"),
    ("San Francisco", "CA"), ("Seattle", "WA"), ("Denver", "CO"), ("Boston", "MA"),
]

STREETS = [
    "Main St", "Oak Ave", "Cedar Ln", "Elm St", "Pine Rd", "Maple Dr", "Washington Blvd",
    "Park Ave", "Lake St", "Hill Rd", "River Dr", "Valley Way", "Forest Ave", "Spring St",
]

ACCOUNT_TYPES = ["CHECKING", "SAVINGS", "BUSINESS", "CREDIT"]
PAYMENT_METHODS = ["ACH", "WIRE", "INTERNAL", "CARD", "REAL_TIME"]
TX_DESCRIPTIONS = [
    "Direct deposit", "Online purchase", "ATM withdrawal", "Bill payment",
    "Transfer to savings", "Rent payment", "Grocery store", "Gas station",
    "Restaurant", "Subscription", "Insurance premium", "Utility bill",
    "Loan payment", "Investment transfer", "Refund", "Salary deposit",
    "Freelance payment", "Wire transfer", "Mobile deposit", "Point of sale",
]


def generate_customer_data(count: int = 100) -> list[dict]:
    """Generate synthetic customer profiles."""
    customers = []
    used_emails = set()

    for _ in range(count):
        first = random.choice(FIRST_NAMES)
        last = random.choice(LAST_NAMES)
        city, state = random.choice(CITIES)

        # Ensure unique emails
        base_email = f"{first.lower()}.{last.lower()}"
        email = f"{base_email}@example.com"
        counter = 1
        while email in used_emails:
            email = f"{base_email}{counter}@example.com"
            counter += 1
        used_emails.add(email)

        customers.append({
            "first_name": first,
            "last_name": last,
            "email": email,
            "phone": f"+1-{random.randint(200,999)}-{random.randint(100,999)}-{random.randint(1000,9999)}",
            "address": f"{random.randint(100, 9999)} {random.choice(STREETS)}",
            "city": city,
            "state": state,
            "zip_code": f"{random.randint(10000, 99999)}",
            "country": "US",
        })
    return customers


def generate_account_data(customer_ids: list[str]) -> list[dict]:
    """Generate 1-3 accounts per customer."""
    accounts = []
    for cid in customer_ids:
        num_accounts = random.choices([1, 2, 3], weights=[0.3, 0.5, 0.2])[0]
        types = random.sample(ACCOUNT_TYPES, min(num_accounts, len(ACCOUNT_TYPES)))
        for acc_type in types:
            balance_ranges = {
                "CHECKING": (500, 50000),
                "SAVINGS": (1000, 200000),
                "BUSINESS": (5000, 500000),
                "CREDIT": (-15000, 0),
            }
            low, high = balance_ranges[acc_type]
            balance = round(random.uniform(low, high), 2)

            accounts.append({
                "customer_id": cid,
                "account_type": acc_type,
                "balance": balance,
                "currency": "USD",
                "daily_limit": random.choice([5000, 10000, 25000, 50000, 100000]),
            })
    return accounts


def generate_transaction_data(
    account_ids: list[str],
    days: int = 30,
    per_day_range: tuple[int, int] = (5, 50),
) -> list[dict]:
    """Generate realistic transaction history."""
    transactions = []
    now = datetime.now(timezone.utc)

    for day_offset in range(days, 0, -1):
        day_start = now - timedelta(days=day_offset)
        num_txns = random.randint(*per_day_range)

        for _ in range(num_txns):
            account_id = random.choice(account_ids)
            hour = random.randint(6, 23)
            minute = random.randint(0, 59)
            ts = day_start.replace(hour=hour, minute=minute, second=random.randint(0, 59))

            tx_type = random.choices(
                ["DEPOSIT", "WITHDRAWAL", "TRANSFER", "PAYMENT", "FEE"],
                weights=[0.25, 0.2, 0.2, 0.3, 0.05],
            )[0]

            amount_ranges = {
                "DEPOSIT": (100, 10000),
                "WITHDRAWAL": (20, 2000),
                "TRANSFER": (50, 5000),
                "PAYMENT": (10, 3000),
                "FEE": (5, 50),
            }
            low, high = amount_ranges[tx_type]
            amount = round(random.uniform(low, high), 2)

            status = random.choices(
                ["COMPLETED", "FAILED", "PENDING"],
                weights=[0.95, 0.03, 0.02],
            )[0]

            transactions.append({
                "account_id": account_id,
                "transaction_type": tx_type,
                "amount": amount,
                "status": status,
                "description": random.choice(TX_DESCRIPTIONS),
                "timestamp": ts.isoformat(),
                "correlation_id": str(uuid4()),
            })

    return sorted(transactions, key=lambda t: t["timestamp"])


SERVICES = [
    "payment-service", "account-service", "customer-service",
    "transaction-service", "authentication-service", "notification-service",
]

DEPLOYMENT_VERSIONS = {
    "payment-service": ["v2.5.0", "v2.6.0", "v2.7.0", "v2.7.1", "v2.8.0"],
    "account-service": ["v1.9.0", "v1.9.1", "v2.0.0", "v2.0.1", "v2.1.0"],
    "customer-service": ["v3.1.0", "v3.1.1", "v3.2.0"],
    "transaction-service": ["v1.5.0", "v1.5.1", "v1.6.0", "v1.6.1"],
    "authentication-service": ["v2.0.0", "v2.0.1", "v2.1.0", "v2.1.1"],
    "notification-service": ["v1.2.0", "v1.2.1", "v1.3.0"],
}


def generate_deployment_history(days: int = 30) -> list[dict]:
    """Generate simulated deployment history."""
    deployments = []
    now = datetime.now(timezone.utc)

    for service in SERVICES:
        versions = DEPLOYMENT_VERSIONS[service]
        num_deploys = random.randint(2, min(len(versions), 4))
        selected = versions[-num_deploys:]

        for i, version in enumerate(selected):
            day_offset = random.randint(1, days)
            deploy_time = now - timedelta(
                days=day_offset,
                hours=random.randint(8, 18),
                minutes=random.randint(0, 59),
            )

            config_changes = []
            if random.random() < 0.4:
                config_changes = random.sample([
                    "max_connections: 100 → 500",
                    "timeout_ms: 5000 → 3000",
                    "pool_size: 10 → 50",
                    "retry_count: 3 → 5",
                    "cache_ttl: 300 → 60",
                    "rate_limit: 1000 → 5000",
                    "log_level: INFO → DEBUG",
                    "ssl_enabled: false → true",
                ], k=random.randint(1, 3))

            deployments.append({
                "service": service,
                "version": version,
                "previous_version": selected[i - 1] if i > 0 else None,
                "deployed_at": deploy_time.isoformat(),
                "deployed_by": random.choice(["ci-pipeline", "ops-team", "developer"]),
                "status": random.choices(["SUCCESS", "FAILED", "ROLLED_BACK"], weights=[0.85, 0.1, 0.05])[0],
                "config_changes": config_changes,
                "commit_hash": "".join(random.choices("0123456789abcdef", k=8)),
                "notes": f"Deploy {version} to production" if random.random() < 0.5 else None,
            })

    return sorted(deployments, key=lambda d: d["deployed_at"])
