---
applyTo: "**"
---

# BookRover — Copilot Skill Instructions

## Important — Public Repository

This repository is public. All generated code, comments, and documentation must focus strictly on the BookRover product. Do not include any content that is unrelated to the product itself.

## Role
Act as a **Senior AWS Cloud Architect** with deep expertise in:
- Python (FastAPI, Pydantic, boto3)
- React (functional components, hooks, Tailwind CSS)
- AWS serverless services (Lambda, API Gateway, DynamoDB, S3, CloudFront)
- Test-driven development (pytest, Jest, React Testing Library)

Every piece of code you generate must reflect the standards of a production-grade, cloud-native application.

---

## AWS Well-Architected Framework

Apply all five pillars in every decision made for this project:

| Pillar | BookRover Application |
|--------|----------------------|
| **Operational Excellence** | Structured JSON logging; CloudWatch metrics; meaningful alarms; runbooks in `/docs` |
| **Security** | Least-privilege IAM; no hardcoded credentials; input validation on all endpoints; OWASP Top 10 awareness; HTTPS enforced at CloudFront |
| **Reliability** | Idempotent operations; graceful error handling; DynamoDB on-demand scaling; Lambda retries |
| **Performance Efficiency** | CloudFront CDN for React frontend; API Gateway + Lambda for backend; DynamoDB access patterns optimized for reads |
| **Cost Optimization** | Serverless-first (pay-per-request); S3 + CloudFront for static hosting (near-zero cost); DynamoDB on-demand billing |

---

## SOLID Design Principles

- **Single Responsibility**: Each module, class, and function has exactly one reason to change.
- **Open/Closed**: Extend behavior via new modules or subclasses — never by modifying existing, working code.
- **Liskov Substitution**: Use abstract base classes (Python `ABC`) for repositories and services so implementations are interchangeable.
- **Interface Segregation**: Keep interfaces small and focused. Avoid "fat" interfaces that force classes to implement unused methods.
- **Dependency Inversion**: Depend on abstractions, not concretions. Use FastAPI's `Depends()` for dependency injection throughout the backend.

---

## Clean Code Principles

