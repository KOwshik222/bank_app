# Authentication Service API Documentation

## Service Overview
The Authentication Service handles user logins, JWT generation, password validation, role enforcement, and token revocation.

## Security Architecture
- Protocol: OAuth2 / OpenID Connect compliant JWT tokens
- Signature Algorithm: HS256 / RS256 with key rotation every 90 days
- Token Expiry: Access tokens 60 minutes, Refresh tokens 7 days

## Endpoints

### POST /api/auth/login
Authenticate with username/password and receive bearer token.

### POST /api/auth/refresh
Refresh expired access token using valid refresh token.

### POST /api/auth/revoke
Immediately revoke token in event of compromised credentials.

## Failure Modes & Common Errors
- `401 Unauthorized`: Invalid credentials or expired token signature.
- `SSL Handshake Exception`: TLS certificate expired on auth ingress gateway.
