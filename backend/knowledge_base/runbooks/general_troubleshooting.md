# Memory Leak Investigation — Runbook

## Symptoms
- Heap memory usage growing steadily over time
- Increasing GC pause times
- OutOfMemoryError in application logs
- Service restarts every few hours
- Response time degradation over time

## Diagnosis Steps
1. Check memory usage trend (should be sawtooth, not steadily increasing)
2. Review GC logs for overhead percentage
3. Capture heap dump if possible
4. Check for object retention in caches or collections
5. Review recent code changes for resource handling

## Common Causes
- **Unclosed resources**: Database connections, HTTP clients, file handles not closed
- **Cache without eviction**: Growing caches without TTL or size limits
- **Event listener accumulation**: Listeners registered but never removed
- **Static collections**: Collections that grow but are never cleared
- **Third-party library leak**: Bug in dependency library

## Remediation
1. **Immediate**: Restart the affected service
2. **Short-term**: Increase heap size if possible (JVM -Xmx)
3. **Investigation**: Analyze heap dump for largest retained objects
4. **Fix**: Identify and fix the leak source
5. **Prevention**: Add memory usage alerts and periodic restart schedule

## Related Incidents
- INC-6543: Memory leak in payment-service due to unclosed HTTP connections
- INC-7890: Cache growth in customer-service without TTL

# Kafka Consumer Failure — Runbook

## Symptoms
- Consumer lag growing (messages not being processed)
- Transaction events not appearing
- Notifications not being sent
- Consumer group rebalance errors in logs

## Diagnosis Steps
1. Check consumer group status and lag
2. Verify Kafka broker connectivity
3. Check for deserialization errors
4. Review consumer configuration
5. Check for partition reassignment issues

## Common Causes
- **Broker unavailable**: Kafka broker crashed or unreachable
- **Deserialization error**: Message schema changed incompatibly
- **Consumer crash**: Application error causing consumer to stop
- **Network partition**: Consumer cannot reach broker
- **Topic deletion**: Topic accidentally deleted or recreated

## Remediation
1. **If broker issue**: Verify broker health, restart if needed
2. **If deserialization**: Fix schema, skip bad messages
3. **If consumer crash**: Restart consumer application
4. **If network**: Check network connectivity and DNS
5. **Use**: `retry_failed_test_job` to reprocess failed messages

# Third-Party API Outage — Runbook

## Symptoms
- External API calls returning 503/504 errors
- Circuit breaker opening for external endpoints
- Specific payment methods failing (e.g., card payments)
- Internal services healthy but external calls failing

## Diagnosis Steps
1. Check external API status page
2. Test connectivity to external endpoint
3. Verify circuit breaker status
4. Check if fallback processor is available
5. Review error patterns (all failing vs. intermittent)

## Remediation
1. **Immediate**: Switch to backup payment processor if available
2. **Communication**: Notify customers of payment delays
3. **Monitoring**: Set up status page polling for the external service
4. **Fallback**: Queue failed transactions for retry when service recovers
