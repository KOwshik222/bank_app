# Database Schema Migration Safety Procedure

## Guidelines
1. All database migrations must be backwards-compatible (expand-and-contract pattern).
2. Never drop columns or tables in the same release as application code changes.
3. Long-running migrations with table locks (e.g. `ALTER TABLE ... ADD COLUMN ... DEFAULT`) must be performed off-peak or using concurrent index creation.

## Rollback Procedure for Failed Migrations
1. Revert to previous schema revision using Alembic: `alembic downgrade -1`.
2. Verify table locks are released: `SELECT * FROM pg_stat_activity WHERE state = 'active';`.
3. Restart backend service instances.
