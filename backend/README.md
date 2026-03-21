# BookRover — Backend

FastAPI (Python) backend, deployed to AWS Lambda via Mangum.

## Stack
- Python 3.12
- FastAPI + Pydantic v2
- Mangum (Lambda adapter for ASGI)
- boto3 (AWS DynamoDB)
- pydantic-settings (typed config)
- pytest + moto (testing)

## Structure
```
app/
├── main.py              # FastAPI app factory + router registration
├── config.py            # Typed config via pydantic-settings
├── dependencies.py      # Shared FastAPI Depends()
├── routers/             # One router per domain
├── models/              # Pydantic request/response models
├── services/            # Business logic layer
├── repositories/        # DynamoDB data access layer
└── utils/               # Shared utilities
tests/
├── unit/                # Unit tests (mocked repositories)
└── integration/         # Integration tests (moto-mocked DynamoDB)
```

## Local Setup

```powershell
# Create virtual environment
python -m venv .venv

# Install dependencies
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\pip install -r requirements-dev.txt

# Set environment variables
$env:APP_ENV = "dev"
$env:AWS_DEFAULT_REGION = "ap-south-1"
$env:AWS_ACCESS_KEY_ID = "test"
$env:AWS_SECRET_ACCESS_KEY = "test"
$env:PYTHONPATH = $null

# Run locally
.venv\Scripts\python.exe -m uvicorn bookrover.main:app --reload --port 8080
```

OpenAPI docs: http://localhost:8080/docs

## Running Tests

```powershell
$env:PYTHONPATH = $null
.venv\Scripts\python.exe -m pytest tests/ -v

# With coverage
.venv\Scripts\python.exe -m pytest tests/ --cov=bookrover --cov-report=term-missing
```

## Linting

```powershell
.venv\Scripts\python.exe -m ruff check bookrover/
```
