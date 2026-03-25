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

#### Configure stage-level throttling

HTTP API throttling is set on the `$default` stage and applies to every route. It is a **built-in feature with no extra cost** on top of normal API Gateway pricing.

> **Why not Usage Plans?** Usage Plans and API Keys are a **REST API** feature. BookRover uses an HTTP API, which does not support them. Stage-level throttling is the equivalent mechanism for HTTP API.

1. In the API Gateway console, open `bookrover-http-api` → **Protect** in the left sidebar → **Throttling**.
2. Under **Default route throttling**, click **Edit**.
3. Set:
   | Setting | Recommended value | Meaning |
   |---------|-------------------|---------|
   | **Rate limit** | `50` | Maximum sustained requests per second across all callers |
   | **Burst limit** | `100` | Maximum concurrent in-flight requests at any instant |
4. Click **Save**.

API Gateway will now return `HTTP 429 Too Many Requests` automatically when either limit is exceeded — no application code change needed.

> **Sizing guidance:** 50 req/s is generous for a small multi-seller app. Raise it only if CloudWatch metrics show sustained 429s from legitimate traffic. Do not set burst below rate.

---

#### 3f — AWS WAF (Optional — recommended before production)

AWS WAF is an independent web application firewall that sits in front of API Gateway. It provides protection beyond simple rate limiting: managed rulesets block known exploit patterns (SQL injection, XSS, bad bots) even before a request reaches Lambda.

**Why it is optional here:**
- Stage-level throttling (step 3e above) already covers gaps 2 & 9 for a small-scale deployment.
- WAF adds ~$5–10/month minimum even at zero traffic (Web ACL fee + per-rule fees).
- For a portfolio or demo deployment the cost is rarely justified; for a real production app with public traffic it is strongly recommended.

**When to add WAF:**
- Before going live with real seller/buyer data.
- When `/lookup/group-leaders` or `/lookup/bookstores` are called from untrusted clients at scale.
- When a penetration test or compliance requirement mandates it.

**Setup steps (when ready):**

