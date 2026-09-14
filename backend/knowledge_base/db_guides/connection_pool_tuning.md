# Database Connection Pool Tuning and Configuration Guide

## Architecture
Every microservice connects to the primary PostgreSQL / SQLite database cluster via a localized HikariCP / SQLAlchemy connection pool.

## Configuration Parameters
- `pool_size`: Base number of permanent database connections kept open in the pool. Default: 10.
- `max_overflow`: Maximum number of burst connections above `pool_size` when traffic surges. Default: 20.
- `pool_timeout`: Number of seconds to wait before giving up on obtaining a connection from the pool. Default: 30s.
- `pool_recycle`: Periodically recycle connections to prevent stale TCP sockets. Default: 1800s.

## Symptoms of Connection Pool Sizing Issues
1. `TimeoutError: QueuePool limit of size 10 overflow 20 reached`: Application traffic exceeds total pool capacity (30 concurrent queries).
2. `OperationalError: FATAL: remaining connection slots are reserved for non-replication superuser connections`: Database server `max_connections` reached across all microservice instances.

## Formula for Total Cluster Connections
`Total Connections = (Number of Pods) * (pool_size + max_overflow) + 20 (Admin buffer)`
Ensure this value is always lower than PostgreSQL `max_connections` setting (typically 500 or 1000).
