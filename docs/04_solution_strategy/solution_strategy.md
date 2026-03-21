# arc42 — Section 4: Solution Strategy

## 4.1 Key Architecture Decisions (Summary)

Detailed rationale for each decision is in `../architecture_decisions/`. This section provides the high-level strategy.

---

## 4.2 Technology Decisions

### Backend — FastAPI (Python)

- FastAPI provides automatic OpenAPI documentation, Pydantic validation, and async request handling out of the box.
- Python is the developer's chosen language and is natively supported on AWS Lambda.
- **Mangum** adapts FastAPI (ASGI) to the AWS Lambda + API Gateway event format with zero code changes.

### Frontend — React + TypeScript + Tailwind CSS

- React is component-based — ideal for a multi-page app with shared UI elements (nav bar, cards, buttons).
- TypeScript catches type errors at compile time, reducing bugs in data handled between API and UI.
- Tailwind CSS enables mobile-first responsive design without writing custom CSS files.

### Database — DynamoDB (NoSQL)

- No provisioned capacity — on-demand billing means $0 cost at low usage.
- Serverless — no database server to manage or patch.
- Native AWS service — integrates directly with Lambda via boto3, no connection pooling required.
- Trade-off accepted: no joins, no transactions across tables — mitigated by careful data model design (snapshots in SaleItem, embedded lists).

### Hosting — Serverless (Lambda + API Gateway + S3 + CloudFront)

- **No EC2, no containers** — no idle server cost, no patching, no scaling configuration.
- Lambda scales automatically from 0 to N concurrent requests.
- S3 + CloudFront for the React frontend: near-zero cost, global CDN, automatic HTTPS.
- API Gateway HTTP API is simpler and cheaper than REST API for this use case.

---

## 4.3 Architectural Style

**Multi-tier serverless web application:**

```
Presentation Tier   →   React SPA (S3 + CloudFront)
API Tier            →   FastAPI on Lambda (API Gateway)
Data Tier           →   DynamoDB (7 tables)
```

The backend follows a **layered architecture**:

```
HTTP Request
    ↓
Router (FastAPI route handler)       — validates input, returns HTTP response
    ↓
Service (business logic)             — applies business rules, orchestrates repositories
    ↓
Repository (data access)             — the only layer that calls DynamoDB
    ↓
DynamoDB
```

This separation ensures:
- Business logic is testable without a database (mock the repository).
- DynamoDB access patterns are centralized in one layer (easy to change or optimize).
- Routers stay thin — no logic, only HTTP concerns.

---

## 4.4 Quality Goal → Strategy Mapping

| Quality Goal | Strategy |
|-------------|---------|
| **Simplicity** | No dropdowns on New Buyer page; `+`/`-` tap buttons; large touch targets (min 44px); clear labels |
| **Mobile-First** | Tailwind CSS mobile-first responsive; `max-w-lg mx-auto` containers; min font-size 16px |
| **Correctness** | Pydantic validation on all inputs; atomic DynamoDB `UpdateExpression` for inventory decrements; quantity checks before sale save |
| **Cost-Minimal** | Serverless-only architecture; on-demand DynamoDB; S3+CloudFront for static hosting |
| **Maintainability** | Layered backend; SOLID principles; ≥80% test coverage; Conventional Commits; feature branches |

---

## 4.5 Local Development Strategy

To support development and testing without AWS charges, the local stack mirrors production:

| Production | Local Equivalent |
|-----------|-----------------|
| Lambda + API Gateway | `uvicorn` running FastAPI on `localhost:8000` |
| DynamoDB | `moto_server` on `localhost:8001` (no Docker needed) or DynamoDB Local via Docker |
| S3 + CloudFront | React Dev Server on `localhost:3000` |
| Cognito | Role-selector placeholder (dev mode only) |

All automated tests (unit + integration) use `moto` in-memory mocking — no running process needed.
