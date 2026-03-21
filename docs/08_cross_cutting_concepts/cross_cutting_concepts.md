# arc42 — Section 8: Cross-Cutting Concepts

Cross-cutting concepts are rules, patterns, and decisions that apply consistently across the entire codebase — not specific to one module or layer.

---

## 8.1 Security

- **Input validation**: all API request bodies validated by Pydantic models with explicit `min_length`, `max_length`, and regex constraints. Invalid input is rejected at the router layer — never reaches business logic.
- **No hardcoded credentials**: all secrets and configuration via environment variables. `.env` files added to `.gitignore`. AWS credentials in Lambda use IAM execution roles — no access keys in code.
- **HTTPS enforced**: CloudFront redirects all HTTP requests to HTTPS. No plain-text traffic in production.
- **CORS**: `allow_origins` restricted to the CloudFront domain in production. `localhost:3000` allowed in dev only.
- **DynamoDB injection prevention**: all expressions use `ExpressionAttributeValues` — never string-formatted expressions.
- **XSS**: React escapes all output by default. `dangerouslySetInnerHTML` is forbidden.
- **IAM least privilege**: Lambda execution role has `PutItem`, `GetItem`, `UpdateItem`, `DeleteItem`, `Query`, `Scan` on `bookrover-*` tables only. No wildcard resource permissions.
- **PII in logs**: phone numbers and full names are never written to logs.

---

## 8.2 Logging

- **Format**: structured JSON (CloudWatch-compatible).
- **Fields per log entry**: `level`, `message`, `timestamp`, `request_id`, `method`, `path`, `status_code`, `duration_ms`.
- **DynamoDB operations**: log `table`, `operation`, `key` for every call.
- **Log levels**: `DEBUG` in dev (verbose); `INFO` in prod (requests + errors only).
- **Never log**: PII (phone numbers, names), credentials, raw request bodies.
- **Location**: Lambda logs ship automatically to CloudWatch Log Group `/aws/lambda/bookrover-api-<env>`.
- **Retention**: 7 days (dev), 30 days (prod).

---

## 8.3 Error Handling

- **Validation errors** (`422`): Pydantic automatically returns field-level error details. Format: `{"detail": [{"loc": [...], "msg": "...", "type": "..."}]}`.
- **Business rule violations** (`400`, `409`): service layer raises custom exceptions caught by FastAPI exception handlers. Format: `{"detail": "human-readable message"}`.
- **Not found** (`404`): repository raises `ItemNotFoundError`; handler returns `{"detail": "Resource not found"}`.
- **Unexpected errors** (`500`): caught by global exception handler; logs full stack trace (server-side only); returns generic `{"detail": "An unexpected error occurred"}` — no internal details exposed to client.
- **Frontend**: every API call handles loading, error, and success states explicitly. Error messages shown in a red banner; auto-dismiss after 5 seconds.

---

## 8.4 Configuration Management

- All config via `pydantic-settings` `BaseSettings` in `backend/app/config.py`.
- Config is type-checked at startup — app will not start with missing required values.
- `.env.dev` for local development; `.env.prod` for production reference only (never committed).
- `.env.example` with placeholder values is committed to the repo.
- Lambda function reads config from environment variables injected at deploy time (via AWS Console or IaC).

---

## 8.5 Testing Strategy

### Layer Isolation — Each Layer Tested Independently

| Level | Location | Tool | What Is Mocked | AWS Needed? |
|-------|----------|------|----------------|-------------|
| **Router unit** | `tests/unit/test_routers/` | `pytest` + FastAPI `TestClient` | Service ABC (mock injected via `Depends()`) | No |
| **Service unit** | `tests/unit/test_services/` | `pytest` | Repository ABC (passed as mock to service constructor) | No |
| **Repository integration** | `tests/integration/` | `pytest` + `moto` | DynamoDB (mocked in-memory by moto) | No |
| **Full stack integration** | `tests/integration/` | `pytest` + `moto` + `TestClient` | DynamoDB only (moto) | No |
| **Manual UI** | Browser | `moto_server` or DynamoDB Local | N/A | No |
| **Smoke** | Browser on AWS | None | N/A | Yes (once) |

**Key isolation rules:**
- Router tests never instantiate a real service — only a mock implementation of the service ABC.
- Service tests never instantiate a real repository — only a mock implementation of the repository ABC.
- No test at the unit level touches DynamoDB, boto3, or moto.
- `moto` is only used in integration tests where real DynamoDB I/O is being verified.
- Each layer can be built and tested in isolation before the next layer is written.

**Test naming:** `test_<action>_<condition>_<expected_result>`  
Example: `test_create_sale_when_quantity_exceeds_stock_returns_400`

**Coverage target:** ≥ 80% on `services/` and `routers/`  
**Run:** `pytest --cov=app --cov-report=term-missing`

---

## 8.6 Code Formatting and Linting

| Language | Formatter | Linter |
|----------|-----------|--------|
| Python | `black` | `ruff` |
| TypeScript/React | `prettier` | `eslint` |

- Enforced via pre-commit hooks (to be configured in Phase 2).
- CI will run lint + format checks on every pull request.

---

## 8.7 Decimal Precision (Money)

- All monetary values stored as DynamoDB `Number` type.
- Pydantic models use Python `Decimal` with 2 decimal places.
- Frontend displays with 2 decimal places: `₹75.00`.
- **Never use JavaScript `float` for money calculations** — use string formatting from the API response directly.

---

## 8.8 Idempotency

- `PUT` (update) endpoints are idempotent — calling the same request twice produces the same result.
- `POST` (create) endpoints are NOT idempotent — duplicate calls create duplicate records. Frontend disables the submit button after the first tap and re-enables only on error.
- DynamoDB `put_item` with `ConditionExpression=Attr("pk").not_exists()` prevents silent overwrites on create operations.
