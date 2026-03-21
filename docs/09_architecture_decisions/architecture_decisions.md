# arc42 — Section 9: Architecture Decisions

Architecture Decision Records (ADRs) document the significant decisions made for BookRover, the context behind them, the options considered, and the rationale for the choice made.

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

## ADR-008: moto_server as DynamoDB Substitute (Pre-Docker)

**Status**: Accepted (temporary)

**Context**: Developer's laptop requires IT approval for Docker Desktop. DynamoDB Local requires Docker.

**Decision**: Use `moto_server` (pip-installable) as an interim DynamoDB substitute for local development.

**Rationale**: Same DynamoDB API surface. Pure Python — no permissions needed. Identical `DYNAMODB_ENDPOINT_URL` config as DynamoDB Local. Zero code changes when switching to Docker later.

**Trade-offs accepted**: In-memory only — data resets on process restart. Acceptable for development; automated tests use `moto` in-memory anyway.
