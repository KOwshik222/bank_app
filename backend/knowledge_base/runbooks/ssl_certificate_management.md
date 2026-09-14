# SSL Certificate Management — Runbook

## Symptoms
- TLS/SSL handshake errors in logs
- "Certificate expired" or "SSLHandshakeException" errors
- Downstream services unable to connect to the affected service
- Authentication failures across all services

## Diagnosis Steps
1. Check certificate expiry: `openssl s_client -connect service:443 | openssl x509 -noout -dates`
2. Review certificate management system for renewal status
3. Check certificate auto-renewal cron job logs
4. Verify certificate chain completeness

## Common Causes
- **Auto-renewal failure**: Certificate renewal cron job failed silently
- **Manual certificate**: Certificate was manually installed and renewal was forgotten
- **Certificate provider outage**: Let's Encrypt or internal CA unavailable during renewal
- **DNS change**: Domain validation failed due to DNS configuration change

## Remediation
1. **Immediate**: Rotate certificate using `rotate_test_certificate` tool
2. **Verify**: Check all dependent services can connect after rotation
3. **Post-incident**: Set up certificate expiry alerting (30/14/7 day warnings)
4. **Prevention**: Ensure auto-renewal is configured and monitored

## Certificate Locations
- authentication-service: /etc/ssl/certs/auth.bank.internal.pem
- payment-service: /etc/ssl/certs/payment.bank.internal.pem
- Internal CA: /etc/ssl/certs/bank-internal-ca.pem

## Related Incidents
- INC-3456: SSL certificate expired on API gateway (resolved by manual rotation)
