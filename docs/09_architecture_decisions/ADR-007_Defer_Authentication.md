# ADR-007: Defer Authentication to Phase 6

**Status**: Superseded — Resolved in Phase 6

---

## Context

The app requires Gmail/Google OAuth authentication via AWS Cognito for production use. Setting this up early adds significant complexity (Cognito User Pool, Identity Provider federation, JWT validation middleware, frontend auth flows) before any core features exist or are validated.

---

## Options Considered

| Option | When | Risk |
|--------|------|------|
| Build auth first, then features | Start of project | High — delays all feature development; auth may need rework once feature scope is clear |
| Build features first, add auth in Phase 6 | Phase 6 | Medium — app is unprotected until Phase 6; mitigated by keeping URL private |
| No auth ever (trust-based for friends) | Never build it | High — unacceptable for any real-world deployment |

---

## Decision

Build all features first using a role-selector placeholder in dev mode. Add Cognito + Google OAuth in Phase 6 as a dedicated authentication layer.

---

## Rationale

- Separating feature development from auth allows each to be built and tested cleanly without dependencies between them.
- All API endpoints are designed with authentication in mind — `seller_id` flows through path parameters exactly as it would with JWT claims. Plugging in Cognito will not require restructuring routes.
- The app will not be publicised until authentication is in place.

---

## Risk

The app is unprotected until Phase 6. Mitigation: the CloudFront URL is not shared publicly until auth is complete.

---

## Resolution

**Implemented in Phase 6:** AWS Cognito Email OTP (passwordless). Users enter their email; Cognito sends a 6-digit one-time code; the frontend verifies it via the Amplify SDK and receives a signed RS256 JWT (IdToken). All backend endpoints verify the JWT on every request via `CognitoJWTVerifier`. No Google/OAuth federation — email is the identity provider. The `POST /dev/mock-token` endpoint (dev only) is explicitly blocked when `APP_ENV=prod`.
