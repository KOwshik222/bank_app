# Customer Service API Documentation

## Service Overview
The Customer Service manages synthetic customer identities, KYC statuses, risk scores, contact information, and address records.

## Endpoints
### GET /api/customers/
List all customers with pagination and name search.

### GET /api/customers/{customer_id}
Get full profile including KYC verification status and risk profile.

### PATCH /api/customers/{customer_id}
Update phone, address, or email records.
