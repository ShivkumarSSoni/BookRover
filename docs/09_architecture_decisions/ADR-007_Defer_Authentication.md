# ADR-007: Defer Authentication to Phase 6

**Status**: Accepted (temporary — will be resolved in Phase 6)

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

## Resolution Plan

Phase 6: AWS Cognito User Pool + Google Identity Provider + JWT authorizer on API Gateway. Frontend login via Cognito Hosted UI or custom React login flow.
