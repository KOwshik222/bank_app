# Network Latency and API Gateway Outage — Runbook

## Symptoms
- Outbound HTTP requests timing out (> 5000ms)
- 504 Gateway Timeout returned to upstream clients
- TCP connection reset by peer in edge proxies
- Sudden drop in request throughput across multiple services

## Diagnostic Steps
1. Measure latency to upstream payment gateway: `curl -w "%{time_total}\n" -o /dev/null -s https://gateway.processor.internal/health`
2. Check DNS resolution times across Kubernetes pods
3. Inspect egress NAT gateway bandwidth and packet drop metrics
4. Validate circuit breaker status in Payment Service

## Remediation Steps
1. Trip the circuit breaker manually to activate local mock fallback
2. Switch payment traffic to secondary payment provider
3. Escalate to cloud network operations team if ISP transit link is degraded
