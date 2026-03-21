# arc42 — Section 10: Quality Requirements

## 10.1 Quality Tree

```
BookRover Quality
├── Usability
│   ├── Mobile-first (375px and above)
│   ├── Zero-training for sellers
│   └── Touch-friendly (min 44×44px targets)
├── Correctness
│   ├── Inventory counts always accurate
│   ├── Money totals always accurate
│   └── Business rules enforced (no overselling, switch-lock)
├── Performance
│   ├── Page load < 2 seconds
│   └── API response < 500ms
├── Cost
│   ├── AWS bill ~$0/month at friend-group scale
│   └── No idle compute charges
├── Maintainability
│   ├── ≥ 80% test coverage on services + routers
│   ├── SOLID + Clean Code principles
│   └── Conventional Commits + feature branches
└── Security
    ├── HTTPS enforced
    ├── No PII in logs
    ├── IAM least privilege
    └── Input validation on all endpoints
```

---

## 10.2 Quality Scenarios

Quality scenarios make abstract goals concrete and testable.

### Usability

| ID | Scenario | Stimulus | Response | Measure |
|----|----------|----------|----------|---------|
| U-1 | Seller records a sale at a door | Seller taps + on 3 books, fills buyer name and phone, taps Save | Sale saved; page resets for next buyer | ≤ 5 taps; ≤ 10 seconds total |
| U-2 | First-time seller registers | Seller opens app; sees Register page | Fills name, email, selects group leader + bookstore; taps Register | Completed without help or documentation |
| U-3 | Page renders on low-end Android phone | App opened on 375px screen | All text readable; buttons tappable; no horizontal scroll | Passes on Chrome Mobile at 375px |

### Correctness

| ID | Scenario | Stimulus | Response | Measure |
|----|----------|----------|----------|---------|
| C-1 | Seller tries to sell more books than in stock | Quantity exceeds `current_count` | API returns 400; UI shows error; inventory unchanged | 100% of attempts blocked |
| C-2 | Two concurrent sale requests for same book | Race condition on `current_count` | DynamoDB atomic `UpdateExpression` prevents negative count | No negative inventory ever |
| C-3 | Seller requests switch without completing return | Switch requested with outstanding inventory | API returns 409; switch blocked | 100% of attempts blocked |

### Performance

| ID | Scenario | Stimulus | Response | Measure |
|----|----------|----------|----------|---------|
| P-1 | Seller loads New Buyer page | GET /sellers/{id}/inventory | Page fully rendered with all books | < 2 seconds end-to-end |
| P-2 | Save Sale API call | POST /sellers/{id}/sales | 201 response returned | < 500ms (excluding network) |
| P-3 | Group leader opens dashboard | GET /group-leaders/{id}/dashboard | Dashboard rendered with all sellers | < 2 seconds end-to-end |

### Cost

| ID | Scenario | Stimulus | Response | Measure |
|----|----------|----------|----------|---------|
| K-1 | App sits idle for a month | No user activity | No charges incurred | $0 Lambda + DynamoDB + API Gateway |
| K-2 | 5 sellers make 20 sales each in a day | 100 sale transactions | AWS charges incurred | < $0.01 for 100 requests |

### Maintainability

| ID | Scenario | Stimulus | Response | Measure |
|----|----------|----------|----------|---------|
| M-1 | New endpoint added to API | Developer adds a new route | Service and repository layers isolated; tests written | New feature deployed without touching existing tests |
| M-2 | DynamoDB table name changes | `TABLE_PREFIX` env var updated | All table names update automatically | Zero code changes required |
| M-3 | Test suite run | `pytest` executed | All tests pass | ≥ 80% coverage on `services/` and `routers/` |
