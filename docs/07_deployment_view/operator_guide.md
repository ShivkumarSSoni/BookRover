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

### Step 2 — Provision DynamoDB Tables

DynamoDB tables **must exist before the Lambda function is deployed**. In production the app never creates them automatically — that only happens in local dev against moto server.

Table names follow the pattern `{TABLE_PREFIX}-{entity}-{APP_ENV}`. With the default env vars (`TABLE_PREFIX=bookrover`, `APP_ENV=prod`) the names are as shown below.

**Settings that apply to every table:**

| Setting | Value |
|---------|-------|
| Region | `ap-south-1` (or whatever you set `DYNAMODB_REGION` to) |
| Billing mode | On-demand (Pay per request) |
| Sort key | None |

**Tables and keys:**

| Table name | Partition key | Global Secondary Indexes |
|---|---|---|
| `bookrover-bookstores-prod` | `bookstore_id` (String) | — |
| `bookrover-group-leaders-prod` | `group_leader_id` (String) | — |
| `bookrover-sellers-prod` | `seller_id` (String) | `group-leader-id-index` |
| `bookrover-inventory-prod` | `book_id` (String) | `seller-id-index` |
| `bookrover-sales-prod` | `sale_id` (String) | `seller-id-index`, `bookstore-id-index` |
| `bookrover-returns-prod` | `return_id` (String) | `seller-id-index` |

**GSI details — for every GSI listed above:**

| GSI name | Appears on table | GSI partition key | Projection |
|---|---|---|---|
| `group-leader-id-index` | sellers | `group_leader_id` (String) | All attributes |
| `seller-id-index` | inventory, sales, returns | `seller_id` (String) | All attributes |
| `bookstore-id-index` | sales | `bookstore_id` (String) | All attributes |

> **Note:** There is no `admins` table. Admin access is controlled entirely by the `ADMIN_EMAILS` environment variable — no database record is needed or created.

#### Creating tables in the AWS Console

