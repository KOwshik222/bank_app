# Historical Incident Report: INC-5491

## Incident Details
- **Incident Number**: INC-5491
- **Date**: 2026-08-14
- **Severity**: HIGH
- **Affected Service**: payment-service
- **Duration**: 34 minutes
- **Status**: RESOLVED

## Symptom
Payment Service CPU utilization shot up to 98% across all container instances. Request latency degraded from 80ms to over 6,000ms.

## Root Cause
Catastrophic backtracking in regular expression used for IBAN account number validation:
`^([A-Z]{2}[0-9]{2})+[A-Z0-9]+$` triggered exponential time complexity on malformed user inputs.

## Remediation Applied
- Replaced vulnerable regex with linear pre-compiled pattern.
- Added 50ms regex evaluation timeout guard.
- Deployed emergency hotfix container tag `v2.7.1`.
