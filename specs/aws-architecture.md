# BookRover — AWS Architecture

## Architecture Overview

BookRover is a **fully serverless, AWS-native** application. There is no server to manage, no idle compute cost, and no infrastructure to patch. Every AWS service choice is justified by cost, simplicity, and alignment with the AWS Well-Architected Framework.

---

## Architecture Diagram (Text)

```
                        ┌─────────────────────────────────────┐
                        │           User's Phone Browser       │
                        └──────────────┬──────────────────────┘
                                       │ HTTPS
                        ┌──────────────▼──────────────────────┐
                        │           AWS CloudFront              │
                        │  (CDN + HTTPS termination + caching)  │
                        └──────────┬───────────────┬───────────┘
                                   │               │
                     Static Files  │               │  API Requests
                     (React build) │               │  (/api/*)
                                   │               │
                    ┌──────────────▼──┐   ┌────────▼────────────┐
                    │    AWS S3       │   │  API Gateway         │
                    │  (React SPA)    │   │  (HTTP API)          │
                    └─────────────────┘   └────────┬────────────┘
                                                   │ Invoke
                                          ┌────────▼────────────┐
                                          │   AWS Lambda         │
                                          │  (FastAPI + Mangum)  │
                                          └────────┬────────────┘
                                                   │ Read/Write
                                          ┌────────▼────────────┐
                                          │   AWS DynamoDB       │
                                          │  (7 tables)          │
                                          └─────────────────────┘

Supporting Services:
  ┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐
  │  AWS CloudWatch  │   │    AWS IAM        │   │  AWS Cognito     │
  │  (Logs/Metrics)  │   │ (Roles/Policies)  │   │ (Auth - deferred)│
  └──────────────────┘   └──────────────────┘   └──────────────────┘
  ┌──────────────────┐   ┌──────────────────┐
  │  AWS ACM         │   │  AWS Route 53    │
  │  (SSL Cert)      │   │  (Custom Domain  │
  └──────────────────┘   │   - optional)    │
                         └──────────────────┘
```

---

## AWS Services — Detail

### 1. Amazon S3 (Simple Storage Service)

**Purpose**: Hosts the React frontend as a static website.

**Configuration**:
- Bucket name: `bookrover-frontend-<env>` (e.g., `bookrover-frontend-prod`)
- **Block all public access** — objects are NOT publicly accessible directly.
- CloudFront accesses S3 via **Origin Access Control (OAC)** — the only secure way.
- Versioning: enabled (easy rollback on bad frontend deploy).
- Lifecycle policy: delete old versions after 30 days (cost control).

**SAA-C03 Topics Covered**: S3 bucket policies, OAC, static website hosting, versioning, lifecycle policies.

**Cost**: ~$0.023/GB/month storage. At <10MB React build = effectively $0.

---

### 2. Amazon CloudFront

**Purpose**: Global CDN for the React frontend. Enforces HTTPS. Routes API calls to API Gateway.

**Configuration**:
- **Origin 1 (Default)**: S3 bucket → serves React SPA (all routes return `index.html` via custom error page for 403/404).
- **Origin 2 (API)**: API Gateway endpoint → for `/api/*` path pattern.
- **HTTPS only**: redirect HTTP to HTTPS.
- **Cache policy**: `CachingDisabled` for `/api/*`; `CachingOptimized` for static assets.
- **Custom domain**: `bookreover.yourdomain.com` via Route 53 + ACM certificate.
- **Price class**: `PriceClass_100` (US, Europe, Asia) for cost control.
- Default root object: `index.html`.
- Custom error pages: 403 → `/index.html` (200), 404 → `/index.html` (200) — required for React Router.

**SAA-C03 Topics Covered**: CloudFront origins, cache behaviors, OAC, HTTPS, custom domains, price classes, error pages.

**Cost**: ~$0.0085/10K HTTPS requests. Extremely low for small usage.

---

### 3. AWS API Gateway (HTTP API)

**Purpose**: Exposes the FastAPI Lambda as HTTP endpoints. Routes requests from CloudFront to Lambda.

**Configuration**:
- Type: **HTTP API** (not REST API — cheaper, faster, simpler for this use case).
- Integration: **Lambda proxy** — passes the full HTTP request to Lambda.
- Stage: `dev` and `prod` as separate stages (or separate deployments).
- **CORS**: configured at API Gateway to allow the CloudFront domain.
- Throttling: default 10,000 requests/second (sufficient for friend-group scale).
- No API keys required (auth is handled by Cognito in Phase 6).

