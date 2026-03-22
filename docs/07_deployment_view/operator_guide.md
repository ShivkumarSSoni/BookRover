# BookRover — Operator Guide

This guide covers everything needed to deploy and operate a BookRover instance — whether you are the original author hosting in your own AWS account, or an independent operator who has cloned the public repository and is hosting it in a separate AWS account.

Each operator controls their own deployment entirely. There is no shared infrastructure between deployments.

---

## 1. Concepts

### The Operator

An **operator** is the person who deploys and administers a BookRover instance. The operator:

- Controls the AWS account where the app runs.
- Sets the `ADMIN_EMAILS` environment variable to designate who can access the Admin panel.
- Is responsible for all operational costs (Lambda invocations, DynamoDB, S3, CloudFront).

### Admin Bootstrap

BookRover has no mechanism for self-service admin registration. Admin identity is declared via an environment variable (`ADMIN_EMAILS`), not stored in a database. This is a deliberate security decision — see [ADR-010](../09_architecture_decisions/ADR-010_Admin_Bootstrap.md) for the rationale.

**Why an env var instead of a database record?**

- Chicken-and-egg: the first admin cannot be created by an admin that does not yet exist.
- Environment variables on AWS Lambda are only modifiable by the AWS account owner — no code path can alter them.
- No UI exists that could be exploited to grant admin access to an unintended user.

---

## 2. First-Time Deployment (Your Own AWS Account)

### Step 1 — Clone the repository

```bash
git clone https://github.com/ShivkumarSSoni/BookRover.git
cd BookRover
```

If you are a different operator, fork the repository first, then clone your fork.

### Step 2 — Deploy backend to AWS Lambda

Follow the architecture described in [deployment_view.md](./deployment_view.md). At minimum you need:

- An AWS Lambda function running the `bookrover` FastAPI app via Mangum.
- An API Gateway HTTP API fronting the Lambda.
- DynamoDB tables for each entity (created automatically on first Lambda cold start when `APP_ENV=dev`, or provisioned via IaC in production).

### Step 3 — Set the ADMIN_EMAILS environment variable

In the AWS Lambda console (or your IaC tool):

1. Go to your Lambda function → **Configuration** → **Environment variables**.
2. Add the variable:

   | Key | Value |
   |-----|-------|
   | `ADMIN_EMAILS` | `youremail@example.com` |

   Multiple admins — comma-separated:

   | Key | Value |
   |-----|-------|
   | `ADMIN_EMAILS` | `admin1@example.com,admin2@example.com` |

3. Save. No redeployment is needed — Lambda reads environment variables on each invocation.

### Step 4 — Deploy frontend to S3 + CloudFront

Build the React app and upload to S3:

```bash
cd frontend
npm install
npm run build
aws s3 sync dist/ s3://your-bucket-name --delete
```

Invalidate the CloudFront cache after each deploy:

```bash
aws cloudfront create-invalidation --distribution-id YOUR_DIST_ID --paths "/*"
```

### Step 5 — First login as Admin

1. Navigate to your CloudFront URL (e.g. `https://d1234abcd.cloudfront.net`).
2. Sign in using the email address you put in `ADMIN_EMAILS`.
3. The backend's `GET /me` endpoint will find your email in `ADMIN_EMAILS` and return `role: admin`.
4. You will be routed to `/admin` automatically.
5. From `/admin`, create bookstores and group leaders.

After this first login, the app is operational. Group leaders can sign up themselves using their email — they will be matched to the group leader record you created by email address.

---

## 3. Environment Variables Reference

### Backend (Lambda environment variables)

| Variable | Required | Example | Description |
|----------|----------|---------|-------------|
| `APP_ENV` | Yes | `prod` | `dev` or `prod`. Controls log level and table name suffix. |
| `ADMIN_EMAILS` | Yes | `you@example.com` | Comma-separated list of email addresses with admin access. |
| `TABLE_PREFIX` | Yes | `bookrover` | DynamoDB table name prefix. Tables are named `{prefix}-{entity}-{env}`. |
| `DYNAMODB_REGION` | Yes | `ap-south-1` | AWS region where DynamoDB tables are provisioned. |
| `DYNAMODB_ENDPOINT_URL` | Dev only | `http://localhost:8001` | Local moto server endpoint. Leave blank in production. |
| `CORS_ALLOWED_ORIGINS` | Yes | `["https://d1234.cloudfront.net"]` | Frontend origin(s) allowed to call the API. Use `["*"]` only in dev. |

### Frontend (Vite build-time variables)

| Variable | Required | Example | Description |
|----------|----------|---------|-------------|
| `VITE_API_BASE_URL` | Yes | `https://api.yourdomain.com` | API Gateway base URL. |
| `VITE_AUTH_MODE` | Yes | `cognito` | `mock` (dev) or `cognito` (prod). Controls the authentication flow. |
| `VITE_COGNITO_USER_POOL_ID` | Prod only | `ap-south-1_XXXXXXX` | Cognito User Pool ID. |
| `VITE_COGNITO_CLIENT_ID` | Prod only | `1abc2defg3hij` | Cognito App Client ID. |

---

## 4. Dev Environment Setup

For local development, no real AWS account is needed. See [backend/README.md](../../backend/README.md) for the full local setup. Key points:

- Run `moto_server` locally to simulate DynamoDB on `http://localhost:8001`.
- Set `APP_ENV=dev` and `DYNAMODB_ENDPOINT_URL=http://localhost:8001` in `backend/.env`.
- Set `ADMIN_EMAILS=admin@test.com` (or any email you choose for local testing) in `backend/.env`.
- Set `VITE_AUTH_MODE=mock` in `frontend/.env.local` — this enables the dev login form.
- Use `POST /dev/mock-token` with any email to simulate logging in as that user.

**The dev mock flow is structurally identical to production.** The only difference is that Cognito authentication is replaced by the mock token endpoint. `GET /me` runs real role-lookup logic against real (moto-mocked) DynamoDB in both modes.

---

## 5. Operating Multiple Environments

If you run both `dev` and `prod` environments under the same AWS account:

- Use separate DynamoDB tables: `bookrover-sellers-dev` vs `bookrover-sellers-prod` (controlled by `APP_ENV`).
- Use separate Lambda functions: `bookrover-api-dev` and `bookrover-api-prod`.
- Use separate S3 buckets and CloudFront distributions.
- **Never share `ADMIN_EMAILS` between environments** — use different values per environment to avoid accidental admin access in prod from a dev account.
- **No production data in dev — ever.**

---

## 6. Security Checklist Before Going Live

- [ ] `ADMIN_EMAILS` set to real operator email(s) only.
- [ ] `CORS_ALLOWED_ORIGINS` restricted to your CloudFront domain — not `["*"]`.
- [ ] `APP_ENV=prod` (enables `INFO` log level, disables dev-only endpoints).
- [ ] `DYNAMODB_ENDPOINT_URL` is blank (uses real AWS DynamoDB, not moto).
- [ ] `VITE_AUTH_MODE=cognito` (disables the mock login form).
- [ ] HTTPS enforced at CloudFront — HTTP redirected to HTTPS.
- [ ] IAM role for Lambda has least-privilege DynamoDB access on BookRover tables only.
- [ ] No `.env` files committed to the repository.
