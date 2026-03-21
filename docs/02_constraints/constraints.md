# arc42 — Section 2: Constraints

## 2.1 Technical Constraints

| Constraint | Reason |
|------------|--------|
| **Backend must be Python** | Developer's chosen language; AWS Lambda has excellent Python support |
| **Frontend must be React** | Modern, mobile-friendly, component-based UI |
| **Hosted exclusively on AWS** | Developer's SAA-C03 learning objective |
| **AWS-native, serverless-first** | Minimum cost — no EC2, no containers, no idle server charges |
| **No SQL database** | DynamoDB chosen for serverless, cost-minimal NoSQL — no RDS provisioned capacity costs |
| **Mobile browser only** | End users (sellers) access app from phone browsers — no native app |
| **HTTPS enforced** | AWS CloudFront enforces HTTPS; no plain HTTP in production |
| **GitHub as source control** | All code versioned and pushed to GitHub from day one |

---

## 2.2 Organizational Constraints

| Constraint | Reason |
|------------|--------|
| **Cost must stay near $0/month** | Project is self-funded by a group of friends; no budget for hosting |
| **No Docker Desktop initially** | Developer's laptop requires IT permissions for Docker installation; use `moto_server` as interim DynamoDB substitute |
| **Authentication deferred to Phase 6** | Gmail/Google OAuth via Cognito will be added after core features are working. Development uses a role-selector placeholder. |
| **No ALB / multi-AZ configuration** | Lambda + API Gateway are inherently multi-AZ; ALB adds cost (~$16/month minimum) without benefit at this scale |
| **Route 53 / custom domain deferred** | $0.50/month cost is avoided until real users need a memorable URL; use free CloudFront URL in the meantime |
| **Terraform IaC deferred to Phase 7** | Manual AWS Console setup first for learning; Terraform codifies what is already understood |

---

## 2.3 Conventions Adopted

| Convention | Decision |
|------------|----------|
| **Code style — Python** | `black` for formatting, `ruff` for linting |
| **Code style — React** | `ESLint` + `Prettier` |
| **API style** | RESTful over HTTP; JSON request/response; explicit HTTP status codes |
| **Commit messages** | Conventional Commits format: `<type>(<scope>): <description>` |
| **Branch strategy** | Feature branches + pull requests; no direct commits to `main` |
| **Environment naming** | `dev` and `prod`; controlled by `APP_ENV` environment variable |
| **AWS region** | `ap-south-1` (Mumbai) — lowest latency for India-based users |
| **Currency display** | Indian Rupee `₹`; configurable via env variable for future flexibility |
| **All timestamps** | ISO 8601 UTC format (`2026-03-21T10:00:00Z`) |
| **All IDs** | UUID v4 strings |
