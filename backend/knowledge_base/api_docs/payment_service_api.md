# Payment Service API Documentation

## Service Overview
The Payment Service handles all payment processing operations including payment initiation,
processing, status tracking, and refunds.

## Endpoints

### POST /api/payments/
Initiate a new payment.

**Request:**
```json
{
    "source_account_id": "string",
    "destination_account_id": "string",
    "amount": 100.00,
    "currency": "USD",
    "payment_method": "ACH|WIRE|INTERNAL|CARD|REAL_TIME",
    "description": "Payment description"
}
```

### POST /api/payments/{id}/process
Process a pending payment. Simulates payment gateway interaction.

### GET /api/payments/
List payments with optional status filter.

## Error Codes
- 400: Invalid payment data
- 402: Insufficient funds
- 404: Payment not found
- 500: Internal server error (database, configuration)
- 502: Payment gateway unavailable
- 504: Payment gateway timeout

## Dependencies
- Database: PostgreSQL (connection pool: HikariCP)
- External: Payment Gateway API (api.payprocessor.com)
- Internal: account-service (balance validation)
- Internal: authentication-service (token validation)

## Health Check
GET /health — Returns service status and dependency health.

## Metrics
- payment.initiated.count
- payment.completed.count
- payment.failed.count
- payment.processing.duration
- payment.gateway.latency
- payment.error.rate

## Configuration
- db.pool.maxSize: 50 (default)
- payment.gateway.timeout: 30000ms
- payment.gateway.retries: 3
- circuit.breaker.threshold: 5 failures in 60s
