# Historical Incident Report: INC-5620

## Incident Details
- **Incident Number**: INC-5620
- **Date**: 2026-08-22
- **Severity**: HIGH
- **Affected Service**: payment-service
- **Duration**: 75 minutes
- **Status**: RESOLVED

## Symptom
Payment Service pods were being terminated every 4 hours with Kubernetes OOMKilled status (exit code 137). Memory metrics showed continuous linear climb from 300MB to 2048MB container limit.

## Root Cause
An internal transaction telemetry audit cache had no maximum capacity (`cache = {}`) and accumulated transaction payloads indefinitely in memory without eviction.

## Remediation Applied
- Restarted payment service pods to restore operational baseline.
- Replaced unbounded dictionary with LRU cache configured with `maxsize=10000` and TTL eviction of 15 minutes.
- Verified stable memory plateau at 420MB under sustained load test.
