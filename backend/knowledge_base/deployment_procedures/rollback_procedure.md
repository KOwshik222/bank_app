# Deployment Rollback Procedure

## When to Rollback
- Error rate exceeds 5% within 15 minutes of deployment
- Service health check failing after deployment
- Critical functionality broken (payments, authentication)
- Configuration mismatch errors in logs

## Rollback Steps
1. Confirm the incident correlates with the deployment timeline
2. Identify the previous stable version
3. Execute rollback using `rollback_deployment` tool
4. Monitor error rate and service health for 10 minutes
5. Verify core functionality (payments, authentication, transactions)
6. Update incident with rollback status

## Rollback Tool Usage
```
rollback_deployment(
    service="payment-service",
    target_version="v2.7.1",
    reason="Error rate spike after v2.8.0 deployment"
)
```

## Post-Rollback Verification
- Error rate returns to baseline (< 1%)
- API latency returns to normal (< 200ms p95)
- Service health check passing
- No new error patterns in logs

## Deployment History
Deployment records are maintained in the deployment management system.
Always check `get_recent_deployments` to identify correlation between
deployment timestamp and incident start time.

## Related Incidents
- INC-8123: Bad configuration in payment-service v2.6.0 (rolled back to v2.5.1)
- INC-9456: Memory leak introduced in account-service v2.0.0 (rolled back to v1.9.1)
