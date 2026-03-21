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

## Architecture Patterns

Apply the following architecture and design patterns consistently. These are not optional — they are what make the codebase clean, testable, and maintainable.

### Hexagonal Architecture (Ports and Adapters)

The core business domain (services) must have **zero knowledge** of external systems (DynamoDB, Lambda, HTTP). External systems connect to the domain through adapters:

- **Inbound adapters**: FastAPI routers (HTTP → service calls); Mangum (Lambda event → ASGI)
- **Outbound adapters**: Repositories (service calls → DynamoDB via boto3)
- **Benefit**: The entire service layer is testable without any AWS dependency — swap DynamoDB for moto in tests, swap Lambda for uvicorn locally. Nothing in the domain changes.

### Repository Pattern

`repositories/` is the **only** layer permitted to call DynamoDB. Services call repositories through injected abstractions — never boto3 directly. This means:
- DynamoDB access patterns are centralized and easy to optimize.
- Services are unit-testable by injecting a mock repository.
- Switching from DynamoDB to another store requires changes in one place only.

### Service Layer Pattern

`services/` owns **all business rules** and orchestration. Routers handle HTTP concerns (status codes, request parsing, response formatting). Repositories handle data concerns. Services handle everything in between. No business logic in routers. No DynamoDB calls in services.

### API Gateway Pattern

AWS API Gateway is the **single, controlled entry point** into the backend. All requests are validated (CORS, throttling) before reaching Lambda. The FastAPI app behind it treats API Gateway as a transport detail — not a business concern.

### Serverless / Event-Driven Pattern

Lambda functions are **stateless** — no in-memory state between invocations. All state lives in DynamoDB. Each Lambda invocation is independent. Design every handler to be safe to retry (idempotency).

---

### Design Patterns

Apply these Gang-of-Four and modern design patterns where they naturally fit:

