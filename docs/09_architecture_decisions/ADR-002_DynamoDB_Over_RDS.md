# ADR-002: DynamoDB over RDS

**Status**: Accepted

---

## Context

The backend requires a persistent database. Cost must be near $0 at low usage. No database administration overhead is acceptable.

---

## Options Considered

| Option | Monthly Cost (idle) | Ops Overhead |
|--------|-------------------|-------------|
| RDS PostgreSQL (db.t3.micro) | ~$15/month | Backups, patches, connection pooling |
| Aurora Serverless v2 | ~$0 idle but minimum ACU cost applies | Medium |
| DynamoDB on-demand | $0 at low usage (always free tier) | None |

---

## Decision

DynamoDB with on-demand billing.

---

## Rationale

- Zero idle cost — billed only per read/write operation.
- Fully serverless — no database server to manage, patch, or scale.
- Native AWS service — integrates directly with Lambda via boto3 without connection pooling.
- Always free tier: 25 GB storage + 25 WCU + 25 RCU permanently free.
- DynamoDB Local and `moto` provide identical local development and test environments.

---

## Trade-offs Accepted

- No SQL joins or cross-table transactions.
  - Mitigated by embedding `SaleItem` lists inside the `Sale` document.
  - Mitigated by snapshotting key values (`book_name`, `price`) at transaction time so historical records are self-contained.
- Requires upfront access pattern design (GSIs must be planned before table creation).
- Multi-table design chosen over single-table design for readability — see ADR-004.
