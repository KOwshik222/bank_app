# Canary Deployment and Release Safety Guide

## Principles
1. Never deploy directly to 100% of production traffic
2. Automated health validation at 10%, 25%, 50%, and 100% phases
3. Automatic rollback if error rate increases by > 1.0% above baseline

## Rollback Triggers
- HTTP 5xx error rate > 2% for 3 consecutive minutes
- P99 latency increases by > 100ms compared to pre-deployment baseline
- Database connection pool utilization exceeds 85%
- Uncaught exceptions spike in application log streams

## Emergency Rollback Execution
Run: `kubectl rollout undo deployment/payment-service`
Or invoke AI remediation action: `rollback_service(service="payment-service")`.
Verify health check returns HTTP 200 within 60 seconds.
