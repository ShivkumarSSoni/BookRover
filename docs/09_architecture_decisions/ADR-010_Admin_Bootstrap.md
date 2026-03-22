# ADR-010: Admin Bootstrap via ADMIN_EMAILS Environment Variable

**Status**: Accepted

---

## Context

BookRover requires an Admin role to manage the system — creating bookstores and assigning group leaders. This creates a classic bootstrap problem: the first admin account cannot be created through the application UI, because the UI requires an existing admin to grant that access.

Additionally, BookRover is an **open-source, self-hostable application**. Any operator who deploys the application to their own AWS account must be able to designate themselves as admin without depending on the original author or any external system.

Three requirements must be satisfied simultaneously:

1. An admin must exist before any other user can be usefully onboarded.
2. Admin designation must not be possible through any code path accessible to end users.
3. Any operator who self-hosts BookRover must be able to bootstrap their own admin without code changes.

---

## Options Considered

### Option A — First-registered user becomes admin

The very first user to register in a fresh deployment is automatically granted admin access.

**Rejected.** A race condition exists: anyone who reaches the registration endpoint first becomes admin. In a cloud deployment, this window is open from the moment the Lambda is first invoked. Unacceptable for a multi-tenant or self-hosted application.

### Option B — Admin record seeded by a migration script

A one-time script inserts an admin record into DynamoDB, run manually by the operator before the app is used.

**Rejected.** Requires a separate operational step outside the normal deployment flow, with no enforcement mechanism. Easy to forget, and the script itself would need to handle credentials and database access — adding complexity and another attack surface. Also requires documentation to be followed correctly for every self-hosted deployment.

### Option C — ADMIN_EMAILS environment variable (chosen)

Admin identity is declared as a comma-separated list of email addresses in a Lambda environment variable (`ADMIN_EMAILS`). The `GET /me` endpoint checks this variable before checking DynamoDB. If the authenticated user's email is in `ADMIN_EMAILS`, the response includes `role: admin` — regardless of any database record.

**Accepted.** See rationale below.

---

## Decision

Use `ADMIN_EMAILS` as a Lambda environment variable to designate operators with admin access. The backend `GET /me` endpoint checks this variable as the first step in role resolution.

---

## Rationale

**Security:** Lambda environment variables are only modifiable by the AWS account owner via the AWS Console, CLI, or IaC tooling. No application code path, no user action, and no API endpoint can alter them. This makes `ADMIN_EMAILS` as secure as the AWS account itself — which is already the trust boundary for the entire deployment.

**Self-hosting:** Any operator who deploys BookRover to their own AWS account sets `ADMIN_EMAILS` to their own email. No communication with the original author is required. The operator is fully autonomous.

**Simplicity:** No database migration, no seed script, no one-time setup endpoint. The operator sets one environment variable and logs in. That is the entire bootstrap procedure.

**Auditability:** Admin identity is visible in the Lambda configuration, not buried in a database record. Any change to admin designation requires a deliberate infrastructure action, which is logged in AWS CloudTrail.

**Multi-instance isolation:** Each self-hosted deployment has its own `ADMIN_EMAILS` in its own Lambda. There is no shared admin state between deployments.

---

## Role Resolution Order in GET /me

```
1. Check ADMIN_EMAILS env var
   → email found: return { roles: ["admin"] }

2. Check bookrover-group-leaders-{env} DynamoDB table
   → email found: return { roles: ["group_leader"], group_leader_id: "..." }

3. Check bookrover-sellers-{env} DynamoDB table
   → email found: return { roles: ["seller"], seller_id: "..." }

4. Email found in both group_leaders and sellers tables
   → return { roles: ["group_leader", "seller"], ... }

5. Email not found anywhere
   → return { roles: [] }  (new user — prompt to register as seller)
```

---

## Trade-offs Accepted

- **Admin is not auditable in DynamoDB.** Admin grants are visible in Lambda config and CloudTrail, but not queryable via the application's own data model. Acceptable for a small-scale operator role that rarely changes.
- **Changing admin emails requires a Lambda environment variable update.** This is intentional — it requires a deliberate infrastructure action, not an in-app UI click.
- **No admin UI to manage other admins.** If the operator wants to add a second admin, they edit `ADMIN_EMAILS` directly. This is acceptable given the expected operational scale.

---

## Consequences

- `config.py` must expose `ADMIN_EMAILS` as a `List[str]` setting via `pydantic-settings`.
- `GET /me` must check `ADMIN_EMAILS` before any DynamoDB lookup.
- `backend/.env.example` must include `ADMIN_EMAILS=your-email@example.com` with a clear comment.
- The operator guide ([operator_guide.md](../07_deployment_view/operator_guide.md)) documents the bootstrap procedure for all operators.
- `APP_ENV=dev` enables `POST /dev/mock-token` for local testing without Cognito. This endpoint must be explicitly disabled when `APP_ENV=prod`.
