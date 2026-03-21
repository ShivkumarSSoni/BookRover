# ADR-004: Multi-Table DynamoDB Design

**Status**: Accepted

---

## Context

DynamoDB supports two dominant design approaches: single-table design (all entities in one table, differentiated by key prefixes) and multi-table design (one table per entity type, matching relational mental models).

---

## Options Considered

| Approach | Complexity | Readability | AWS Console Manageability |
|----------|-----------|-------------|--------------------------|
| Single-table design | High (requires deep DynamoDB expertise) | Low | Difficult |
| Multi-table design | Low | High | Easy |

---

## Decision

Multi-table design — one DynamoDB table per entity type.

---

## Rationale

- Multi-table design maps directly to the mental model already established in the data models spec — one table per business entity.
- Easier to set up, inspect, and manage via the AWS Console during manual setup.
- Each table's access patterns are clearly scoped, making GSI design straightforward.
- No discipline overhead required to maintain key prefix conventions (a common source of bugs in single-table designs).

---

## Trade-offs Accepted

- More tables to create and manage (7 tables). At this scale, negligible.
- Cross-entity queries require multiple DynamoDB calls in the service layer (e.g., fetching seller + bookstore in one request). Acceptable given low read volumes.
- Single-table design can be revisited in the future if dashboard aggregation performance becomes a concern — see `11_risks_and_technical_debt`.