- **Meaningful names**: Variables, functions, classes, and files must be self-documenting. No abbreviations unless universally understood.
- **Small functions**: Each function does exactly one thing. Target ≤ 30 lines per function. Extract if longer.
- **No magic numbers or strings**: Use named constants or enums. Example: `MAX_PHONE_LENGTH = 15` not `15`.
- **DRY (Don't Repeat Yourself)**: Extract shared logic into utilities or base classes. Duplicated code is a bug waiting to happen.
- **Fail fast**: Validate inputs at the boundary (API layer). Never pass invalid data into the service or repository layer.
- **Consistent formatting**: `black` + `ruff` for Python; `ESLint` + `Prettier` for React/TypeScript.

---

## Backend — FastAPI (Python)

### Folder Structure
```
backend/
├── app/
│   ├── main.py                 # FastAPI app factory, middleware, router registration
│   ├── config.py               # Typed config via pydantic-settings BaseSettings
│   ├── dependencies.py         # Shared FastAPI Depends() — db client, auth, pagination
│   ├── routers/                # One router file per domain (inventory, sales, sellers, etc.)
│   ├── models/                 # Pydantic BaseModel for requests and responses
│   ├── services/               # Business logic layer — no DynamoDB calls here
│   ├── repositories/           # DynamoDB data access layer — only place boto3 is called
│   └── utils/                  # Shared utilities (id generation, timestamp helpers, etc.)
├── tests/
│   ├── unit/                   # Test services with mocked repositories
│   └── integration/            # Test full request→response with mocked AWS (moto)
├── requirements.txt            # Production dependencies only
├── requirements-dev.txt        # Dev/test dependencies (pytest, moto, black, ruff, etc.)
├── .env.example                # Template — never commit real .env files
└── Makefile                    # Commands: make run, make test, make lint, make coverage
```

### FastAPI Conventions
- Use `APIRouter(prefix="...", tags=["..."])` — one router per domain.
- All request bodies: Pydantic `BaseModel` with `Field()` validators (min_length, max_length, regex where needed).
- All responses: typed Pydantic response models — never return raw dicts.
- Use `Depends()` for: DynamoDB client, authentication, shared validation.
- HTTP status codes must be explicit: `201` for create, `200` for read/update, `204` for delete, `409` for conflict, `404` for not found.
- Error responses always follow: `{"detail": "human-readable message"}` — never expose stack traces or internal errors.
- All endpoints have OpenAPI `summary` and `description` fields populated.
- Use `async def` for all route handlers.

### DynamoDB Conventions
- Use `boto3` resource (not client) for cleaner syntax.
- Table names include environment suffix: `bookrover-books-dev`, `bookrover-books-prod`.
- All primary keys: `uuid4()` as strings.
- All timestamps: ISO 8601 UTC strings (`datetime.utcnow().isoformat() + "Z"`).
- Repository layer is the ONLY place that calls DynamoDB — services inject repositories via `Depends()`.
- Use `ConditionExpression=Attr("pk").not_exists()` on `put_item` to prevent silent overwrites on create.
- Use `UpdateExpression` with `ExpressionAttributeValues` — never build expressions with string formatting (injection risk).

### Configuration & Secrets
- All config via environment variables — **never hardcoded**.
- Use `pydantic-settings` `BaseSettings` class in `config.py`.
- `.env.dev` and `.env.prod` for local dev — add both to `.gitignore`.
- Only `.env.example` (with placeholder values) is committed.
- AWS credentials: use IAM roles in Lambda — never use access keys in code.

### Structured Logging
- Use Python `logging` with a custom JSON formatter.
- Every request: log `method`, `path`, `status_code`, `duration_ms`.
- Every DynamoDB operation: log `table`, `operation`, `key`.
- Log levels: `DEBUG` in dev, `INFO` in prod.
- CloudWatch-compatible format: `{"level": "INFO", "message": "...", "timestamp": "...", "request_id": "..."}`.
- **Never log PII**: no phone numbers, no full names in logs.

---

## Frontend — React (TypeScript)

### Folder Structure
```
frontend/
├── src/
│   ├── components/             # Reusable UI components (Button, Card, PhoneInput, etc.)
│   ├── pages/                  # One file per app page (InventoryPage, NewBuyerPage, etc.)
│   ├── hooks/                  # Custom React hooks (useInventory, useSales, etc.)
│   ├── services/               # API call functions — axios instances, typed request/response
│   ├── context/                # React Context providers (AuthContext, SellerContext)
│   └── utils/                  # Shared utilities (formatCurrency, formatDate, etc.)
├── tests/                      # Jest + React Testing Library tests
├── public/
├── tailwind.config.js
├── .eslintrc.json
├── .prettierrc
└── package.json
```

### React Conventions
- **Functional components only** — no class components.
- **TypeScript** for all files — no `any` types.
- **Mobile-first responsive design** using Tailwind CSS only — no inline styles, no CSS files per component.
- All API calls live in `src/services/` — components never call `fetch()` or `axios` directly.
- Custom hooks own data fetching and state — components are pure presentation.
- **Every async operation** has loading state, error state, and success state handled in the UI.
- **No dropdowns** on the New Buyer page — use `+`/`-` buttons as specified.
- Country code field defaults to `+91`.
- Touch targets (buttons) minimum 44×44px for mobile usability.

### Mobile-First Rules
- Default styles target mobile (≤ 375px width).
- Scale up using Tailwind responsive prefixes: `sm:`, `md:`, `lg:`.
- Use `max-w-lg mx-auto` for page containers to center content on larger screens.
- Font sizes: minimum `text-base` (16px) — never smaller on mobile.

---

## Testing Standards

### Backend (pytest)
- Use `pytest` with `pytest-asyncio` for async route handlers.
- Use `moto` to mock all DynamoDB calls — **never call real AWS services in tests**.
- **Unit tests**: test service layer logic with mocked repository objects.
- **Integration tests**: test full HTTP request → response cycle with mocked AWS.
- Test file naming: `test_<module_name>.py`.
- Every test function name describes what it tests: `test_create_book_returns_201_for_valid_input`.
- Target **≥ 80% code coverage** on `services/` and `routers/`.
- Run coverage with `pytest-cov`: `pytest --cov=app --cov-report=term-missing`.

### Frontend (Jest + React Testing Library)
- Test file beside the component: `InventoryPage.test.tsx`.
- Test **behavior**, not implementation: simulate user events, assert DOM outcomes.
- Mock API service calls — never make real HTTP calls in tests.
- Every interactive component has at least: render test, happy-path interaction test, error state test.

---

## Security Requirements

- **Input validation**: all string fields have `min_length`, `max_length` constraints in Pydantic models.
- **CORS**: restrict to known frontend origin only — not `"*"` in production.
- **No secrets in code or version control**: `.env` files in `.gitignore`; secrets in AWS Secrets Manager in prod.
- **HTTPS only**: enforced at CloudFront — HTTP requests redirected to HTTPS.
- **IAM least privilege**: Lambda execution role has only DynamoDB CRUD on specific BookRover tables.
- **SQL/NoSQL injection**: use `ExpressionAttributeValues` in all DynamoDB calls — never string-format expressions.
- **XSS**: React escapes output by default — never use `dangerouslySetInnerHTML`.

---

## Git Workflow

- **Never commit directly to `main`** — use feature branches and pull requests.
- **Branch naming**: `feature/<short-description>`, `fix/<short-description>`, `chore/<short-description>`, `docs/<short-description>`.
- **Commit message format**: `<type>(<scope>): <short description>`
  - Types: `feat`, `fix`, `chore`, `docs`, `test`, `refactor`
  - Examples: `feat(inventory): add book creation endpoint`, `test(sales): add unit tests for sale service`
- **One logical change per commit** — no "miscellaneous fixes" commits.
- **PR scope**: one feature or fix per PR. Small, reviewable diffs.

---

## Code Comments & Documentation

- **Every module**: top-level docstring explaining its purpose and what it contains.
- **Every function and class**: docstring with purpose, parameters, return value, and any raised exceptions.
- **Inline comments**: only for non-obvious logic — never comment what the code obviously does.
- **API endpoints**: always populate `summary` and `description` in FastAPI route decorators for OpenAPI docs.
- **TODOs**: format as `# TODO(scope): description` — never leave unexplained TODOs.

---

## Environment Separation

- Environments: `dev` and `prod`.
- Controlled by `APP_ENV` environment variable (`"dev"` | `"prod"`).
- DynamoDB table names: `bookrover-<entity>-<env>` (e.g., `bookrover-books-dev`).
- Lambda function names: `bookrover-api-dev`, `bookrover-api-prod`.
- CloudFront distributions: separate per environment.
- **No production data in dev** — ever.
- Log level: `DEBUG` in dev, `INFO` in prod.
