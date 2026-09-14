# Historical Incident Report: INC-5788

## Incident Details
- **Incident Number**: INC-5788
- **Date**: 2026-09-01
- **Severity**: CRITICAL
- **Affected Service**: transaction-service, notification-service
- **Duration**: 42 minutes
- **Status**: RESOLVED

## Symptom
Kafka producer errors flooded application logs: `TimeoutException: Failed to update metadata after 60000 ms`. Financial settlement messages stalled.

## Root Cause
One of the 3 Kafka broker nodes experienced an EBS storage detachment on AWS due to an underlying hypervisor maintenance action. Partition leaders were unable to replicate.

## Remediation Applied
- Rebalanced partition leadership across remaining healthy brokers.
- Attached new EBS volume and restarted Kafka broker instance.
- Verified in-sync replicas (ISR) count returned to 3/3 across all topics.
