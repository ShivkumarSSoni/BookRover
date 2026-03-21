# ADR-006: S3 + CloudFront for Frontend Hosting

**Status**: Accepted

---

## Context

The React frontend must be served over HTTPS globally at near-zero cost. Users are on mobile phone browsers — performance and reliability matter.

---

## Options Considered

| Option | Cost | HTTPS | Security | Performance |
|--------|------|-------|----------|-------------|
| S3 static website (public bucket, HTTP) | ~$0 | ❌ HTTP only | Low (public bucket) | No CDN |
| S3 + CloudFront with Origin Access Control | ~$0 | ✅ Enforced | High (private bucket) | ✅ Global CDN |
| EC2 / ECS with Nginx | ~$15–20/month | Manual cert management | Medium | No built-in CDN |

---

## Decision

S3 (private bucket) + CloudFront distribution with Origin Access Control (OAC).

---

## Rationale

- S3 direct static website hosting is HTTP only — unacceptable for a production app. CloudFront enforces HTTPS with automatic HTTP → HTTPS redirect.
- OAC keeps the S3 bucket fully private — CloudFront is the only authorized accessor. No accidental public exposure of bucket contents.
- CloudFront delivers assets from the nearest edge location to the user — critical for mobile users in India.
- Custom error pages for 403/404 → `index.html` (200) are required for React Router client-side navigation to work correctly.
- Cost is effectively $0 for low traffic (well within CloudFront free tier).

---

## Trade-offs Accepted

- Slightly more involved setup than S3 static hosting alone (OAC configuration, cache behaviors, error pages). Cost is paid once at setup time.