| Pattern | Where Applied in BookRover |
|---------|--------------------------|
| **Dependency Injection** | FastAPI `Depends()` for DB client, repositories, settings — never instantiate dependencies inside functions |
| **Factory** | `app/main.py` is the app factory — creates the FastAPI instance, registers all routers, applies middleware; never scattered across files |
| **DTO (Data Transfer Object)** | Pydantic models are the DTOs between HTTP ↔ service ↔ repository layers; never pass raw dicts between layers |
| **Singleton** | `pydantic-settings` `BaseSettings` is instantiated once and shared via `Depends(get_settings)` |
| **Strategy** | Dashboard sorting: `sort_by` and `sort_order` are injected as parameters; the sorting logic is interchangeable without changing the service structure |
| **Snapshot** | `SaleItem` and `ReturnItem` capture `book_name`, `language`, and `price` at transaction time — historical records remain accurate even if the book's details are later modified |

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
├── bookrover/                  # The bookrover Python package — this IS the BookRover namespace
│   ├── __init__.py
│   ├── main.py                 # FastAPI app factory, middleware, router registration
│   ├── config.py               # Typed config via pydantic-settings BaseSettings
│   ├── dependencies.py         # Shared FastAPI Depends() — db client, auth, pagination
│   ├── routers/                # HTTP layer — parse requests, call services, return responses
│   ├── models/                 # Pydantic DTOs — request bodies and response models
│   ├── interfaces/             # Abstract base classes (ABC) for services and repositories
│   ├── services/               # Business logic layer — no DynamoDB calls here
│   ├── repositories/           # DynamoDB data access layer — only place boto3 is called
│   ├── exceptions/             # Domain exception classes (e.g., BookNotFoundError)
│   └── utils/                  # Shared utilities (id generation, timestamp helpers, etc.)
├── tests/
│   ├── unit/
│   │   ├── test_services/      # Services tested with mocked repository ABCs
│   │   └── test_routers/       # Routers tested with mocked service ABCs
│   └── integration/            # Full HTTP request → DynamoDB round trip via moto
├── requirements.txt            # Production dependencies only
├── requirements-dev.txt        # Dev/test dependencies (pytest, moto, black, ruff, etc.)
├── .env.example                # Template — never commit real .env files
└── Makefile                    # Commands: make run, make test, make lint, make coverage
```

### Strict Layer Isolation Rules

These rules are **non-negotiable**. Every violation breaks testability and maintainability.

**Dependency direction — strictly one way, no skipping:**
```
Router → Service → Repository → DynamoDB
```
- Routers call services only — never repositories directly.
- Services call repositories only — never boto3 or DynamoDB directly.
- Repositories call DynamoDB only — they never call services or other repositories.

**Abstract Base Classes (ABCs) as layer contracts:**
- Every service has an ABC in `interfaces/` — e.g., `AbstractInventoryService`.
- Every repository has an ABC in `interfaces/` — e.g., `AbstractInventoryRepository`.
- Routers depend on the service ABC — never the concrete service class.
- Services depend on the repository ABC — never the concrete repository class.
- This makes every layer swappable and independently testable.

**Data flow between layers:**
- Router → Service: pass Pydantic request model fields as typed arguments — never pass the raw request object into the service.
- Service → Router: return Pydantic response models — never raw dicts.
- Service → Repository: pass primitive typed arguments (IDs, strings, Decimals) — never Pydantic HTTP models.
- Repository → Service: return domain data as typed dicts or dataclasses — never raw DynamoDB response dicts.

**Exception hierarchy — domain exceptions only cross layer boundaries:**
- Repositories raise domain exceptions from `exceptions/` (e.g., `BookNotFoundError`, `DuplicateEmailError`).
- Services may raise additional domain exceptions for business rule violations.
- Routers catch domain exceptions and translate them to HTTP responses — boto3 `ClientError` must never propagate to the router.
- No `except Exception` in routers — only catch specific domain exceptions.

**Per-layer testability:**
- `tests/unit/test_services/` — instantiate the concrete service with a **mocked** repository ABC. No moto, no DynamoDB, no HTTP client needed.
- `tests/unit/test_routers/` — use FastAPI `TestClient` with a **mocked** service ABC injected via `Depends()`. No repository, no DynamoDB needed.
- `tests/integration/` — use FastAPI `TestClient` with the real service and repository wired together, DynamoDB mocked via `moto`.
- Each layer must be fully testable without knowledge of any other layer's implementation.

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
│   ├── types/                  # BookRover namespace declarations — one file per domain + index barrel
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
- Use `moto` to mock DynamoDB in integration tests — **never call real AWS services in tests**.
- **Router unit tests** (`tests/unit/test_routers/`): use FastAPI `TestClient` with a mocked service ABC injected via `Depends()`. No repository, no DynamoDB needed.
- **Service unit tests** (`tests/unit/test_services/`): instantiate the concrete service with a mocked repository ABC. No moto, no HTTP client needed.
- **Integration tests** (`tests/integration/`): wire real service + real repository together; mock only DynamoDB via `moto`.
- Each layer must be fully testable without knowledge of any other layer's implementation.
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

## Feature Build Order

When implementing any new feature, always follow this vertical-slice order. Do not skip layers or implement them out of sequence.

**Backend first:**
```
models → ABC → repository → service → router → tests
```
1. **models** — Pydantic DTOs (request + response) in `models/`
2. **ABC** — abstract base classes in `interfaces/` for both the repository and service
3. **repository** — DynamoDB adapter in `repositories/` implementing the repository ABC
4. **service** — business logic in `services/` implementing the service ABC, injecting the repository ABC
5. **router** — HTTP layer in `routers/` injecting the service ABC via `Depends()`
6. **tests** — unit tests for service (mock repo), unit tests for router (mock service), integration tests (moto)

**Frontend after backend is tested:**
```
types → service → hook → page → tests → wire App.tsx
```
1. **types** — add interfaces to the `BookRover` namespace in `src/types/`
2. **service** — API call functions in `src/services/`
3. **hook** — custom hook in `src/hooks/` for data fetching and state
4. **page** — React component in `src/pages/`
5. **tests** — `<Page>.test.tsx` beside the page file
6. **wire** — add the route to `src/App.tsx`

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

## Code Organization

- **All logic in classes**: Every service, repository, and router handler lives inside a class. No naked functions at module level (except utility functions in `utils/` that are truly stateless helpers with no dependencies).
- **ABCs as contracts**: Every concrete class implements its corresponding ABC from `interfaces/`. Never instantiate a concrete class where the ABC is expected.
- **Constructor injection in services**: e.g., `InventoryService.__init__(self, repository: AbstractInventoryRepository)` — the repository is injected into the constructor, never instantiated inside the service.
- **Constructor injection in repositories**: e.g., `DynamoDBInventoryRepository.__init__(self, table)` — the DynamoDB table resource is injected, never fetched inside the repository constructor.
- **FastAPI wiring**: `Depends()` at the router level is the DI entry point — it builds the dependency graph (`DynamoDB resource → repository → service`) and injects the correct concrete implementation at request time.
- **One class per file**: Each concrete service, repository, or ABC lives in its own file. File name must match the class it contains.

---

## Naming Conventions

Naming follows language-idiomatic standards for each layer. Do not mix conventions across languages.

### Namespace — BookRover

All interfaces, classes, and types in both the backend and frontend must belong to the `BookRover` namespace. Each language expresses this differently due to language constraints:

**Python backend** — the `bookrover` package IS the namespace:
- Python's import system requires lowercase package names. `bookrover` (lowercase) is the Python expression of the `BookRover` namespace.
- Every class (service, repository, ABC, Pydantic model, exception) must be defined inside the `bookrover` package hierarchy — never as a standalone script or top-level module outside the package.
- The qualified name of any class is always `bookrover.<layer>.<module>.ClassName`.
  ```
  bookrover.services.inventory_service.InventoryService
  bookrover.interfaces.abstract_inventory_service.AbstractInventoryService
  bookrover.repositories.dynamodb_inventory_repository.DynamoDBInventoryRepository
  bookrover.models.book.BookResponse
  bookrover.exceptions.not_found.BookNotFoundError
  ```
- Import pattern: `from bookrover.services.inventory_service import InventoryService`

**TypeScript frontend** — explicit `namespace BookRover` blocks:
- All interfaces, types, classes, and enums must be declared inside an `export namespace BookRover { }` block.
- Namespace declarations live in `src/types/` — one file per domain (e.g., `inventory.ts`, `sales.ts`) plus a barrel `src/types/index.ts` that re-exports all.
- React functional components are top-level named exports (JSX requirement). Their prop interfaces are declared inside the `BookRover` namespace.
- Usage pattern:
  ```typescript
  // src/types/inventory.ts
  export namespace BookRover {
    export interface Book { book_id: string; title: string; language: string; }
    export interface BookListResponse { books: Book[]; total: number; }
  }

  // src/types/index.ts
  export { BookRover } from './inventory';

  // usage in a component
  import { BookRover } from '../types';
  const book: BookRover.Book = { ... };
  ```

---

### Python Backend — PEP 8

| Element | Convention | Example |
|---------|-----------|---------|
| Package / module | `snake_case` | `bookrover`, `inventory_service`, `book_repository` |
| Class | `PascalCase` | `InventoryService`, `AbstractBookRepository` |
| Method | `snake_case` | `create_book()`, `list_books()`, `get_book_by_id()` |
| Variable / parameter | `snake_case` | `book_id`, `seller_name`, `unit_price` |
| Protected attribute | `self._name` | `self._repository`, `self._settings` |
| Public attribute | `self.name` | `self.book_id`, `self.created_at` |
| Constant | `UPPER_SNAKE_CASE` | `MAX_PHONE_LENGTH = 15`, `DEFAULT_PAGE_SIZE = 20` |
| File | `snake_case.py` | `inventory_service.py`, `book_repository.py` |

- Never use an `m_` prefix for instance attributes — use `self._name` for protected, `self.name` for public.
- Never use PascalCase or camelCase for method or variable names in Python.

### TypeScript / React Frontend — TypeScript Conventions

| Element | Convention | Example |
|---------|-----------|---------|
| Component / page file | `PascalCase.tsx` | `InventoryPage.tsx`, `BookCard.tsx` |
| Hook / service / util file | `camelCase.ts` | `useInventory.ts`, `bookService.ts`, `formatCurrency.ts` |
| Types file | `camelCase.ts` in `src/types/` | `inventory.ts`, `sales.ts`, `index.ts` |
| Class / Interface / Type | `PascalCase` inside `namespace BookRover` | `BookRover.Book`, `BookRover.SaleItem` |
| React component name | `PascalCase` (top-level export) | `BookCard`, `SaleTable`, `NewBuyerPage` |
| Method / function | `camelCase` | `createBook()`, `formatCurrency()`, `handleSubmit()` |
| Variable / parameter | `camelCase` | `bookId`, `sellerName`, `unitPrice` |
| Constant | `UPPER_SNAKE_CASE` | `MAX_PHONE_LENGTH`, `DEFAULT_PAGE_SIZE` |

### DynamoDB — Database Layer

| Element | Convention | Example |
|---------|-----------|---------|
| Table name | `kebab-case-<env>` | `bookrover-books-dev`, `bookrover-sales-prod` |
| Attribute name | `snake_case` | `book_id`, `seller_id`, `created_at` |
| GSI name | `kebab-case-index` | `seller-id-index`, `bookstore-id-index` |

---

## Architecture Diagrams — PlantUML

### Tooling

- **Format**: PlantUML (`.puml` files) — chosen for its full 4+1 view coverage and native arc42 compatibility.
- **VS Code**: use the PlantUML extension for local preview.
- **GitHub rendering**: PlantUML does not render natively in GitHub markdown. Solve by committing both the `.puml` source and the generated `.png` image alongside it.

### File and Folder Conventions

- Every arc42 section that contains diagrams gets a `diagrams/` subfolder.
- Source file naming: `<view>_<description>.puml` — e.g., `context_system_context.puml`, `logical_domain_classes.puml`.
- Generated image naming: same base name, `.png` extension — e.g., `context_system_context.png`.
- Reference the PNG in the section's `.md` file using a relative path:
  ```markdown
  ![System Context](./diagrams/context_system_context.png)
  ```
- The `.puml` file is the **source of truth** — always edit the `.puml`, regenerate the `.png`, commit both together.

### Generate + Commit PNG Workflow

1. Edit the `.puml` file in VS Code.
2. Preview using the PlantUML extension (`Alt+D`).
3. Export to PNG: right-click in the `.puml` file → "Export Current Diagram" → save as `.png` in the same `diagrams/` folder.
4. Commit both files together:
   ```
   git add docs/<section>/diagrams/<name>.puml docs/<section>/diagrams/<name>.png
   git commit -m "docs(<section>): add/update <description> diagram"
   ```

### PlantUML Style Conventions

- Always begin with `!theme plain` for clean, professional output.
- Always include a `title` directive.
- Use `skinparam` for consistent font and arrow styling across all diagrams.
- Group related elements inside `package`, `component`, or `namespace` blocks.
- Use `note` blocks sparingly — only for non-obvious decisions.
- Keep diagrams focused: one diagram per concern. Do not try to show everything in one diagram.

### Standard Header (apply to every `.puml` file)

```plantuml
@startuml
!theme plain
skinparam defaultFontName Segoe UI
skinparam defaultFontSize 13
skinparam ArrowColor #444444
skinparam shadowing false
title <Diagram Title>

