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

Run the backend and frontend across three terminals. **Start them in order: moto server first, then backend, then frontend.**

### Prerequisites
- Python 3.12
- Node.js 18
- Git

### Terminal 1 — Local DynamoDB (moto server)

No Docker needed. `moto_server` is a pure-Python DynamoDB emulator included in the dev dependencies.

```powershell
cd BookRover/backend
$env:PYTHONPATH = $null
.venv\Scripts\python.exe -m moto.server -p 8001
```

Leave this running. moto server stores data in-memory only — all table data resets when the process stops.

### Terminal 2 — Backend (FastAPI)

```powershell
cd BookRover/backend

# First time only — create virtual environment and install dependencies
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\pip install -r requirements-dev.txt

# Copy the env template and set your admin email (first time only)
Copy-Item .env.example .env
# Then open .env and set: ADMIN_EMAILS=["admin@test.com"]
# Or skip the .env edit and just set the shell variable:
$env:ADMIN_EMAILS = '["admin@test.com"]'

# Set required environment variables
$env:APP_ENV = "dev"
$env:AWS_DEFAULT_REGION = "ap-south-1"
$env:AWS_ACCESS_KEY_ID = "test"
$env:AWS_SECRET_ACCESS_KEY = "test"
$env:DYNAMODB_ENDPOINT_URL = "http://localhost:8001"
$env:PYTHONPATH = $null  # required on Windows if a global Python is also installed

# Start the backend
.venv\Scripts\python.exe -m uvicorn bookrover.main:app --reload --port 8080
```

Backend runs at: http://localhost:8080  
OpenAPI docs: http://localhost:8080/docs

### Terminal 3 — Frontend (React)

```powershell
cd BookRover/frontend

# First time only
npm install

# Start the frontend
npm run dev
```

Frontend runs at: http://localhost:5173  
All `/api/*` requests are proxied to `http://localhost:8080` automatically.

### First-Run Flow

The local dev auth flow is structurally identical to production — the only difference is that Cognito is replaced by a mock token endpoint. All data is created through the app UI, exactly as in production. There is no seed step.

1. Open `http://localhost:5173` — redirected to `/login`.
2. Enter the email you set in `ADMIN_EMAILS` (e.g. `admin@test.com`) and click **Continue**.
3. `GET /me` finds your email in `ADMIN_EMAILS` and returns `role: admin` → routed to `/admin`.
4. From `/admin`, create at least one **bookstore** and one **group leader** (linked to that bookstore).
5. Open a private/incognito window. Log in as the group leader's email → routed to `/dashboard`.
6. Log in as a brand-new email → routed to `/register`.
7. The registration dropdown shows the group leader and bookstore you created. Complete registration → routed to `/inventory`.

> **Note:** moto_server is in-memory. All data is lost when you stop it. Re-run steps 4–7 after each restart.

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
