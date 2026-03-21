# ADR-005: Mangum as Lambda Adapter for FastAPI

**Status**: Accepted

---

## Context

FastAPI is an ASGI (Asynchronous Server Gateway Interface) framework. AWS Lambda expects a specific `handler(event, context)` function signature from API Gateway proxy events. These two interfaces are incompatible without an adapter layer.

---

## Options Considered

| Option | Approach | Complexity |
|--------|----------|-----------|
| Write a custom Lambda handler | Manually parse API Gateway events into FastAPI Request objects | High — duplicates routing logic |
| Flask + aws-wsgi | Use WSGI adapter; lose async support | Medium |
| FastAPI + Mangum | Thin adapter translates ASGI ↔ Lambda event format | Low |

---

## Decision

Use Mangum as a thin, zero-business-logic adapter layer.

---

## Rationale

- Mangum translates API Gateway proxy events to the ASGI scope format FastAPI expects — one line of code: `handler = Mangum(app)`.
- Zero changes to FastAPI application code — the same `app` object runs locally via `uvicorn` and in Lambda via Mangum. No dual codebases.
- Widely adopted, actively maintained, and well documented.
- Supports both API Gateway HTTP API and REST API event formats.

---

## Trade-offs Accepted

- Adds one additional dependency. Risk is minimal given the library's maturity and focused scope (it does exactly one thing).
