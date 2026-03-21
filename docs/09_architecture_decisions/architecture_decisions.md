# arc42 — Section 9: Architecture Decisions

Each Architecture Decision Record (ADR) is maintained as a separate file for clarity and manageability.

## ADR Index

| ADR | Title | Status |
|-----|-------|--------|
| [ADR-001](ADR-001_Serverless_Architecture.md) | Serverless Architecture (Lambda + API Gateway) | Accepted |
| [ADR-002](ADR-002_DynamoDB_Over_RDS.md) | DynamoDB over RDS | Accepted |
| [ADR-003](ADR-003_React_TypeScript_Frontend.md) | React + TypeScript + Tailwind CSS for Frontend | Accepted |
| [ADR-004](ADR-004_Multi_Table_DynamoDB_Design.md) | Multi-Table DynamoDB Design | Accepted |
| [ADR-005](ADR-005_Mangum_Lambda_Adapter.md) | Mangum as Lambda Adapter for FastAPI | Accepted |
| [ADR-006](ADR-006_S3_CloudFront_Frontend_Hosting.md) | S3 + CloudFront for Frontend Hosting | Accepted |
| [ADR-007](ADR-007_Defer_Authentication.md) | Defer Authentication to Phase 6 | Accepted (temporary) |
| [ADR-008](ADR-008_Moto_Server_For_Local_Dev.md) | moto_server as Local DynamoDB Substitute | Accepted (temporary) |
| [ADR-009](ADR-009_Strict_Layered_Architecture.md) | Strict Layered Architecture with Abstract Base Classes | Accepted |

## How to Add a New ADR

1. Create a new file: `ADR-0NN_Short_Title.md` in this folder.
2. Use the structure: Status, Context, Options Considered, Decision, Rationale, Trade-offs Accepted.
3. Add a row to the index table above.
4. Reference related ADRs where relevant.

---

## ADR-001: Serverless Architecture (Lambda + API Gateway)

**Status**: Accepted

**Context**: The app serves a small friend group with unpredictable, low traffic. Cost must be near $0.

**Options considered**:
| Option | Monthly Cost (idle) | Complexity |
|--------|-------------------|------------|
| EC2 (t3.micro) | ~$8–10/month | Medium |
| ECS Fargate | ~$15–20/month | High |
| Lambda + API Gateway | $0 (free tier) | Low |

**Decision**: Lambda + API Gateway HTTP API.

**Rationale**: Pay-per-request pricing means $0 cost when nobody is using the app. Lambda scales automatically — no Auto Scaling Groups to configure. API Gateway HTTP API is simpler and 70% cheaper than REST API for this use case.

**Trade-offs accepted**: Lambda cold starts (~1 second for Python + FastAPI). Acceptable for a non-latency-critical internal tool.

---

## ADR-002: DynamoDB over RDS

**Status**: Accepted

**Context**: Need a database with serverless billing and zero idle cost.

**Options considered**:
| Option | Monthly Cost (idle) | Ops Overhead |
|--------|-------------------|-------------|
| RDS PostgreSQL (db.t3.micro) | ~$15/month | Backups, patches, connections |
| Aurora Serverless v2 | ~$0 idle but min ACU cost | Medium |
| DynamoDB on-demand | $0 at low usage (free tier) | None |

**Decision**: DynamoDB on-demand.

**Rationale**: Zero idle cost. No server to manage. Native Lambda integration via boto3. Free tier covers 25 GB storage + 25 WCU/RCU permanently.

**Trade-offs accepted**: No SQL joins. No multi-table transactions (mitigated by careful data model: sale items embedded in sale document; snapshot values at sale time). Requires GSI design upfront.

---

## ADR-003: React (TypeScript) + Tailwind CSS for Frontend

**Status**: Accepted

**Context**: Frontend must be mobile-first, maintainable, and hosted as a static site on S3.

**Decision**: React 18 + TypeScript + Tailwind CSS.

**Rationale**:
- React builds to static files — perfect for S3 hosting.
- TypeScript prevents type mismatch bugs between API responses and UI.
- Tailwind CSS: mobile-first by design; no custom CSS files needed; responsive utilities built-in.

**Trade-offs accepted**: Larger bundle than plain HTML/CSS/JS. Mitigated by CloudFront caching and gzip compression.

