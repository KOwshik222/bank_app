# Historical Incident Report: INC-5102

## Incident Details
- **Incident Number**: INC-5102
- **Date**: 2026-07-02
- **Severity**: CRITICAL
- **Affected Service**: authentication-service
- **Duration**: 28 minutes
- **Status**: RESOLVED

## Symptom
Downstream microservices (payment-service, account-service) began logging TLS certificate validation failures: `javax.net.ssl.SSLHandshakeException: PKIX path validation failed`. Users were unable to log in and received HTTP 500 across mobile and web banking portals.

## Investigation Evidence
- Logs from payment-service indicated: `SSL handshake failed: certificate has expired on 2026-07-02T00:00:00Z`.
- OpenSSL verification: `openssl s_client -connect auth-internal:8443` confirmed the ingress secret expired 4 hours earlier.
- Automated cert-manager job had failed due to an invalid Let's Encrypt / internal CA DNS challenge configuration.

## Root Cause
The TLS/SSL certificate protecting the internal mutual TLS authentication endpoint expired, preventing inter-service communication.

## Remediation Applied
- Rotated the expired certificate using the internal certificate authority CLI tool.
- Restarted `authentication-service` pods to reload the key store.
- Added Prometheus alert for certificate expiry < 14 days.

## Verification
- Health checks for `authentication-service` returned HTTP 200.
- User login success rate returned to 99.8%.
