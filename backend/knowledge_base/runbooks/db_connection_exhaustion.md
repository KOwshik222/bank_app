# Database Connection Pool Exhaustion — Runbook

## Symptoms
- HTTP 500 errors from services using the database
- "Connection pool exhausted" or "Connection is not available" in application logs
- `db_connections` metric approaching `db_max_connections`
- Increasing API latency
- Rising error rate

## Diagnosis Steps
1. Check current connection count: `SELECT count(*) FROM pg_stat_activity;`
2. Check connection pool metrics in application monitoring
3. Review connection pool configuration (HikariCP maxPoolSize)
4. Identify long-running queries: `SELECT pid, duration, query FROM pg_stat_activity WHERE state = 'active' ORDER BY duration DESC;`
5. Check for connection leaks in application logs
6. Review recent configuration changes

## Common Causes
- **Configuration change**: maxPoolSize reduced or timeout shortened
- **Connection leak**: Application code not properly closing connections
- **Long-running queries**: Queries holding connections for extended periods
- **Traffic spike**: Sudden increase in concurrent requests
- **Database performance degradation**: Slow queries causing connection buildup

## Remediation
1. **Immediate**: Restart the affected service to reset connection pool
2. **Short-term**: Increase `maxPoolSize` configuration if below recommended (typically 20-50 per instance)
3. **If caused by config change**: Rollback the configuration to previous values
4. **If connection leak**: Deploy fix for leaked connections
5. **If long-running queries**: Terminate blocking queries and optimize

## Configuration Reference
- Default maxPoolSize: 50
- Recommended for payment-service: 50-100
- Connection timeout: 30000ms
- Idle timeout: 600000ms

## Related Incidents
- INC-4832: Database connection exhaustion due to config change (resolved by rollback)
- INC-6721: Connection leak in transaction-service v1.4.0 (resolved by hotfix)
