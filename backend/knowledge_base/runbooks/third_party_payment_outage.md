# Third-Party Payment Gateway Outage — Runbook

## Symptoms
- Outbound API calls to external payment processor failing with HTTP 502/503/504
- Error logs in `payment-service`: `GatewayTimeoutException: External provider unreachable after 10000ms`
- Payment transaction success rate drops below 70%

## Root Causes
- Upstream network failure at payment processor data center
- Degraded API performance on external payment partner side
- Firewall or TLS certificate handshake problem at partner edge

## Remediation Workflow
1. **Enable Circuit Breaker**: Trip the circuit breaker for the primary gateway to immediately stop hammering the degraded upstream.
2. **Switch Gateway Route**: Reroute outgoing credit/debit card authorizations to secondary provider (e.g. Stripe to Adyen / CyberSource).
3. **Queue Asynchronous Payments**: Switch non-instant payments to scheduled ACH batching queue.
4. **Notify Incident Commander**: Post status update to internal banking incident Slack/Teams channel.
