# Security Policy

## Supported Versions

BookRover is currently in active development. Security fixes are applied to the
latest version on the `main` branch only.

| Version | Supported |
|---------|-----------|
| main (latest) | ✅ |
| older commits | ❌ |

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

Use GitHub's built-in private vulnerability reporting:

1. Go to the [Security tab](../../security) of this repository.
2. Click **"Report a vulnerability"**.
3. Describe the issue, steps to reproduce, and potential impact.

Reports are received privately. You will receive an acknowledgement within
**48 hours** and a resolution update within **7 days**. If the issue is
confirmed, a fix will be released as soon as possible depending on severity.

## Scope

This policy covers the BookRover application code in this repository:

- `backend/` — FastAPI application and AWS Lambda handler
- `frontend/` — React / TypeScript SPA

It does **not** cover:
- Third-party dependencies (report those to the relevant upstream project)
- The AWS infrastructure configuration (not included in this repository)

## Preferred Languages

Reports in **English** are preferred.
