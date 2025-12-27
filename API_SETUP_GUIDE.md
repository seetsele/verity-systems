# Verity Systems - API Setup Guide
Complete step-by-step instructions to configure all required APIs

---

## TABLE OF CONTENTS
1. [Anthropic Claude API](#1-anthropic-claude-api)
2. [Stripe Payment Platform](#2-stripe)
3. [Supabase Database](#3-supabase)
4. [Google Fact Check API](#4-google-fact-check-api)
5. [Optional: Groq API](#5-optional-groq-api)
6. [Environment File Setup](#environment-file-setup)
7. [Testing & Verification](#testing--verification)

---

## 1. ANTHROPIC CLAUDE API

### What You Get
- Claude 3.5 Sonnet model access for fact-checking
- Free $25/month via GitHub Education Pack (or paid tier)
- Used for: Core fact-checking, content analysis, claim verification

### GitHub Student Option (FREE $25/month)
**IF YOU ARE A STUDENT:**

1. Go to: https://education.github.com/pack
2. Verify your student status with GitHub
3. Once verified, you'll get Anthropic credits in your Education Pack
4. Then follow the "Self-Pay" steps below

### Self-Pay Option (Pay-As-You-Go)

#### Step 1: Create Anthropic Account
1. Go to: https://console.anthropic.com
2. Click "Sign Up"
3. Enter email and create password
4. Verify email address

#### Step 2: Set Up Billing
1. Go to: https://console.anthropic.com/account/billing/overview
2. Click "Add Payment Method"
3. Enter credit card details
4. Set billing address

#### Step 3: Generate API Key
1. Go to: https://console.anthropic.com/account/keys
2. Click "Create Key"
3. Name it: `verity-systems-prod`
4. Click "Create"
5. **Copy the key immediately** (shown only once)

#### Step 4: Add to .env File
```bash
ANTHROPIC_API_KEY=sk-ant-v0-xxxxxxxxxxxxx
```

#### Estimated Cost
- **First 1000 requests:** ~$0.50
- **Monthly (10K requests):** ~$5
- **Scale varies by model:** 
  - Claude 3.5 Sonnet: $3-15/1M tokens
  - Claude 3 Haiku: $0.25/1M tokens (cheaper option)

#### Test It
```bash
python python-tools/fact_checker.py
```

---

## 2. STRIPE

### What You Get
- Payment processing for subscriptions
- Checkout UI
- Invoice management
- Webhook support
- Free test mode (no real payments)

### Step 1: Create Stripe Account
1. Go to: https://dashboard.stripe.com/register
2. Enter email
3. Set password
4. Verify email
5. Complete business information

### Step 2: Set Up Account Type
1. After signup, you'll see "Choose your business type"
2. Select: "Software/SaaS" or "Business Services"
3. Fill in business name: `Verity Systems`
4. Fill in website: `yourdomain.com` (or localhost for testing)

### Step 3: Get API Keys (TEST MODE)
1. Go to: https://dashboard.stripe.com/apikeys
2. Make sure "View test data" is enabled (toggle top-left)
3. You'll see two test keys:
   - **Publishable Key (pk_test_...)** - Use on frontend
   - **Secret Key (sk_test_...)** - Use on backend
4. Copy the **Secret Key**

### Step 4: Add to .env File
```bash
STRIPE_SECRET_KEY=sk_test_xxxxxxxxxxxxx
STRIPE_PUBLISHABLE_KEY=pk_test_xxxxxxxxxxxxx
```

### Step 5: Set Up Products (Optional)
1. Go to: https://dashboard.stripe.com/products
2. Click "Add Product"
3. Create three tiers:
   - **Starter** - $9/month
   - **Professional** - $29/month
   - **Enterprise** - $99/month
4. After creating, note the Price IDs

### Step 6: Add Price IDs to .env
```bash
STRIPE_STARTER_PRICE_ID=price_xxxxx
STRIPE_PROFESSIONAL_PRICE_ID=price_xxxxx
STRIPE_ENTERPRISE_PRICE_ID=price_xxxxx
```

#### Estimated Cost
- **Free forever** for test mode
- **Live mode:** 2.9% + $0.30 per transaction
- **No monthly fees**

#### Test Payment Card Numbers
```
4242 4242 4242 4242 - Success
4000 0000 0000 0002 - Decline
5555 5555 5555 4444 - MasterCard
378282246310005 - Amex
```
Use any future expiry date and any 3-digit CVC.

---

## 3. SUPABASE

### What You Get
- PostgreSQL database (free 500MB)
- Authentication/user management
- Real-time API
- Storage for files
- Edge functions

### Step 1: Create Supabase Account
1. Go to: https://supabase.com
2. Click "Start your project"
3. Click "Continue with GitHub" or email signup
4. Create account/verify email

### Step 2: Create Project
1. Click "New Project"
2. Project name: `verity-systems`
3. Database password: Create strong password (save it!)
4. Region: Select closest to your users
5. Click "Create New Project"
6. **Wait 2-3 minutes** for initialization

### Step 3: Get Connection String
1. Go to: Project Settings → Database → Connection String
2. Copy the connection string (starts with `postgresql://`)
3. Password field shows as `[YOUR-PASSWORD]` - replace with your actual password

### Step 4: Get API Keys
1. Go to: Project Settings → API
2. Copy the following:
   - **Project URL** - `https://xxxxx.supabase.co`
   - **Service Role Secret** - `eyJ...` (starts with eyJ)

### Step 5: Add to .env File
```bash
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
DATABASE_URL=postgresql://postgres:[YOUR-PASSWORD]@db.xxxxx.supabase.co:5432/postgres
```

### Step 6: Create Tables (Optional but Recommended)
Go to SQL Editor and run:

```sql
-- Users table
CREATE TABLE users (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  email VARCHAR(255) UNIQUE,
  created_at TIMESTAMP DEFAULT NOW(),
  subscription_tier VARCHAR(50) DEFAULT 'free'
);

-- Fact checks table
CREATE TABLE fact_checks (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  claim TEXT,
  result JSONB,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Audit logs table
CREATE TABLE audit_logs (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  action VARCHAR(255),
  details JSONB,
  created_at TIMESTAMP DEFAULT NOW()
);
```

#### Estimated Cost
- **Free tier:** Up to 500MB database, 2GB bandwidth
- **Paid:** Starts at $25/month for more storage/users

---

## 4. GOOGLE FACT CHECK API

### What You Get
- Access to Google's Fact Check dataset
- Search fact checks across sources
- Free tier: 10,000 requests/day

### Step 1: Enable Google Cloud
1. Go to: https://cloud.google.com/
2. Click "Try free" (if new account)
3. Create Google Cloud account
4. Verify payment method (won't charge for free tier)

### Step 2: Create Project
1. Go to: https://console.cloud.google.com/projectcreate
2. Project name: `Verity Systems`
3. Click "Create"
4. **Wait for project creation**

### Step 3: Enable Fact Check API
1. Go to: https://console.cloud.google.com/apis/library
2. Search: `Fact Check API`
3. Click on result
4. Click "Enable"
5. **Wait for enabling**

### Step 4: Create API Key
1. Go to: https://console.cloud.google.com/apis/credentials
2. Click "Create Credentials" → "API Key"
3. Copy the API key
4. Click the edit icon
5. Under "Application restrictions":
   - Select "HTTP referrers (web sites)"
   - Add: `localhost/*` and your domain
6. Under "API restrictions":
   - Select "Restrict key"
   - Choose: `Fact Check API`
7. Click "Save"

### Step 5: Add to .env File
```bash
GOOGLE_FACT_CHECK_API_KEY=AIzaSyDxxxxxxxxxxxxx
```

#### Estimated Cost
- **Free:** 10,000 requests/day (usually enough)
- **Paid:** $2.50 per 1000 additional requests

---

## 5. OPTIONAL: GROQ API

### What You Get
- High-speed LLM inference
- Free tier: Very generous limits
- Models: Llama 3.1, Mixtral, others

### Step 1: Create Account
1. Go to: https://console.groq.com/keys
2. Click "Sign up"
3. Enter email
4. Create password
5. Verify email

### Step 2: Generate API Key
1. After login, go to: https://console.groq.com/keys
2. Click "Create API Key"
3. Name: `verity-systems`
4. Copy the key

### Step 3: Add to .env
```bash
GROQ_API_KEY=gsk_xxxxxxxxxxxxx
```

#### Cost
- **Free:** Unlimited requests (rate limited)
- **No credit card** required

---

## ENVIRONMENT FILE SETUP

### Create .env File

Navigate to your project root directory:

```bash
cd c:\Users\lawm\Desktop\verity-systems
```

Create a file named `.env` (note the dot at the beginning):

**Windows (PowerShell):**
```powershell
New-Item .env -Force
```

**Windows (Command Prompt):**
```cmd
type nul > .env
```

**Mac/Linux:**
```bash
touch .env
```

### Complete .env Template

Copy and fill in all values:

```env
# ================================================
# AI PROVIDERS
# ================================================
ANTHROPIC_API_KEY=sk-ant-v0-xxxxxxxxxxxxx
GROQ_API_KEY=gsk_xxxxxxxxxxxxx

# ================================================
# PAYMENT PROCESSING
# ================================================
STRIPE_SECRET_KEY=sk_test_xxxxxxxxxxxxx
STRIPE_PUBLISHABLE_KEY=pk_test_xxxxxxxxxxxxx
STRIPE_STARTER_PRICE_ID=price_xxxxx
STRIPE_PROFESSIONAL_PRICE_ID=price_xxxxx
STRIPE_ENTERPRISE_PRICE_ID=price_xxxxx
STRIPE_WEBHOOK_SECRET=whsec_xxxxxxxxxxxxx

# ================================================
# DATABASE
# ================================================
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_SERVICE_KEY=eyJ...
DATABASE_URL=postgresql://postgres:PASSWORD@db.xxxxx.supabase.co:5432/postgres

# ================================================
# FACT CHECKING SOURCES
# ================================================
GOOGLE_FACT_CHECK_API_KEY=AIzaSyDxxxxxxxxxxxxx
NEWSAPI_KEY=xxxxxxxxxxxxx

# ================================================
# SECURITY
# ================================================
JWT_SECRET=generate-random-secret-key-here-min-32-chars
ENCRYPTION_KEY=generate-random-key-here
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=3600

# ================================================
# APPLICATION
# ================================================
DEBUG=False
ENVIRONMENT=production
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com
MAX_CONTENT_LENGTH=10485760
```

### Generate Random Keys (for JWT_SECRET and ENCRYPTION_KEY)

**Python:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Run this twice to generate two random keys.

---

## TESTING & VERIFICATION

### Test 1: Verify .env is Loaded
```bash
cd c:\Users\lawm\Desktop\verity-systems
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('ANTHROPIC_API_KEY set:', bool(os.getenv('ANTHROPIC_API_KEY')))"
```

Expected output: `ANTHROPIC_API_KEY set: True`

### Test 2: Test Anthropic API
```bash
python python-tools/fact_checker.py
```

Expected: Returns fact-checking analysis

### Test 3: Test Stripe Connection
```bash
python -c "
import stripe
import os
from dotenv import load_dotenv

load_dotenv()
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

try:
    products = stripe.Product.list(limit=1)
    print('[OK] Stripe API is working!')
except Exception as e:
    print(f'[ERROR] {e}')
"
```

### Test 4: Test Database Connection
```bash
python -c "
import os
from dotenv import load_dotenv

load_dotenv()
try:
    from supabase import create_client
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_SERVICE_KEY')
    client = create_client(url, key)
    print('[OK] Supabase connection successful!')
except Exception as e:
    print(f'[ERROR] {e}')
"
```

### Test 5: Start the API Server
```bash
cd python-tools
uvicorn api_server:app --reload --host 0.0.0.0 --port 8000
```

Expected:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

Open browser to: http://localhost:8000/docs (interactive API documentation)

---

## QUICK REFERENCE CHECKLIST

### Before Starting Server
- [ ] Created `.env` file in project root
- [ ] Anthropic API key added (or skipped if using free tier)
- [ ] Stripe keys added (can use test mode)
- [ ] Supabase credentials added
- [ ] JWT_SECRET generated (32+ chars)
- [ ] All env vars verified with `echo %VARIABLE_NAME%` (Windows) or `echo $VARIABLE_NAME` (Mac/Linux)

### Environment Variables by Priority

**MUST HAVE (to run):**
1. ✓ ANTHROPIC_API_KEY
2. ✓ STRIPE_SECRET_KEY & STRIPE_PUBLISHABLE_KEY
3. ✓ SUPABASE_URL & SUPABASE_SERVICE_KEY

**SHOULD HAVE (recommended):**
4. ✓ DATABASE_URL
5. ✓ JWT_SECRET
6. ✓ ENCRYPTION_KEY

**NICE TO HAVE (optional):**
7. GROQ_API_KEY
8. GOOGLE_FACT_CHECK_API_KEY

---

## TROUBLESHOOTING

### Issue: "Module not found: anthropic"
**Solution:**
```bash
pip install anthropic
```

### Issue: "ANTHROPIC_API_KEY is None"
**Solution:**
1. Check `.env` file exists in project root (not in `python-tools/`)
2. Verify API key format: should start with `sk-ant-v0-`
3. Restart your IDE/terminal (some don't reload env vars)
4. Test with: `python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(os.getenv('ANTHROPIC_API_KEY'))"`

### Issue: "Stripe API Error: Invalid API Key"
**Solution:**
1. Make sure using **Secret Key** (starts with `sk_`), not Publishable Key
2. Verify you're in TEST mode for testing (not live)
3. Copy the full key without spaces

### Issue: "Supabase connection refused"
**Solution:**
1. Verify SUPABASE_URL format: `https://xxxxx.supabase.co` (no trailing slash)
2. Check SERVICE_KEY starts with `eyJ`
3. Make sure project is fully initialized (wait 5 min after creation)

### Issue: ".env file not being loaded"
**Solution:**
1. File must be named `.env` exactly (with dot)
2. Must be in project root: `c:\Users\lawm\Desktop\verity-systems\.env`
3. Use `load_dotenv()` at start of Python scripts
4. Some IDEs need restart to pick up new `.env`

---

## COST SUMMARY

| Service | Free Tier | Cost |
|---------|-----------|------|
| Anthropic | $25/mo (students) | $0.003/1K tokens |
| Stripe | Test mode | 2.9% + $0.30 per transaction |
| Supabase | 500MB database | $25/mo for more |
| Google Fact Check | 10,000 req/day | $2.50/1000 extra |
| Groq | Unlimited (rate limited) | Free |

**Estimated Monthly Cost (startup):**
- Anthropic: $0-25
- Stripe: $0 (only on sales)
- Supabase: $0-25
- **Total: $0-50/month** to start

---

## NEXT STEPS

1. **Get Anthropic API Key** (5 min) - Use GitHub Education or sign up
2. **Get Stripe Keys** (5 min) - Use test mode for free
3. **Set up Supabase** (10 min) - Free database for 500MB
4. **Create .env file** (2 min) - Add all three above
5. **Test** (5 min) - Run `python python-tools/fact_checker.py`
6. **Launch server** (1 min) - Run `uvicorn python-tools/api_server:app --reload`
7. **View docs** - Open http://localhost:8000/docs

**Total time: ~30 minutes to full API setup!**
