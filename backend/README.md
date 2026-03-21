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

## Setup
> Instructions will be added in Phase 2.
