# Historical Incident Report: INC-6240

## Incident Details
- **Incident Number**: INC-6240
- **Date**: 2026-09-08
- **Severity**: CRITICAL
- **Affected Service**: payment-service
- **Duration**: 18 minutes
- **Status**: RESOLVED

## Symptom
Immediately after continuous deployment release `v2.8.0`, error rate spiked from 0.2% to 41.5%. Client requests returned `500 Internal Server Error: connection pool timeout`.

## Root Cause
Configuration change committed in deployment mistakenly set `db_max_connections: 5` instead of `db_max_connections: 500` in the Helm values file.

## Remediation Applied
- Executed immediate deployment rollback to previous stable version `v2.7.1`.
- Verified configuration restored `db_max_connections: 500`.
- Errors dropped to zero within 45 seconds of pod restart.
