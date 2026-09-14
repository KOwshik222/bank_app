# High CPU Troubleshooting — Runbook

## Symptoms
- CPU utilization consistently above 80%
- Increased response times
- Thread pool exhaustion warnings
- GC pause time increases
- Request queuing

## Diagnosis Steps
1. Check CPU metrics trend in Grafana/monitoring
2. Review thread dump for busy threads
3. Check GC logs for excessive garbage collection
4. Profile the application for hot methods
5. Review recent deployments for CPU-intensive changes
6. Check for traffic spike correlation

## Common Causes
- **Code regression**: Inefficient algorithm introduced in recent deployment
- **Traffic spike**: Unexpected surge in request volume
- **GC pressure**: Excessive object creation causing GC overhead
- **Thread contention**: Lock contention causing CPU spin
- **Resource-intensive operations**: Large report generation, bulk operations

## Remediation
1. **Immediate**: Scale service horizontally (add instances)
2. **If deployment-related**: Rollback to previous version
3. **If traffic spike**: Enable rate limiting
4. **Long-term**: Profile and optimize hot code paths
5. **Emergency**: Restart service to clear state

## Scaling Procedures
- Use `scale_test_service` tool to increase instance count
- Default scaling: 2 → 4 instances
- Maximum instances: 8 per service

## Related Incidents
- INC-5891: CPU spike after payment-service v2.5 deployment (resolved by rollback)
- INC-7234: Black Friday traffic spike (resolved by auto-scaling)