**SAA-C03 Topics Covered**: API Gateway HTTP API vs REST API trade-offs, Lambda proxy integration, CORS, throttling.

**Cost**: $1.00/million API calls. At small usage = effectively $0.

---

### 4. AWS Lambda

**Purpose**: Runs the FastAPI Python backend. Stateless, scales automatically.

**Configuration**:
- Runtime: **Python 3.12**
- Handler: `app.main.handler` (Mangum wraps FastAPI as a Lambda handler)
- Memory: **256 MB** (sufficient for FastAPI + boto3; adjust if needed)
- Timeout: **30 seconds** (DynamoDB operations are fast; 30s is generous)
- Environment variables:
  - `APP_ENV` = `dev` or `prod`
  - `DYNAMODB_REGION` = `ap-south-1` (Mumbai — closest to India)
  - `TABLE_PREFIX` = `bookrover`
- **Execution role**: custom IAM role with only DynamoDB CRUD on BookRover tables.
- Layers: dependencies (boto3 pre-installed in Lambda; only app-specific packages in layer).
- Deployment package: zip of `backend/` folder.

**Cold starts**: FastAPI + Mangum typically cold-starts in < 1 second. Acceptable for this use case.

**SAA-C03 Topics Covered**: Lambda runtime, memory/timeout configuration, execution roles, environment variables, deployment packages, cold starts.

**Cost**: First 1 million requests/month **FREE** (always free tier). After that, $0.20/million. = $0 for friend-group usage.

---

### 5. Amazon DynamoDB

**Purpose**: Primary database. Stores all app data (7 tables).

**Configuration**:
- Billing mode: **On-demand** (PAY_PER_REQUEST) — no provisioned capacity needed.
- Tables: see Data Models spec for full list.
- **Global Secondary Indexes (GSIs)**: as defined in data-models.md.
- Region: `ap-south-1` (Mumbai).
- Point-in-time recovery (PITR): enabled on prod tables (protects against accidental data loss).
- Encryption: AWS-managed keys (SSE enabled by default).

**SAA-C03 Topics Covered**: DynamoDB on-demand vs provisioned, GSIs, PITR, encryption at rest, partition key design.

**Cost**: First 25 GB storage + 25 WCU + 25 RCU **FREE forever** (always free tier). On-demand at small scale = $0.

---

### 6. AWS Cognito (Deferred — Phase 6)

**Purpose**: Manages user authentication via Google/Gmail OAuth federation.

**Configuration** (when implemented):
- User Pool: `bookrover-users-<env>`
- Identity Provider: Google (OAuth 2.0)
- App client: configured for the React frontend (Cognito Hosted UI or custom login page)
- JWT tokens: used to authorize API Gateway requests
- User groups: `admin`, `group-leader`, `seller` — mapped to app roles
- API Gateway: configured with Cognito authorizer — validates JWT on every request

**SAA-C03 Topics Covered**: Cognito User Pools, Identity Providers, OAuth 2.0 federation, JWT, API Gateway authorizers.

**Cost**: First 50,000 MAU **FREE**. = $0 for this app.

---

### 7. AWS CloudWatch

**Purpose**: Centralized logging and monitoring for Lambda and API Gateway.

**Configuration**:
- Lambda automatically ships logs to CloudWatch Log Groups: `/aws/lambda/bookrover-api-<env>`
- Log retention: 7 days for dev, 30 days for prod (cost control).
- API Gateway access logs: enabled, shipping to CloudWatch.
- **Alarms**: 
  - Lambda error rate > 1% → alert (via email via SNS).
  - Lambda duration > 5 seconds → alert.

**SAA-C03 Topics Covered**: CloudWatch Logs, Log Groups, retention policies, alarms, SNS notifications.

**Cost**: First 5 GB logs/month **FREE**. Alarms: $0.10/alarm/month. = ~$0.20/month.

---

### 8. AWS IAM (Identity and Access Management)

**Purpose**: Controls what each AWS service can do. Enforces least privilege.

**Key Roles**:

`bookrover-lambda-execution-role`:
- `AWSLambdaBasicExecutionRole` (CloudWatch Logs permissions)
- Custom inline policy: DynamoDB `PutItem`, `GetItem`, `UpdateItem`, `DeleteItem`, `Query`, `Scan` on `arn:aws:dynamodb:ap-south-1:*:table/bookrover-*` only.

`bookrover-cloudfront-s3-oac`:
- S3 `GetObject` on the frontend bucket only.

**SAA-C03 Topics Covered**: IAM roles, policies, least privilege principle, resource-based policies, trust relationships.

