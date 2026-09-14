# Transaction Service API Documentation

## Service Overview
The Transaction Service records all financial ledger entries, publishes transaction events to Kafka, and coordinates two-phase commits for fund transfers.

## Endpoints
### GET /api/transactions/
Query transaction ledger with filter parameters: `account_id`, `status`, `start_date`, `end_date`.

### POST /api/transactions/
Post a new ledger entry with automatic balance validation.

## Performance Requirements
- Throughput: Up to 5,000 transactions per second under peak banking hours.
- Consistency: Strict serializable or read-committed isolation level on database.