1. Open the [DynamoDB console](https://console.aws.amazon.com/dynamodb) and confirm the region is `ap-south-1` (top-right corner).
2. Click **Create table**.
3. Enter the **Table name** and **Partition key** (name + type **String**) from the table above. Leave **Sort key** blank.
4. Under **Table settings** choose **Customize settings**, then set **Capacity mode** to **On-demand**.
5. For tables that have GSIs, scroll to **Global secondary indexes** and click **Add global secondary index** for each:
   - **Index name** — enter exactly as shown (e.g. `seller-id-index`).
   - **Partition key** — enter the attribute name and select **String**.
   - **Projection attributes** — select **All**.
6. Leave all other settings at their defaults and click **Create table**.
7. Repeat for all six tables.
8. Wait until every table shows **Active** status before proceeding.

---

### Step 3 — IAM Role, Lambda, and API Gateway

#### 3a — Create the IAM execution role

The Lambda function needs permission to write logs to CloudWatch and to read/write the six DynamoDB tables. Create a dedicated role for this.

1. Open the [IAM console](https://console.aws.amazon.com/iam) → **Roles** → **Create role**.
2. **Trusted entity type:** AWS service. **Use case:** Lambda. Click **Next**.
3. On the **Add permissions** screen, search for and attach **`AWSLambdaBasicExecutionRole`** (grants CloudWatch Logs write access). Click **Next**.
4. **Role name:** `bookrover-lambda-execution-role`. Click **Create role**.
5. Open the newly created role → **Add permissions** → **Create inline policy**.
6. Switch to the **JSON** editor and paste the policy below, replacing `YOUR_ACCOUNT_ID` with your 12-digit AWS account number:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:UpdateItem",
        "dynamodb:DeleteItem",
        "dynamodb:Query",
        "dynamodb:Scan"
      ],
      "Resource": [
        "arn:aws:dynamodb:ap-south-1:YOUR_ACCOUNT_ID:table/bookrover-bookstores-prod",
        "arn:aws:dynamodb:ap-south-1:YOUR_ACCOUNT_ID:table/bookrover-bookstores-prod/index/*",
        "arn:aws:dynamodb:ap-south-1:YOUR_ACCOUNT_ID:table/bookrover-group-leaders-prod",
        "arn:aws:dynamodb:ap-south-1:YOUR_ACCOUNT_ID:table/bookrover-group-leaders-prod/index/*",
        "arn:aws:dynamodb:ap-south-1:YOUR_ACCOUNT_ID:table/bookrover-sellers-prod",
        "arn:aws:dynamodb:ap-south-1:YOUR_ACCOUNT_ID:table/bookrover-sellers-prod/index/*",
        "arn:aws:dynamodb:ap-south-1:YOUR_ACCOUNT_ID:table/bookrover-inventory-prod",
        "arn:aws:dynamodb:ap-south-1:YOUR_ACCOUNT_ID:table/bookrover-inventory-prod/index/*",
        "arn:aws:dynamodb:ap-south-1:YOUR_ACCOUNT_ID:table/bookrover-sales-prod",
        "arn:aws:dynamodb:ap-south-1:YOUR_ACCOUNT_ID:table/bookrover-sales-prod/index/*",
        "arn:aws:dynamodb:ap-south-1:YOUR_ACCOUNT_ID:table/bookrover-returns-prod",
        "arn:aws:dynamodb:ap-south-1:YOUR_ACCOUNT_ID:table/bookrover-returns-prod/index/*"
      ]
    }
  ]
}
```

7. Click **Next**, name the policy `bookrover-dynamodb-prod`, and click **Create policy**.

> **Why `index/*`?** The app queries GSIs (e.g. `seller-id-index`). DynamoDB GSI access requires a separate ARN entry for `table/*/index/*`.

---

#### 3b — Package the backend

Lambda runs your code from a zip file containing the app and all its dependencies. Lambda runs on **Linux x86_64** — the wheels must match that platform regardless of your local OS.

Run these commands from the `backend/` directory:

**Linux / macOS:**

```bash
cd backend

# 1. Install Linux-compatible wheels (--platform ensures correct binaries even on Mac ARM)
pip install -r requirements.txt --target ./package \
  --platform manylinux2014_x86_64 --python-version 3.12 --only-binary=:all: --upgrade

# 2. Copy the bookrover package
cp -r bookrover ./package/

# 3. Zip everything up
cd package && zip -r ../bookrover-lambda.zip . && cd ..
```

**Windows (PowerShell):**

```powershell
cd backend

# 1. Install Linux-compatible wheels
pip install -r requirements.txt --target .\package `
  --platform manylinux2014_x86_64 --python-version 3.12 --only-binary=:all: --upgrade

# 2. Copy the bookrover package
Copy-Item -Recurse bookrover .\package\

# 3. Zip using Python — avoids Windows MAX_PATH errors that break Compress-Archive on deep botocore paths
python -c "import zipfile, pathlib; p=pathlib.Path('package'); z=pathlib.Path('bookrover-lambda.zip'); z.unlink(missing_ok=True); zf=zipfile.ZipFile(z,'w',zipfile.ZIP_DEFLATED); [zf.write(f,f.relative_to(p)) for f in p.rglob('*') if f.is_file()]; zf.close(); print(f'Done: {round(z.stat().st_size/1024/1024,1)} MB')"
```

This produces `backend/bookrover-lambda.zip`. The Lambda handler entry point is `bookrover.main.handler` — the `Mangum` instance that wraps the FastAPI app.

---

#### 3c — Create the Lambda function

1. Open the [Lambda console](https://console.aws.amazon.com/lambda) — confirm region is `ap-south-1`.
2. Click **Create function** → **Author from scratch**.
3. Fill in:

   | Field | Value |
   |-------|-------|
   | Function name | `bookrover-api-prod` |
   | Runtime | Python 3.12 |
   | Architecture | x86_64 |
   | Execution role | **Use an existing role** → `bookrover-lambda-execution-role` |

4. Click **Create function**.
5. On the function page, scroll to **Code source** → **Upload from** → **.zip file**. Upload `bookrover-lambda.zip`.
6. Under **Runtime settings** → **Edit**, set **Handler** to: `bookrover.main.handler`. Save.
7. Go to **Configuration** → **General configuration** → **Edit**:
   - **Memory:** 256 MB
   - **Timeout:** 30 seconds
   - Save.
8. Go to **Configuration** → **Environment variables** → **Edit** → **Add environment variable** for each:

   | Key | Value |
   |-----|-------|
   | `APP_ENV` | `prod` |
   | `ADMIN_EMAILS` | `["youremail@example.com"]` |
   | `TABLE_PREFIX` | `bookrover` |
   | `DYNAMODB_REGION` | `ap-south-1` |
   | `CORS_ALLOWED_ORIGINS` | `["*"]` |
   | `COGNITO_USER_POOL_ID` | `ap-south-1_XXXXXXXX` |
   | `COGNITO_REGION` | `ap-south-1` |

   > `ADMIN_EMAILS` and `CORS_ALLOWED_ORIGINS` are **list fields** — they must be set as JSON arrays (with square brackets), not plain strings. Multiple admins: `["admin1@example.com","admin2@example.com"]`.
   >
   > Leave `DYNAMODB_ENDPOINT_URL` **unset** — its absence tells the app to use real AWS DynamoDB. Update `CORS_ALLOWED_ORIGINS` to your CloudFront URL once you have it.
   >
   > Set `COGNITO_USER_POOL_ID` and `COGNITO_REGION` **after** completing Step 4 below. You can add them now as placeholders and update once the User Pool is created.

9. Save.

---

#### 3d — Test the Lambda function directly

Before wiring up API Gateway, do a quick smoke test.

1. On the function page click **Test** → **Create new test event**.
2. Use the template **apigateway-http-api-proxy** or **API Gateway Http API** from the dropdown. Name it `SmokeTest`.
3. Change the `rawPath` value to `/docs` and click **Save**, then **Test**.
4. Check the **Response** — you should see `"statusCode": 200`. A `404` means the route doesn't exist but the app IS running; a `500` or `ImportModuleError` means something is wrong.

> `/health` is not a registered route in BookRover — use `/docs` (FastAPI Swagger UI) for smoke testing.

---

#### 3e — Create the API Gateway

1. Open the [API Gateway console](https://console.aws.amazon.com/apigateway) → **Create API**.
2. Choose **HTTP API** → **Build**.
3. **Skip** the "Add integration" screen for now — click **Next**.
4. **API name:** `bookrover-http-api`. Click **Next**.
5. On the **Configure routes** screen, define one route:
   - **Method:** `ANY`
   - **Resource path:** `/{proxy+}`

   Click **Next**.
6. **Stage name:** `$default` (already filled in). Make sure **Auto-deploy** is enabled. Click **Next** → **Create**.
7. After the API is created, go to **Routes** in the left sidebar → click **ANY /{proxy+}**.
8. Under **Integration**, click **Attach integration** → **Create and attach an integration**:
   - **Integration type:** Lambda function
   - **AWS Region:** `ap-south-1`
   - **Lambda function:** `bookrover-api-prod`
   - Click **Create**.
9. Verify Lambda invoke permissions: go to the Lambda console → `bookrover-api-prod` → **Configuration** → **Permissions** → **Resource-based policy statements**. You should see an entry with principal `apigateway.amazonaws.com`. The console adds this automatically when you attach the integration — if it is missing, copy and run the AWS CLI snippet shown on the API Gateway integration page.
10. Back in API Gateway, click **Deploy**.
11. Copy the **Invoke URL** from the left sidebar → **API** (the top-level summary page) — it looks like:
    `https://abc123def.execute-api.ap-south-1.amazonaws.com`
    This is your `VITE_API_BASE_URL`.
12. Verify end-to-end: open `https://YOUR_INVOKE_URL/docs` in a browser. You should see the FastAPI Swagger UI.

---

### Step 4 — Provision Cognito User Pool (Authentication)

BookRover uses AWS Cognito Email OTP for production authentication. Users enter their email address; Cognito sends a one-time 6-digit code; the frontend verifies the code and receives a JWT that is attached to every API request. No passwords — no password reset flows, no storage of credentials.

#### 4a — Create the User Pool

1. Open the [Cognito console](https://console.aws.amazon.com/cognito) — confirm the region is `ap-south-1`.
2. Click **Create user pool**.
3. Under **Authentication providers**, select **Email** as the sign-in option. Click **Next**.
4. On the **Security requirements** screen:
   - **Multi-factor authentication:** select **No MFA** (the OTP code IS the authentication factor).
   - Leave all other options at their defaults. Click **Next**.
5. On the **Sign-up experience** screen, leave all defaults and click **Next**.
6. On the **Message delivery** screen, select **Send email with Cognito** (uses Cognito's shared SES — free, no domain verification needed for low volumes). Click **Next**.
7. On the **Integrate your app** screen:
   - **User pool name:** `bookrover-prod`
   - **App type:** Leave **Traditional web application** selected (you will change auth flows in the next step).
   - **App client name:** `bookrover-frontend`
   - **Client secret:** select **Don't generate a client secret** — the frontend is a public SPA and cannot keep a secret.
   - Click **Next**.
8. Review the summary and click **Create user pool**.

#### 4b — Enable the EMAIL_OTP auth flow

Cognito's EMAIL_OTP (passwordless sign-in via one-time code) is configured on the App Client:

1. On the Cognito console, open the newly created `bookrover-prod` user pool.
2. Go to **App integration** → **App clients and analytics** → click `bookrover-frontend`.
3. Click **Edit** next to **Authentication flows**.
4. Enable both:
   - **ALLOW_USER_AUTH** — enables the new multi-step auth flow
   - **ALLOW_REFRESH_TOKEN_AUTH** — allows token refresh without re-authenticating
5. Click **Save changes**.

> **Why ALLOW_USER_AUTH?** The Amplify `signIn()` call with `authFlowType: 'USER_AUTH'` requires this flow. It is the Cognito prerequisite for Email OTP step-up challenges.

#### 4c — Note your User Pool ID and App Client ID

1. On the **User pool overview** page, copy the **User pool ID** — it looks like `ap-south-1_XXXXXXXX`.
2. Go to **App integration** → **App clients** → click `bookrover-frontend`. Copy the **Client ID**.

You will need both values in the next two places:

| Where | Key | Value |
|-------|-----|-------|
| Lambda env vars | `COGNITO_USER_POOL_ID` | `ap-south-1_XXXXXXXX` |
| Lambda env vars | `COGNITO_REGION` | `ap-south-1` |
| Frontend `.env.production` | `VITE_COGNITO_USER_POOL_ID` | `ap-south-1_XXXXXXXX` |
| Frontend `.env.production` | `VITE_COGNITO_CLIENT_ID` | `<client-id>` |

Update the Lambda environment variables now (Lambda console → `bookrover-api-prod` → **Configuration** → **Environment variables** → **Edit**). The frontend values are set in the next step when you build and deploy.

---

### Step 5 — Deploy frontend to S3 + CloudFront

Create a `.env.production` file in the `frontend/` directory (never commit it — it is already in `.gitignore`):

```env
VITE_API_BASE_URL=https://YOUR_INVOKE_URL
VITE_AUTH_MODE=cognito
VITE_COGNITO_USER_POOL_ID=ap-south-1_XXXXXXXX
VITE_COGNITO_CLIENT_ID=your-app-client-id
```

Build and deploy:

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

### Step 6 — First login as Admin

1. Navigate to your CloudFront URL (e.g. `https://d1234abcd.cloudfront.net`).
2. Enter the email address you put in `ADMIN_EMAILS` and click **Send sign-in code**.
3. Cognito sends a 6-digit OTP to your inbox — enter it in the verification screen.
4. The frontend exchanges the Cognito session for a JWT and calls `GET /me`. The backend verifies the JWT, finds your email in `ADMIN_EMAILS`, and returns `role: admin`.
5. You will be routed to `/admin` automatically.
6. From `/admin`, create bookstores and group leaders.

After this first login, the app is operational. Group leaders receive their invitation by having a group leader record created for them by the admin — they authenticate with their email OTP and are matched to that record automatically.

---

## 3. Environment Variables Reference

### Backend (Lambda environment variables)

| Variable | Required | Example | Description |
|----------|----------|---------|-------------|
| `APP_ENV` | Yes | `prod` | `dev` or `prod`. Controls log level and table name suffix. |
| `ADMIN_EMAILS` | Yes | `["you@example.com"]` | JSON array of email addresses with admin access. Multiple: `["a@x.com","b@x.com"]`. |
| `TABLE_PREFIX` | Yes | `bookrover` | DynamoDB table name prefix. Tables are named `{prefix}-{entity}-{env}`. |
| `DYNAMODB_REGION` | Yes | `ap-south-1` | AWS region where DynamoDB tables are provisioned. |
| `DYNAMODB_ENDPOINT_URL` | Dev only | `http://localhost:8001` | Local moto server endpoint. Leave blank in production. |
| `CORS_ALLOWED_ORIGINS` | Yes | `["https://d1234.cloudfront.net"]` | Frontend origin(s) allowed to call the API. Use `["*"]` only in dev. |
| `COGNITO_USER_POOL_ID` | Prod only | `ap-south-1_XXXXXXXX` | Cognito User Pool ID. Used by the backend to verify Cognito JWTs. |
| `COGNITO_REGION` | Prod only | `ap-south-1` | AWS region of the Cognito User Pool. Used to construct the JWKS endpoint URL. |

### Frontend (Vite build-time variables)

| Variable | Required | Example | Description |
|----------|----------|---------|-------------|
| `VITE_API_BASE_URL` | Yes | `https://api.yourdomain.com` | API Gateway base URL. |
| `VITE_AUTH_MODE` | Yes | `cognito` | `mock` (dev) or `cognito` (prod). Controls the authentication flow. |
| `VITE_COGNITO_USER_POOL_ID` | Prod only | `ap-south-1_XXXXXXX` | Cognito User Pool ID. |
| `VITE_COGNITO_CLIENT_ID` | Prod only | `1abc2defg3hij` | Cognito App Client ID. |

---

## 4. Operating Multiple Environments

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
- [ ] `COGNITO_USER_POOL_ID` and `COGNITO_REGION` set on the Lambda function.
- [ ] `VITE_COGNITO_USER_POOL_ID` and `VITE_COGNITO_CLIENT_ID` baked into the frontend build.
- [ ] Cognito App Client has **no client secret** and `ALLOW_USER_AUTH` + `ALLOW_REFRESH_TOKEN_AUTH` flows enabled.
- [ ] HTTPS enforced at CloudFront — HTTP redirected to HTTPS.
- [ ] IAM role for Lambda has least-privilege DynamoDB access on BookRover tables only.
- [ ] No `.env` files committed to the repository.
