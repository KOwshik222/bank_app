# Database Deadlock Resolution — Runbook

## Symptoms
- `DeadlockDetectedException: Process 412 waiting for ExclusiveLock on relation ...` in application logs
- Payment processing transactions abruptly aborted
- Spike in 409 Conflict / 500 Internal Server Error responses
- Elevated transaction retry counts

## Diagnosis
1. Query active locks:
   ```sql
   SELECT blocked_locks.pid AS blocked_pid, blocking_locks.pid AS blocking_pid,
          blocked_activity.query AS blocked_statement, blocking_activity.query AS current_statement_in_blocking_process
   FROM  pg_catalog.pg_locks blocked_locks
   JOIN pg_catalog.pg_stat_activity blocked_activity ON blocked_activity.pid = blocked_locks.pid
   JOIN pg_catalog.pg_locks blocking_locks ...
   ```
2. Identify concurrent updates affecting accounts in opposite locking order (e.g. Tx A locks Acc 1 then Acc 2; Tx B locks Acc 2 then Acc 1).

## Remediation
1. Terminate long-running blocking query: `SELECT pg_cancel_backend(blocking_pid);`
2. Ensure application code consistently sorts account IDs before locking in multi-account transfers.