---

## ADR-004: Multi-Table DynamoDB Design

**Status**: Accepted

**Context**: DynamoDB supports both single-table and multi-table design patterns.

**Decision**: Multi-table design (one table per entity type).

**Rationale**: This is a learning project. Multi-table design is easier to reason about, easier to set up on the AWS Console, and maps naturally to the relational mental model. Single-table design requires deep DynamoDB expertise to get right and adds complexity without meaningful cost benefit at this scale.

**Trade-offs accepted**: More tables to create and manage. At this scale (7 tables, low traffic) this is negligible.

---

## ADR-005: Mangum as Lambda Adapter for FastAPI

**Status**: Accepted

**Context**: FastAPI is an ASGI framework; Lambda expects a specific event/context handler signature.

**Decision**: Use Mangum as a thin adapter layer.

**Rationale**: Mangum translates API Gateway proxy events to ASGI scope. Zero changes to FastAPI code. Widely used, well-maintained. Allows running the same FastAPI app locally with `uvicorn` and on Lambda with Mangum — no dual codebases.

---

## ADR-006: S3 + CloudFront for Frontend Hosting

**Status**: Accepted

**Context**: React SPA must be served over HTTPS globally with minimal cost.

**Decision**: S3 (private bucket) + CloudFront with Origin Access Control (OAC).

**Rationale**: S3 direct static website hosting is HTTP only and requires public bucket access. CloudFront + OAC gives HTTPS, CDN caching, and keeps the S3 bucket private (more secure). Cost is negligible for low traffic.

---

## ADR-007: Defer Authentication to Phase 6

**Status**: Accepted (temporary)

**Context**: Gmail OAuth via Cognito is needed for production use. Setting it up early adds complexity before core features exist.

**Decision**: Build all features first with a role-selector placeholder in dev mode. Add Cognito + Google OAuth in Phase 6.

**Rationale**: Separating concerns — feature completeness first, then security layer. This is a controlled, intentional deferral — not neglect. All API endpoints are designed with authentication in mind (user identity flows from seller_id in the path).

**Risk**: App is not secured until Phase 6. Mitigated by keeping the app private (not publicized) until auth is in place.

---

---

## ADR-009: Strict Layered Architecture with Abstract Base Classes

**Status**: Accepted

**Context**: A layered backend alone is not enough if layers can still directly import concrete implementations from adjacent layers. Without enforced abstractions, any layer can accidentally depend on internal details of another, making isolated testing impossible and refactoring risky.

**Decision**: Enforce strict one-way dependencies through Abstract Base Classes (ABCs) in a dedicated `interfaces/` module. Domain exceptions defined in `exceptions/` are the only thing that crosses layer boundaries.

**Layer contract:**
```
Router    →  AbstractService     (from interfaces/)
Service   →  AbstractRepository  (from interfaces/)
Repository →  DynamoDB            (boto3 only)
```

**Rules enforced:**
- No layer imports a concrete class from an adjacent layer — only the ABC.
- Concrete classes are injected at runtime via FastAPI `Depends()`.
- Repositories raise domain exceptions (`exceptions/`) — never boto3 `ClientError`.
- Routers catch only domain exceptions — boto3 errors never propagate above the repository.
- Raw DynamoDB response dicts never leave the repository layer.

**Rationale**:
- Routers can be tested with a mocked service without any database.
- Services can be tested with a mocked repository without moto or DynamoDB Local.
- Each layer can be developed and validated independently.
- Swapping DynamoDB for another store requires changes only in `repositories/` and `interfaces/` — zero changes to services or routers.

**Trade-offs accepted**: More upfront boilerplate (ABCs + exceptions module). This cost is paid once and saves significant rework later as the codebase grows.

**Status**: Accepted (temporary)

**Context**: Developer's laptop requires IT approval for Docker Desktop. DynamoDB Local requires Docker.

**Decision**: Use `moto_server` (pip-installable) as an interim DynamoDB substitute for local development.

**Rationale**: Same DynamoDB API surface. Pure Python — no permissions needed. Identical `DYNAMODB_ENDPOINT_URL` config as DynamoDB Local. Zero code changes when switching to Docker later.

**Trade-offs accepted**: In-memory only — data resets on process restart. Acceptable for development; automated tests use `moto` in-memory anyway.