**Cost**: IAM is free.

---

### 9. AWS Certificate Manager (ACM)

**Purpose**: Free SSL/TLS certificate for the custom domain.

**Configuration**:
- Certificate region: **us-east-1** (required for CloudFront — must be in us-east-1 regardless of app region).
- Domain: `bookreover.yourdomain.com` and `api.bookreover.yourdomain.com`.
- Validation: DNS validation via Route 53 (automatic).

**SAA-C03 Topics Covered**: ACM, certificate regions, DNS validation, HTTPS.

**Cost**: ACM certificates are **FREE**.

---

### 10. Amazon Route 53 (Optional)

**Purpose**: DNS management for custom domain.

**Configuration**:
- Hosted zone for your domain.
- A record (alias): `bookreover.yourdomain.com` → CloudFront distribution.

**SAA-C03 Topics Covered**: Route 53 hosted zones, alias records, routing policies.

**Cost**: $0.50/hosted zone/month. $0.40/million DNS queries. = ~$0.50/month.

---

## AWS Region Choice

**Primary Region**: `ap-south-1` (Mumbai, India)

**Why**: 
- Lowest latency for users in India.
- All DynamoDB tables, Lambda, and API Gateway in Mumbai.
- ACM certificate in `us-east-1` (CloudFront requirement only).
- S3 bucket can be in any region; `ap-south-1` for consistency.

---

## Cost Estimate (Monthly)

| Service | Cost |
|---------|------|
| S3 | ~$0.00 (< 100MB) |
| CloudFront | ~$0.00 (< 10K requests/month) |
| API Gateway | ~$0.00 (< 1M requests/month — free tier) |
| Lambda | $0.00 (< 1M requests/month — always free) |
| DynamoDB | $0.00 (< 25 GB — always free) |
| CloudWatch | ~$0.00 (< 5 GB logs — free tier) |
| IAM | $0.00 (always free) |
| ACM | $0.00 (always free) |
| Route 53 | ~$0.50/month (optional) |
| **Total** | **~$0 – $0.50/month** |

---

## Manual AWS Console Setup Order

Set up in this order to avoid dependency issues:

```
Step 1:  IAM — Create Lambda execution role + policies
Step 2:  DynamoDB — Create all 7 tables + GSIs
Step 3:  Lambda — Create function, upload code, configure env vars + role
Step 4:  API Gateway — Create HTTP API, Lambda integration, CORS config
Step 5:  S3 — Create frontend bucket, block public access
Step 6:  ACM — Request SSL certificate (us-east-1), validate via DNS
Step 7:  CloudFront — Create distribution (S3 origin + API Gateway origin), attach cert
Step 8:  Route 53 — Create A record pointing to CloudFront (optional)
Step 9:  Deploy React build to S3
Step 10: Test end-to-end via CloudFront URL
```

Detailed Console steps for each will be documented in `/docs/aws-setup-guide.md` (created during Phase 4).

---

## SAA-C03 Exam Topic Mapping

| Exam Domain | BookRover Service | Concept Applied |
|-------------|------------------|-----------------|
| Design Resilient Architectures | DynamoDB on-demand, Lambda | Auto-scaling, no single point of failure |
| Design High-Performing Architectures | CloudFront CDN, API Gateway HTTP API | Low latency, edge caching |
| Design Secure Applications | IAM least privilege, OAC, HTTPS, Cognito | Identity, access control, encryption in transit |
| Design Cost-Optimized Architectures | Serverless (Lambda, DynamoDB on-demand, S3) | Pay-per-use, no idle cost |
| Networking | CloudFront behaviors, API Gateway, Route 53 | Content delivery, DNS, HTTPS |
| Storage | S3 (static hosting), DynamoDB (NoSQL) | Object storage, serverless database |
| Compute | Lambda (serverless functions) | Event-driven compute |
| Monitoring | CloudWatch Logs, Alarms, Metrics | Observability, operational excellence |

---

## Future: Terraform IaC

When you are ready to codify the manual setup into Terraform, the infrastructure will be defined in `/infra/`:

```
infra/
├── main.tf
├── variables.tf
├── outputs.tf
├── modules/
│   ├── dynamodb/
│   ├── lambda/
│   ├── api_gateway/
│   ├── s3_cloudfront/
│   └── iam/
└── environments/
    ├── dev.tfvars
    └── prod.tfvars
```

Each Terraform module will directly mirror what you set up manually in the Console — your hands-on knowledge directly transfers to IaC.
