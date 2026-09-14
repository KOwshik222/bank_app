# Account Service API Documentation

## Service Overview
The Account Service manages all customer financial accounts, balances, account limits, and state transitions (ACTIVE, INACTIVE, FROZEN, CLOSED).

## Endpoints

### GET /api/accounts/
List accounts with filtering by `customer_id` and `account_type`.

### GET /api/accounts/{account_id}
Fetch detailed account status, current balance, and currency.

### GET /api/accounts/{account_id}/balance
Fetch real-time verified ledger balance for the account.

### POST /api/accounts/{account_id}/freeze
Freeze account in case of suspected fraud or security alert.

## Health Check
- `GET /health` returns `{ "status": "UP", "database": "CONNECTED", "cache": "HIT" }`.
- Expected P99 latency: < 45ms.
