# Database Troubleshooting Guide

## Connection Pool Monitoring
- **Healthy**: Connection utilization < 70%
- **Warning**: Connection utilization 70-90%
- **Critical**: Connection utilization > 90%

## Query Performance
- **Normal**: Query latency < 100ms (p95)
- **Degraded**: Query latency 100ms - 1000ms
- **Critical**: Query latency > 1000ms

## Common Database Issues

### Connection Pool Exhaustion
When active connections approach the maximum pool size, new requests
queue and eventually timeout.

**Detection**: `db_connections / db_max_connections > 0.9`
**Resolution**: See runbook: db_connection_exhaustion.md

### Long-Running Queries
Queries running longer than expected can hold connections and locks.

**Detection**: Check `pg_stat_activity` for queries running > 30 seconds
**Resolution**: Identify and optimize slow queries, add appropriate indexes

### Lock Contention
Multiple transactions competing for the same rows.

**Detection**: Check `pg_locks` for blocked queries
**Resolution**: Optimize transaction scope, add row-level locking hints

### Disk Space
Database disk usage approaching limits.

**Detection**: `disk_percent > 85%`
**Resolution**: Vacuum, archive old data, increase disk allocation

## PostgreSQL Health Checks
```sql
-- Active connections
SELECT count(*) FROM pg_stat_activity WHERE state = 'active';

-- Connection utilization
SELECT count(*) * 100.0 / current_setting('max_connections')::int AS utilization
FROM pg_stat_activity;

-- Long running queries
SELECT pid, now() - pg_stat_activity.query_start AS duration, query
FROM pg_stat_activity
WHERE state = 'active' AND now() - query_start > interval '30 seconds';

-- Lock conflicts
SELECT blocked_locks.pid AS blocked_pid,
       blocking_locks.pid AS blocking_pid,
       blocked_activity.query AS blocked_query
FROM pg_locks blocked_locks
JOIN pg_stat_activity blocked_activity ON blocked_activity.pid = blocked_locks.pid
JOIN pg_locks blocking_locks ON blocking_locks.locktype = blocked_locks.locktype;
```
