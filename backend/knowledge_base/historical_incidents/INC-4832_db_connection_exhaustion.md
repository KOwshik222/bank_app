# Historical Incident Report: INC-4832

## Incident Details
- **Incident Number**: INC-4832
- **Date**: 2026-06-15
- **Severity**: CRITICAL
- **Affected Service**: payment-service
- **Duration**: 45 minutes
- **Status**: RESOLVED

## Symptom
Payment Service returning HTTP 500 errors. Error rate spiked to 28%.
Database connection pool exhausted.

## Timeline
- 14:15 — Deployment of payment-service v2.6.0 with configuration change
- 14:27 — First HTTP 500 errors observed
- 14:31 — Error rate exceeds 10%
- 14:35 — Incident INC-4832 created
- 14:38 — AI investigation started
- 14:42 — Root cause identified: connection pool maxSize changed from 50 to 10
- 14:45 — Rollback approved by incident manager
- 14:48 — Configuration rolled back to maxSize=50
- 14:52 — Error rate returns to normal
- 15:00 — Incident resolved

## Root Cause
The deployment of v2.6.0 included a configuration change that reduced the database
connection pool maxPoolSize from 50 to 10. Under normal load (~40 concurrent connections),
this caused connection pool exhaustion.

## Evidence
- DB connections: 10/10 (100% utilization)
- Error logs: "HikariPool-1 — Connection is not available, request timed out after 30000ms"
- Deployment record: v2.6.0 deployed at 14:15 with config change "maxPoolSize: 50 → 10"
- API latency: p95 increased from 150ms to 30000ms

## Resolution
Rolled back connection pool configuration to maxPoolSize=50.

## Lessons Learned
- Configuration changes should be reviewed for impact on resource limits
- Connection pool size alerts should be set at 80% utilization
- Deployment pipeline should validate configuration changes against minimum thresholds

## Similar Incidents
- INC-2103: Similar DB connection exhaustion due to traffic spike (2026-03-10)
