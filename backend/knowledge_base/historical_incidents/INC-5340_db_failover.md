# Historical Incident Report: INC-5340

## Incident Details
- **Incident Number**: INC-5340
- **Date**: 2026-08-05
- **Severity**: CRITICAL
- **Affected Service**: payment-service, account-service
- **Duration**: 21 minutes
- **Status**: RESOLVED

## Symptom
All microservices reported total inability to connect to PostgreSQL: `Connection refused: port 5432`. No user transactions could proceed.

## Root Cause
Hardware disk controller failure on the primary database VM triggered a sudden kernel panic and ungraceful shutdown.

## Remediation Applied
- Executed emergency failover promoting hot-standby replica node `pg-replica-01` to new primary.
- Updated DNS virtual IP (VIP) to point to the promoted replica.
- Restarted application connection pools across all microservices.

## Verification
- Connection checks succeeded across all 6 microservices.
- Transaction backlog drained in 4 minutes.