1. Open the [AWS WAF console](https://console.aws.amazon.com/wafv2) — confirm the region is `ap-south-1`.
2. Click **Create web ACL**.
3. Fill in:
   - **Resource type:** Regional resources
   - **Region:** Asia Pacific (Mumbai) — `ap-south-1`
   - **Name:** `bookrover-waf-prod`
4. Under **Associated AWS resources**, click **Add AWS resources** → select your `bookrover-http-api` API Gateway stage (`$default`). Click **Add**.
5. Click **Next** → **Add rules** → **Add managed rule groups**. Enable:
   - **AWS managed rules — Core rule set** (`AWSManagedRulesCommonRuleSet`) — blocks OWASP Top 10 patterns.
   - **AWS managed rules — Known bad inputs** (`AWSManagedRulesKnownBadInputsRuleSet`) — blocks exploit probes.
6. Click **Add rules** → **Add my own rules** → **Rate-based rule**:
   - **Rule name:** `global-rate-limit`
   - **Rate limit:** `300` (requests per 5 minutes per IP — adjust to your traffic profile)
   - **Scope of inspection:** All requests (default)
   - **Action:** Block
7. Set **Default action** to **Allow**.
8. Click through **Next** → **Next** → **Create web ACL**.

**Approximate monthly cost at low traffic:**

| Item | Cost |
|------|------|
| Web ACL | $5.00/month |
| Rules (2 managed + 1 rate-based) | ~$3.00/month |
| Requests (first 10M) | $0.60 per million |
| **Minimum** | **~$8/month** |

> WAF costs are in addition to API Gateway request charges. The WAF Web ACL is associated directly with the API Gateway stage — no CloudFront distribution is required unless you want global edge protection.

---

### Step 4 — Provision Cognito User Pool (Authentication)

BookRover uses AWS Cognito Email OTP for production authentication. Users enter their email address; Cognito sends a one-time sign-in code (6 or 8 digits depending on your pool's configuration); the frontend verifies the code and receives a JWT that is attached to every API request. No passwords — no password reset flows, no storage of credentials.

> **Self-registration is built in.** The app automatically creates a Cognito account the first time any user logs in — no admin pre-provisioning required. On first login `signUp()` is called silently; on subsequent logins Cognito detects the existing account and issues the OTP directly.

#### 4a — Create the User Pool

1. Open the [Cognito console](https://console.aws.amazon.com/cognito) — confirm the region is `ap-south-1`.
2. If this is your first User Pool, you will see a landing page with two options. Click **Get started for free** under **"Add sign-in and sign-up experiences to your app"**. If you have existing User Pools, click **Create user pool** instead.
3. You will land on a **"Set up resources for your application"** wizard. Fill it in as follows:
   - **Application type:** Select **Single-page application (SPA)** — BookRover is a React app.
   - **Name your application:** `bookrover-frontend`
   - **Options for sign-in identifiers:** tick **Email** only (untick Phone number and Username if selected).
   - **Self-registration:** tick **Enable self-registration** — this allows Cognito to create a user profile automatically on first Email OTP sign-in.
   - **Required attributes for sign-up:** leave at defaults.
   > AWS displays a banner: *"Options for sign-in identifiers and required attributes can't be changed after the app has been created."* This is informational — not an error. Confirm your selections are correct (Email sign-in, default required attributes) and proceed.
4. The final wizard screen shows an optional **Return URL** field. Leave it **blank** — BookRover uses Amplify's API-based EMAIL_OTP flow, not Cognito's hosted UI redirect, so no callback URL is needed.
5. Click **Create User Directory**.
6. After creation, AWS shows a **"Set up resources for your application"** quick-start page with React/OIDC code snippets. **Ignore it entirely** — BookRover uses AWS Amplify with EMAIL_OTP, not the OIDC redirect flow shown there.
7. The pool will be auto-named (e.g. `"User pool - abcd1x"`). The name you entered (`bookrover-frontend`) is the **App Client** name — it is separate. To rename the User Pool: on the User pool overview page, click **Rename** next to the pool name and enter `bookrover-prod`.

#### 4b — Enable EMAIL_OTP at the User Pool level

BookRover uses Cognito's passwordless EMAIL_OTP sign-in. This must be enabled at two levels: the User Pool itself (here) and the App Client (next step).

1. On the Cognito console, open the `bookrover-prod` user pool.
2. Click the **Sign-in experience** tab.
3. Scroll to **Passwordless authentication** (or **Email-based authentication**).
4. Click **Edit**.
5. Enable **Email OTP** (also shown as *"Allow users to sign in using an OTP sent via email"*).
6. Click **Save changes**.

> Without this step, Cognito only offers PASSWORD_SRP and PASSWORD challenges — the EMAIL_OTP challenge never appears in responses.

#### 4c — Enable the EMAIL_OTP auth flow on the App Client

EMAIL_OTP sign-in also requires specific auth flows enabled on the App Client:

1. On the Cognito console, open the `bookrover-prod` user pool.
2. Go to **App integration** → **App clients and analytics** → click `bookrover-frontend`.
3. Click **Edit** next to **Authentication flows**.
4. `ALLOW_USER_SRP_AUTH` will already be checked — leave it as-is. Additionally enable:
   - **ALLOW_USER_AUTH** — enables the multi-step auth flow required for EMAIL_OTP
   - **ALLOW_REFRESH_TOKEN_AUTH** — allows token refresh without re-authenticating
5. Leave the token expiration settings at their defaults:
   - **Auth flow session duration:** 3 minutes (time to enter the OTP — sufficient)
   - **Refresh token expiration:** 5 days (how long before full re-auth is needed)
   - **Access token expiration:** 60 minutes (standard short-lived token)
   - **ID token expiration:** 60 minutes (same as access token)
6. Under **Advanced security configurations**, leave both options enabled (they are on by default):
   - **Enable token revocation** — allows sign-out to invalidate tokens immediately (important if a device is lost)
   - **Prevent user existence errors** — returns a generic auth failure instead of revealing whether an email is registered (prevents account enumeration)
7. Click **Save changes**.

> **Why ALLOW_USER_AUTH?** The Amplify `signUp()` / `signIn()` calls with `authFlowType: 'USER_AUTH'` require this flow. It is the Cognito prerequisite for Email OTP challenges.

#### 4d — Note your User Pool ID and App Client ID

1. On the **User pool overview** page, copy the **User pool ID** — it looks like `ap-south-1_XXXXXXXX`.
2. Go to **App integration** → **App clients** → click `bookrover-frontend`. Copy the **Client ID**.

You will need both values in the next two places:

| Where | Key | Value |
|-------|-----|-------|
| Lambda env vars | `COGNITO_USER_POOL_ID` | `ap-south-1_XXXXXXXX` |
| Lambda env vars | `COGNITO_REGION` | `ap-south-1` |
| Frontend `.env.prod` | `VITE_COGNITO_USER_POOL_ID` | `ap-south-1_XXXXXXXX` |
| Frontend `.env.prod` | `VITE_COGNITO_CLIENT_ID` | `<client-id>` |

Update the Lambda environment variables now (Lambda console → `bookrover-api-prod` → **Configuration** → **Environment variables** → **Edit**). The frontend values are set in the next step when you build and deploy.

---

### Step 5 — Deploy frontend to S3 + CloudFront

#### 5a — Install and configure the AWS CLI

The deployment commands require the AWS CLI. Install it once on your machine:

**Windows:**
1. Download the installer from `https://aws.amazon.com/cli/` and run it.
2. Verify: open a new PowerShell window and run `aws --version`.
3. Configure credentials:
   ```powershell
   aws configure
   ```
   Enter when prompted:
   | Prompt | Value |
   |--------|-------|
   | AWS Access Key ID | Your IAM user access key |
   | AWS Secret Access Key | Your IAM user secret key |
   | Default region name | `ap-south-1` |
   | Default output format | `json` |

**Linux / macOS:**
```bash
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip && sudo ./aws/install
aws configure   # same prompts as above
```

> The IAM user used here needs `s3:PutObject`, `s3:DeleteObject`, `s3:ListBucket`, and `cloudfront:CreateInvalidation` permissions. The simplest approach for a personal deployment is to use your existing admin IAM user credentials, or create a dedicated deploy user and attach `AdministratorAccess` (or a scoped S3+CloudFront policy) to it.

---

#### 5b — Create the S3 bucket

1. Open the [S3 console](https://console.aws.amazon.com/s3) — region does **not** matter for S3 (it is global), but choose `ap-south-1` for consistency.
2. Click **Create bucket**.
3. Fill in:
   - **Bucket name:** `bookrover-frontend-prod` (must be globally unique — add a suffix if taken, e.g. `bookrover-frontend-prod-2026`)
   - **AWS Region:** `ap-south-1`
4. Under **Block Public Access settings**: **uncheck** "Block all public access". Acknowledge the warning. CloudFront will serve the files publicly via its own identity — you need the bucket to allow it.
5. Leave all other settings at defaults and click **Create bucket**.
6. Open the newly created bucket → **Properties** tab → scroll to **Static website hosting** → **Edit**:
   - Enable static website hosting
   - **Index document:** `index.html`
   - **Error document:** `index.html` (React router handles 404s client-side)
   - Click **Save changes**.
7. Go to the **Permissions** tab → **Bucket policy** → **Edit**, paste the policy below (replace `bookrover-frontend-prod` with your actual bucket name):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::bookrover-frontend-prod/*"
    }
  ]
}
```

Click **Save changes**.

---

#### 5c — Create the CloudFront distribution

1. Open the [CloudFront console](https://console.aws.amazon.com/cloudfront) → **Create distribution**.
2. You will see a **"Get started"** screen before the origin settings. Fill it in as follows:
   - **Distribution name:** `bookrover-frontend-prod`
   - **Description:** leave blank (optional)
   - **Distribution type:** select **Single website or app**
   - **Domain (Route 53):** leave blank — skip this optional field unless you have a custom domain in Route 53
   - Click **Next** (or scroll down to continue to the Origin section).
3. Under **Origin**:
   - **Origin domain:** The CloudFront dropdown only lists S3 REST endpoints (`.s3.amazonaws.com`) — do **not** select from the dropdown. Instead, **type the website endpoint manually**:
     1. Open a new browser tab → S3 console → your bucket → **Properties** tab → scroll to **Static website hosting** → copy the **Bucket website endpoint** URL.
     2. It looks like: `bookrover-frontend-prod.s3-website.ap-south-1.amazonaws.com`
     3. Paste **only the hostname** (no `http://`) into the CloudFront **Origin domain** field.
   - Leave **Origin path** blank.
4. Under **Settings** (directly below Origin):
   - **Origin settings:** select **Use recommended origin settings**
   - **Cache settings:** select **Use recommended cache settings tailored to serving S3 content**
   - Click **Next**.
5. On the **Enable security** screen (AWS WAF):
   - Select **Do not enable security protections** — WAF adds ~$14/month minimum; skip for now. (See step 3f if you want to add WAF later.)
   - Click **Next**.
6. You will see a **"Review and create"** summary page — verify the origin shows your S3 website endpoint and Security shows "None". Click **Create distribution**.
7. Wait for the distribution **Status** to change from `Deploying` to `Enabled` (takes a few minutes).
8. **Set the default root object** (required — the wizard skips this):
   - Open the distribution → **Settings** tab → **Edit**.
   - **Default root object:** `index.html`
   - Click **Save changes**.
9. Copy the **Distribution domain name** from the distribution overview — it looks like `d1234abcd.cloudfront.net`. This is your app's public URL.

> **After you have the CloudFront URL**, go back and update the Lambda env var:
> - Lambda console → `bookrover-api-prod` → **Configuration** → **Environment variables** → **Edit**
> - Set `CORS_ALLOWED_ORIGINS` → `["https://d1234abcd.cloudfront.net"]` (replace with your actual domain)
> - Save.

---

#### 5d — Create the `.env.prod` file and build

Create `frontend/.env.prod` (never commit it — it is already in `.gitignore`):

```env
VITE_API_BASE_URL=https://YOUR_INVOKE_URL
VITE_AUTH_MODE=cognito
VITE_COGNITO_USER_POOL_ID=ap-south-1_XXXXXXXX
VITE_COGNITO_CLIENT_ID=your-app-client-id
```

Build and deploy:

```powershell
cd frontend
npm install
npm run build -- --mode prod
aws s3 sync dist/ s3://bookrover-frontend-prod --delete
```

> `--mode prod` tells Vite to load `.env.prod` instead of the default `.env.production`.

Invalidate the CloudFront cache after each deploy so users get the latest build immediately:

```powershell
aws cloudfront create-invalidation --distribution-id YOUR_DIST_ID --paths "/*"
```

Replace `YOUR_DIST_ID` with the Distribution ID shown in the CloudFront console (format: `E1ABCDEF2GHIJK`).

### Step 6 — First login as Admin

1. Navigate to your CloudFront URL (e.g. `https://d1234abcd.cloudfront.net`).
2. Enter the email address you put in `ADMIN_EMAILS` and click **Send sign-in code**.
3. The app silently calls Cognito `signUp` behind the scenes — Cognito creates the admin account and sends a sign-in code to your inbox.
4. Enter the code in the verification screen. The code may be 6 or 8 digits depending on your Cognito pool configuration — enter all digits shown in the email.
5. The frontend exchanges the Cognito session for a JWT and calls `GET /me`. The backend verifies the JWT, finds your email in `ADMIN_EMAILS`, and returns `role: admin`.
6. You will be routed to `/admin` automatically.
7. From `/admin`, create bookstores and group leaders.

> **OTP email not arriving?** Check your **Spam / Junk** folder — Cognito's default sender is `no-reply@verificationemail.com`. For reliable inbox delivery in production, configure Amazon SES: Cognito console → `bookrover-prod` → **Messaging** → **Email** → switch from "Cognito default" to "Send email with Amazon SES". SES requires verifying your sending domain or address and may require exiting the SES sandbox for non-verified recipients.

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
