# ADR-001: Serverless Architecture (Lambda + API Gateway)

**Status**: Accepted

---

## Context

The app serves a small friend group with unpredictable, low traffic. Cost must be near $0. No dedicated operations team exists to manage servers.

---

## Options Considered

| Option | Monthly Cost (idle) | Complexity |
|--------|-------------------|------------|
| EC2 (t3.micro) | ~$8–10/month | Medium |
| ECS Fargate | ~$15–20/month | High |
| Lambda + API Gateway HTTP API | $0 (free tier) | Low |

---

## Decision

Lambda + API Gateway HTTP API.

---

## Rationale

- Pay-per-request pricing means $0 cost when nobody is using the app.
- Lambda scales automatically from 0 to N — no Auto Scaling Groups to configure.
- API Gateway HTTP API is simpler and 70% cheaper than REST API for this use case.
- No server infrastructure to patch, manage, or monitor.
- Mangum adapts FastAPI (ASGI) to Lambda events with zero changes to application code.

---

## Trade-offs Accepted

- Lambda cold starts (~1 second for Python + FastAPI). Acceptable for a non-latency-critical internal tool used by a small friend group.
- No persistent in-memory state between invocations. All state lives in DynamoDB (by design).
