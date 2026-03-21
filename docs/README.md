# BookRover — Docs

Project documentation — AWS setup guides, runbooks, and how-to guides.

## Contents (to be created in Phase 4)

- `aws-setup-guide.md` — Step-by-step AWS Console setup for all services.
- `local-dev-guide.md` — How to run the app locally for development.
- `deployment-guide.md` — How to deploy backend and frontend to AWS.
- `runbook.md` — Operational runbook (what to do if something breaks).

---

## Local Dev — DynamoDB Options (notes for local-dev-guide.md)

The app requires a local DynamoDB substitute when developing and testing on your laptop.
There are two options depending on what's available on your machine:

### Option A: moto Server Mode (no Docker needed — use this first)

Recommended when Docker Desktop is not yet installed or not permitted.

```powershell
pip install "moto[server]"
moto_server -p 8001
```

- Starts a DynamoDB-compatible HTTP server at `http://localhost:8001`.
- Pure Python — no Docker, no admin permissions needed.
- Data is in-memory only: resets when the process stops (fine for development).
- Set `DYNAMODB_ENDPOINT_URL=http://localhost:8001` in your `.env.dev` file.

### Option B: DynamoDB Local via Docker (preferred once Docker is available)

Requires Docker Desktop to be installed. Permissions may be needed on a managed laptop.

```powershell
# TODO: Install Docker Desktop first (requires admin/IT permission)
docker run -p 8001:8000 amazon/dynamodb-local
```

- Data persists across restarts (when using a volume mount).
- Identical behavior to real AWS DynamoDB.
- Set `DYNAMODB_ENDPOINT_URL=http://localhost:8001` in your `.env.dev` file.

### Switching Between Options

Zero code changes required. Both options use the same DynamoDB API.
Only the `DYNAMODB_ENDPOINT_URL` env variable changes — and it's the same value for both.

### Testing Strategy (no AWS costs)

| Test Type | Tool | AWS Needed? |
|-----------|------|-------------|
| Unit tests | `pytest` + `moto` (in-memory mock) | ❌ No |
| Integration tests | `pytest` + `moto` (in-memory mock) | ❌ No |
| Manual browser testing | React Dev Server + local FastAPI + moto server or DynamoDB Local | ❌ No |
| Final smoke test | Deployed app on AWS | ✅ Yes (one-time, minimal cost) |

99.99% of all development and testing happens on your laptop — no AWS charges incurred.
