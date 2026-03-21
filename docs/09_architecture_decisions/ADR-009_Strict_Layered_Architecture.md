# ADR-009: Strict Layered Architecture with Abstract Base Classes

**Status**: Accepted

---

## Context

A layered backend alone is not sufficient if layers can still directly import concrete implementations from adjacent layers. Without enforced abstractions, any layer can accidentally depend on internal details of another, making isolated testing impossible and refactoring risky. Every layer must be independently testable — swapping a concrete implementation must require zero changes to calling layers.

---

## Decision

Enforce strict one-way dependencies through Abstract Base Classes (ABCs) in a dedicated `interfaces/` module. Domain exceptions defined in `exceptions/` are the only artefacts that cross layer boundaries.

---

## Layer Contract

```
Router    →  AbstractXxxService      (from interfaces/)
Service   →  AbstractXxxRepository   (from interfaces/)
Repository →  DynamoDB               (boto3 only)
```

Concrete classes are injected at runtime via FastAPI `Depends()` — never imported directly by the calling layer.

---

## Rules Enforced

- No layer imports a concrete class from an adjacent layer — only the ABC.
- Repositories raise domain exceptions (`exceptions/`) — never boto3 `ClientError`.
- Routers catch only domain exceptions — boto3 errors never propagate above the repository.
- Raw DynamoDB response dicts never leave the repository layer.
- Pydantic HTTP request/response models never enter the service or repository layer.

---

## Data Flow at Each Boundary

| Boundary | What Passes |
|----------|------------|
| Router → Service | Typed primitive arguments extracted from the Pydantic request model |
| Service → Router | Pydantic response model — never a raw dict |
| Service → Repository | Primitive types: IDs (str), names (str), amounts (Decimal) |
| Repository → Service | Typed domain data (dataclass or typed dict) — never a raw DynamoDB response |

---

## Rationale

- Routers can be unit-tested with a mocked service ABC — no database, no moto needed.
- Services can be unit-tested with a mocked repository ABC — no DynamoDB, no moto needed.
- Integration tests wire all layers together, mocking only DynamoDB via `moto`.
- Swapping DynamoDB for another store requires changes only in `repositories/` and `interfaces/` — zero changes to services or routers.

---

## Trade-offs Accepted

More upfront boilerplate: ABCs + exceptions module + explicit data conversion at boundaries. This cost is paid once and prevents a much larger cost of untestable, tightly-coupled code as the codebase grows.
