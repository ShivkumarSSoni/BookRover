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
│   └── aws-architecture.md             # AWS services, setup order, cost estimate
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

---

## Local Development

Run the backend and frontend in two separate terminals.

### Prerequisites
- Python 3.12
- Node.js 18
- Git

### Terminal 1 — Backend (FastAPI)

```powershell
cd BookRover/backend

# First time only — create virtual environment and install dependencies
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\pip install -r requirements-dev.txt

# Set required environment variables
$env:APP_ENV = "dev"
$env:AWS_DEFAULT_REGION = "ap-south-1"
$env:AWS_ACCESS_KEY_ID = "test"
$env:AWS_SECRET_ACCESS_KEY = "test"
$env:PYTHONPATH = $null  # required on Windows if a global Python is also installed

# Start the backend
.venv\Scripts\python.exe -m uvicorn bookrover.main:app --reload --port 8000
```

Backend runs at: http://localhost:8000  
OpenAPI docs: http://localhost:8000/docs

> **Note:** In `dev` mode the app uses a local DynamoDB (moto-based in tests) or real DynamoDB if AWS credentials are configured. For local UI testing without real AWS, set dummy credentials as shown above — the backend will start but DynamoDB calls will fail unless you also run a local DynamoDB instance.

### Terminal 2 — Frontend (React)

```powershell
cd BookRover/frontend

# First time only
npm install

# Start the frontend
npm run dev
```

Frontend runs at: http://localhost:5173  
All `/api/*` requests are proxied to `http://localhost:8000` automatically.

### Access the Admin Feature

Open: http://localhost:5173/admin

- **Group Leaders tab** — create, edit, delete group leaders; assign bookstores
- **Bookstores tab** — create, edit, delete bookstores

### Running Tests

**Backend:**
```powershell
cd BookRover/backend
$env:PYTHONPATH = $null
.venv\Scripts\python.exe -m pytest tests/ -v
```

**Frontend:**
```powershell
cd BookRover/frontend
npm test
```
