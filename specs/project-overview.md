# BookRover — Project Overview

## Purpose

BookRover is a mobile-first web application that manages the end-to-end lifecycle of a door-to-door book selling operation:

1. **Collect** books from a local bookstore (on consignment).
2. **Sell** books door-to-door to buyers.
3. **Return** unsold books + collected money to the bookstore.

The app tracks inventory per seller, records every sale, and provides the group leader with a consolidated dashboard of all sellers' performance.

---

## Business Model

- A **bookstore** provides books to a **group leader** on consignment.
- A **group leader** oversees a team of **sellers**.
- Each **seller** takes their own portion of books and sells door-to-door independently.
- At the end of the selling round, each seller returns unsold books + collected cash to the bookstore.
- Sellers are always tied to exactly one group leader + bookstore combination at a time.

---

## User Roles

| Role | Description | Access |
|------|-------------|--------|
| **Admin** | Manages group leaders and bookstore records. Separate login — not visible to sellers. | Admin page only |
| **Group Leader** | Oversees sellers under them; views dashboard for their bookstore. Can be linked to multiple bookstores. | Group Leader Dashboard |
| **Seller** | Registers themselves, manages their inventory, records sales, views their return summary. | Seller pages |

---

## Key Business Rules

1. **Inventory is per seller, per bookstore** — each seller independently manages their own book stock collected from a specific bookstore.
2. **Return summary is per seller** — shows that seller's remaining books + money collected from their sales.
3. **Seller ↔ Group Leader is fixed at registration** — a seller picks a group leader (and thus a bookstore) when registering.
4. **Switching group leader requires full return first** — a seller must complete a full return (all books + money) before switching to a different group leader + bookstore combination.
5. **One active group leader + bookstore per seller at a time** — no split inventory across multiple bookstores.
6. **Admin is a separate login** — not part of the seller or group leader flow.

---

## App Name

**BookRover**

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React (TypeScript), Tailwind CSS |
| Backend | Python, FastAPI, Pydantic, Mangum |
| Database | AWS DynamoDB |
| Hosting — Frontend | AWS S3 + CloudFront |
| Hosting — Backend | AWS Lambda + API Gateway (HTTP API) |
| Authentication | Gmail/Google OAuth via AWS Cognito (deferred to rollout phase) |
| Source Control | GitHub |
| IaC (future) | Terraform |

---

## AWS Services Used

| Service | Purpose |
|---------|---------|
| **S3** | Host React static build files |
| **CloudFront** | CDN for React frontend; enforces HTTPS |
| **API Gateway (HTTP API)** | Expose backend Lambda as REST endpoints |
| **Lambda** | Run FastAPI backend (via Mangum adapter) |
| **DynamoDB** | Serverless NoSQL database for all app data |
| **Cognito** | Gmail federation for authentication (deferred) |
| **CloudWatch** | Logs and metrics for Lambda and API Gateway |
| **IAM** | Least-privilege roles for Lambda execution |
| **ACM (Certificate Manager)** | SSL/TLS certificate for custom domain |
| **Route 53** | Custom domain DNS (optional) |

---

## Cost Strategy

- All compute is serverless (Lambda, API Gateway) — pay only when used.
- DynamoDB uses on-demand billing — no provisioned capacity costs.
- S3 + CloudFront for frontend — negligible cost for small traffic.
- Expected AWS bill: **$0–$2/month** at small friend-group scale (within free tier).

---

## Development Phases

| Phase | Scope |
|-------|-------|
| **Phase 1** | Spec files, SKILL.md, project scaffold, GitHub repo |
| **Phase 2** | Backend: FastAPI app, all API endpoints, DynamoDB tables, unit + integration tests |
| **Phase 3** | Frontend: React app, all pages, mobile-first UI, connected to backend |
| **Phase 4** | AWS manual setup (Console): DynamoDB, Lambda, API Gateway, S3, CloudFront |
| **Phase 5** | End-to-end testing on AWS |
| **Phase 6** | Authentication: Gmail/Google OAuth via Cognito |
| **Phase 7** | Terraform IaC — codify the manual AWS setup |

---

## Non-Functional Requirements

- **Mobile-first**: all pages must work correctly on a phone browser at 375px width and above.
- **Performance**: page loads < 2 seconds; API responses < 500ms.
- **Simplicity**: the UI must require zero training — sellers are non-technical users.
- **Cost-minimal**: AWS bill must stay within free tier or near-zero for small usage.
- **Testability**: ≥ 80% test coverage on backend services and routers.
- **Maintainability**: clean, well-commented code following SOLID and Clean Code principles.

---

## Out of Scope (for now)

- Push notifications
- Offline mode
- Multi-language UI
- Payment gateway integration
- PDF report generation
- Authentication (deferred to Phase 6)
