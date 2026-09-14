# Historical Incident Report: INC-5219

## Incident Details
- **Incident Number**: INC-5219
- **Date**: 2026-07-19
- **Severity**: HIGH
- **Affected Service**: payment-service
- **Duration**: 52 minutes
- **Status**: RESOLVED

## Symptom
Payment API latency spiked from an average of 120ms to over 28,000ms. Clients experienced timeouts, and checkout transactions failed repeatedly.

## Root Cause
Upstream clearing house payment gateway was experiencing degraded connectivity across transatlantic fiber trunks, causing 30-second socket read timeouts on synchronous HTTP calls.

## Remediation Applied
- Activated the circuit breaker on `payment-service` to immediately fast-fail degraded calls.
- Switched payment route to secondary domestic payment processor.
- Reduced HTTP client read timeout from 30s to 4s to prevent connection pooling saturation.

## Lessons Learned
Never allow external API calls without a strict circuit breaker and tight connect/read timeouts.
