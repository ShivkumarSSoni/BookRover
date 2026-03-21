# ADR-008: moto_server as Local DynamoDB Substitute

**Status**: Accepted (temporary — will be replaced by DynamoDB Local once Docker Desktop is available)

---

## Context

Local development and manual browser testing require a running DynamoDB-compatible service on the developer's laptop. AWS DynamoDB Local (the official emulator) requires Docker Desktop, which requires IT department approval on the developer's laptop.

---

## Options Considered

| Option | Requires Docker | Data Persistence | Setup |
|--------|----------------|-----------------|-------|
| Real AWS DynamoDB (dev tables) | No | Yes | Costs money on every call; not suitable for active development |
| DynamoDB Local (official AWS Docker image) | Yes | Optional (volume) | Requires Docker Desktop (pending IT approval) |
| `moto_server` (Python pip package) | No | In-memory only (resets on stop) | `pip install "moto[server]"` + `moto_server -p 8001` |

---

## Decision

Use `moto_server` as an interim local DynamoDB substitute until Docker Desktop is permitted.

---

## Rationale

- `moto_server` exposes the same DynamoDB HTTP API as the real service and DynamoDB Local.
- Pure Python — no admin or Docker permissions required.
- Identical `DYNAMODB_ENDPOINT_URL=http://localhost:8001` config as DynamoDB Local — zero code changes when switching.
- Automated unit and integration tests use `moto` in-memory directly (no running process needed at all).

---

## Trade-offs Accepted

- In-memory only — all data is lost when `moto_server` stops. Acceptable for development sessions; tests are fully automated and do not rely on persisted state.

---

## Resolution Plan

When Docker Desktop is approved: switch to `amazon/dynamodb-local` Docker image. `DYNAMODB_ENDPOINT_URL` stays the same. No code changes required.
