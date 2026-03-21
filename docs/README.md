# BookRover — Docs

Project documentation — AWS setup guides, runbooks, and how-to guides.

## Contents (to be created in Phase 4)

All guides live inside arc42 section subfolders — never as loose files directly under `docs/`.

| File | Arc42 Section | Purpose |
|------|--------------|---------|
| `08_cross_cutting_concepts/local-dev-guide.md` | Cross-cutting | How to run the app locally for development |
| `08_cross_cutting_concepts/runbook.md` | Cross-cutting | Operational runbook (what to do if something breaks) |
| `07_deployment_view/aws-setup-guide.md` | Deployment | Step-by-step AWS Console setup for all services |
| `07_deployment_view/deployment-guide.md` | Deployment | How to deploy backend and frontend to AWS |

---

## Local Dev — DynamoDB Options (notes for `08_cross_cutting_concepts/local-dev-guide.md`)

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
