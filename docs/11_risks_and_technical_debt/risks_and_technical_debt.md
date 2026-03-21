# arc42 — Section 11: Risks and Technical Debt

## 11.1 Risks

| ID | Risk | Likelihood | Impact | Mitigation |
|----|------|-----------|--------|------------|
| R-1 | **No authentication in phases 1–5** | Medium | High (anyone with the URL can access the app) | Keep CloudFront URL private until Phase 6; do not share the URL publicly |
| R-2 | **DynamoDB race condition on concurrent sales** | Low | High (negative inventory count) | Use DynamoDB `UpdateExpression` with `ConditionExpression` — atomic operation prevents concurrent overselling |
| R-3 | **moto_server data loss on restart** | High | Low (dev only) | Expected behavior; automated tests use in-memory moto; data loss only affects manual dev testing sessions |
| R-4 | **Lambda cold start latency** | Medium | Low (< 1 second) | Acceptable for non-latency-critical internal tool; future mitigation: Lambda provisioned concurrency if needed |
| R-5 | **Seller accidentally submits return twice** | Low | High (inventory cleared twice) | `POST /returns` checks if seller has any inventory before creating return; idempotent guard on return submission |
| R-6 | **Group leader deleted while sellers are assigned** | Low | High (orphaned sellers) | `DELETE /admin/group-leaders/{id}` returns 409 Conflict if active sellers exist |
| R-7 | **AWS free tier exceeded unexpectedly** | Very Low | Medium (unexpected bill) | Set AWS Billing Alert at $5/month threshold in CloudWatch; all services well within free tier at friend-group scale |

---

## 11.2 Technical Debt

| ID | Debt | Reason Accepted | Resolution Plan |
|----|------|----------------|-----------------|
| TD-1 | **No authentication (Phase 1–5)** | Scope control — auth adds significant complexity; core features must work first | Phase 6: Gmail OAuth via Cognito |
| TD-2 | **No Terraform IaC (Phase 1–6)** | Manual Console setup first to understand resources before codifying them | Phase 7: Terraform modules to codify all resources |
| TD-3 | **moto_server instead of DynamoDB Local** | Docker Desktop not yet permitted on developer's laptop | Replace with DynamoDB Local Docker once permissions obtained |
| TD-4 | **No CI/CD pipeline** | Keeping setup simple in early phases | Future: GitHub Actions for lint, test, deploy on PR merge |
| TD-5 | **No API versioning** | Single-client app; no versioning needed now | Add `/v1/` prefix if breaking changes become necessary |
| TD-6 | **Role-selector placeholder for auth (dev mode)** | Auth deferred to Phase 6 | Remove placeholder; replace with Cognito JWT validation |
| TD-7 | **Dashboard aggregation done in Lambda (not pre-computed)** | Low traffic; real-time aggregation is acceptable now | If dashboard becomes slow, add DynamoDB Streams + pre-aggregated table |

---

## 11.3 AWS Billing Safety Net

To avoid unexpected AWS charges during development:

1. **Set a billing alert**: AWS Console → Billing → Budgets → Create Budget → $5/month alert → notify via email.
2. **Use dev tables only** during development (`bookrover-*-dev`).
3. **Test locally** (moto_server) — zero AWS calls during development.
4. **Only hit real AWS** during the smoke test phase (Phase 5) and rollout.
