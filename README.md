# BookRover

**Door-to-door book selling management app.**

BookRover manages the end-to-end lifecycle of a door-to-door book selling operation — from collecting books at a local bookstore, selling them door-to-door, to returning unsold books and collected money.

## Project Structure

```
BookRover/
├── .github/
│   └── instructions/
│       └── bookrover.instructions.md   # Copilot SKILL — coding standards & conventions
├── specs/
│   ├── project-overview.md             # Business context, roles, tech stack
│   ├── data-models.md                  # All entities, DynamoDB table design
│   ├── api-spec.md                     # All FastAPI endpoints (request/response)
│   ├── pages-spec.md                   # Per-page UI specification
│   └── aws-architecture.md             # AWS services, setup order, cost, SAA-C03 map
├── frontend/                           # React (TypeScript) + Tailwind CSS
├── backend/                            # FastAPI (Python) + Lambda + DynamoDB
├── infra/                              # Terraform IaC (Phase 7)
└── docs/                               # AWS setup guides, runbooks
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, TypeScript, Tailwind CSS |
| Backend | Python 3.12, FastAPI, Mangum |
| Database | AWS DynamoDB |
| Hosting | AWS Lambda + API Gateway + S3 + CloudFront |
| Auth | AWS Cognito + Google OAuth (Phase 6) |
| IaC | Terraform (Phase 7) |

## Development Phases

1. ✅ Spec files + SKILL.md + project scaffold
2. ⬜ Backend: FastAPI + DynamoDB + tests
3. ⬜ Frontend: React + mobile-first UI
4. ⬜ AWS Console manual setup
5. ⬜ End-to-end testing on AWS
6. ⬜ Gmail authentication (Cognito)
7. ⬜ Terraform IaC

## Estimated AWS Cost

**~$0 – $0.50/month** at small friend-group usage scale (within AWS free tier).
Door-to-door book selling management app
