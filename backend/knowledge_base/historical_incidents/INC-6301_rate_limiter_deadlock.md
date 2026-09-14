# Historical Incident Report: INC-6301

## Incident Details
- **Incident Number**: INC-6301
- **Date**: 2026-09-10
- **Severity**: HIGH
- **Affected Service**: authentication-service
- **Duration**: 24 minutes
- **Status**: RESOLVED

## Symptom
Login API requests stalled and threw HTTP 429 Too Many Requests even for non-rate-limited legitimate customer sessions.

## Root Cause
Redis token bucket cluster keys expired with incorrect TTL format, causing rate limiting middleware to default to rejecting all incoming traffic.

## Remediation Applied
- Flushed rate limiting key namespace: `redis-cli KEYS "ratelimit:*" | xargs redis-cli DEL`.
- Patched rate limiter fallback logic to allow traffic in fail-open mode during Redis degradation.