' ... diagram content ...

@enduml
```

---

## 4+1 View → arc42 Mapping

The 4+1 architectural view model maps onto arc42 sections as follows. Use this as the guide for where to create PlantUML diagrams.

### View Assignments

| 4+1 View | What It Describes | arc42 Section | PlantUML Diagram Types |
|---|---|---|---|
| **+1 Scenarios** (Use Case view) | Use cases that drive and validate all other views | `01_introduction_and_goals/` | Use case diagram |
| **Logical view** | Domain entities, their static relationships, Pydantic models | `05_building_block_view/` Level 1 & 2 | Class diagram, object diagram |
| **Development view** | Code layers, package structure, module dependencies | `05_building_block_view/` Level 2+ | Component diagram, package diagram |
| **Process view** | Runtime sequences, interactions, state transitions | `06_runtime_view/` | Sequence diagram, activity diagram, state diagram |
| **Physical view** | Deployment topology — AWS infrastructure, network | `07_deployment_view/` | Deployment diagram, C4 container diagram |
| **Context** | System boundary — what is inside vs outside BookRover | `03_context_and_scope/` | Context diagram (C4 Level 1) |

### Sections That Don't Belong to a Single View

These arc42 sections are cross-cutting framing — they inform all 4+1 views but are not a view themselves:

| arc42 Section | Role |
|---|---|
| `02_constraints/` | Technical and organisational constraints that bound every view |
| `03_context_and_scope/` | System boundary — what is inside vs outside (feeds the Context diagram) |
| `04_solution_strategy/` | Key decisions that shape the architecture across all views |
| `08_cross_cutting_concepts/` | Layering rules, error handling, logging — applied across all views |
| `09_architecture_decisions/` | ADRs — the *why* behind decisions visible in all views |
| `10_quality_requirements/` | Quality scenarios that the +1 Scenarios view must satisfy |
| `11_risks_and_technical_debt/` | Gaps and risks across all views |
| `12_glossary/` | Vocabulary used across all views |

### BookRover Diagram Inventory

| 4+1 View | Diagram | File | Section |
|---|---|---|---|
| +1 Scenarios | Use case: all actors + primary use cases | `01_introduction_and_goals/diagrams/scenarios_use_cases.puml` | `01_introduction_and_goals/` |
| Context | System context: BookRover ↔ actors + external systems | `03_context_and_scope/diagrams/context_system_context.puml` | `03_context_and_scope/` |
| Logical | Domain class diagram: all entities + relationships | `05_building_block_view/diagrams/logical/logical_domain_classes.puml` | `05_building_block_view/` |
| Development | Component diagram: bookrover package layers | `05_building_block_view/diagrams/development/development_layers.puml` | `05_building_block_view/` |
| Physical | Deployment diagram: full AWS infrastructure | `07_deployment_view/diagrams/physical_aws_deployment.puml` | `07_deployment_view/` |
| Process | Sequence: Create Sale flow | `06_runtime_view/diagrams/process/process_create_sale.puml` | `06_runtime_view/` |
| Process | Sequence: Submit Return flow | `06_runtime_view/diagrams/process/process_submit_return.puml` | `06_runtime_view/` |

> Process diagrams are added separately. All other diagrams must exist before any code is written.

---

## Environment Separation

- Environments: `dev` and `prod`.
- Controlled by `APP_ENV` environment variable (`"dev"` | `"prod"`).
- DynamoDB table names: `bookrover-<entity>-<env>` (e.g., `bookrover-books-dev`).
- Lambda function names: `bookrover-api-dev`, `bookrover-api-prod`.
- CloudFront distributions: separate per environment.
- **No production data in dev** — ever.
- Log level: `DEBUG` in dev, `INFO` in prod.
