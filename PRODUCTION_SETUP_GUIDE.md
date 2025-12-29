# Verity Systems - Production Setup Guide

This guide covers everything needed to get Verity Systems fully operational with payments, authentication, and security.

---

## 📋 Table of Contents

1. [Environment Variables](#1-environment-variables)
2. [Stripe Payment Setup](#2-stripe-payment-setup)
3. [Supabase Authentication Setup](#3-supabase-authentication-setup)
4. [GitHub OAuth Setup](#4-github-oauth-setup)
5. [Google OAuth Setup](#5-google-oauth-setup)
6. [Security Enhancements](#6-security-enhancements)
7. [Running the Servers](#7-running-the-servers)
8. [Troubleshooting](#8-troubleshooting)

---

## 1. Environment Variables

Create a `.env` file in the project root with:

```env
# ============================================
# STRIPE CONFIGURATION
# ============================================
STRIPE_PUBLISHABLE_KEY=pk_test_your_publishable_key_here
STRIPE_SECRET_KEY=sk_test_your_secret_key_here
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret_here

# Stripe Price IDs (create these in Stripe Dashboard)
STRIPE_PRICE_STARTER=price_starter_id
STRIPE_PRICE_PRO=price_professional_id
STRIPE_PRICE_BUSINESS=price_business_id

# ============================================
# SUPABASE CONFIGURATION
# ============================================
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_anon_key_here
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key_here

# ============================================
# AI MODEL API KEYS
# ============================================
OPENAI_API_KEY=sk-your-openai-key
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key
GROQ_API_KEY=gsk_your-groq-key
GOOGLE_AI_KEY=your-google-ai-key
PERPLEXITY_API_KEY=pplx-your-key

# ============================================
# SECURITY
# ============================================
JWT_SECRET=your-jwt-secret-min-32-chars
ENCRYPTION_KEY=your-32-byte-encryption-key
API_RATE_LIMIT=100
```

---

## 2. Stripe Payment Setup

### Step 1: Create Stripe Account
1. Go to [stripe.com](https://stripe.com) and create an account
2. Complete business verification

### Step 2: Get API Keys
1. Go to **Developers → API Keys**
2. Copy the **Publishable key** (`pk_test_...`) 
3. Copy the **Secret key** (`sk_test_...`)
4. Add both to your `.env` file

### Step 3: Create Products & Prices
1. Go to **Products** in Stripe Dashboard
2. Create products for each plan:

   **Starter Plan ($79/month)**
   - Name: "Verity Starter"
   - Price: $79.00/month recurring
   - Copy the Price ID → `STRIPE_PRICE_STARTER`

   **Professional Plan ($199/month)**
   - Name: "Verity Professional"  
   - Price: $199.00/month recurring
   - Copy the Price ID → `STRIPE_PRICE_PRO`

   **Business Plan ($799/month)**
   - Name: "Verity Business"
   - Price: $799.00/month recurring
   - Copy the Price ID → `STRIPE_PRICE_BUSINESS`

### Step 4: Configure Webhooks
1. Go to **Developers → Webhooks**
2. Add endpoint: `https://your-api-domain.com/v1/webhook/stripe`
3. Select events:
   - `checkout.session.completed`
   - `customer.subscription.created`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
   - `invoice.payment_succeeded`
   - `invoice.payment_failed`
4. Copy the **Signing secret** → `STRIPE_WEBHOOK_SECRET`

### Step 5: Update Frontend
In `public/billing.html`, update the Stripe publishable key:
```javascript
const STRIPE_PUBLISHABLE_KEY = 'pk_live_your_actual_key';
```

And update the price IDs:
```javascript
const STRIPE_PRICE_IDS = {
    starter: 'price_actual_starter_id',
    pro: 'price_actual_pro_id',
    business: 'price_actual_business_id',
    enterprise: 'enterprise_custom'
};
```

---

## 3. Supabase Authentication Setup

### Step 1: Create Supabase Project
1. Go to [supabase.com](https://supabase.com)
2. Create a new project
3. Note your project URL and anon key

### Step 2: Enable Email Authentication
1. Go to **Authentication → Providers**
2. Ensure **Email** is enabled
3. Configure email templates under **Email Templates**

### Step 3: Configure Redirect URLs
1. Go to **Authentication → URL Configuration**
2. Add Site URL: `https://your-domain.com`
3. Add Redirect URLs:
   - `http://localhost:8000/dashboard.html`
   - `https://your-domain.com/dashboard.html`

### Step 4: Update Frontend
In `public/assets/js/supabase-client.js`:
```javascript
const SUPABASE_URL = 'https://your-project.supabase.co';
const SUPABASE_ANON_KEY = 'your-anon-key';
```

---

## 4. GitHub OAuth Setup

### Step 1: Create GitHub OAuth App
1. Go to [github.com/settings/developers](https://github.com/settings/developers)
2. Click **New OAuth App**
3. Fill in:
   - **Application name**: Verity Systems
   - **Homepage URL**: `https://your-domain.com`
   - **Authorization callback URL**: `https://your-project.supabase.co/auth/v1/callback`

4. Click **Register application**
5. Copy the **Client ID**
6. Generate and copy the **Client Secret**

### Step 2: Configure in Supabase
1. Go to **Authentication → Providers** in Supabase Dashboard
2. Find **GitHub** and enable it
3. Paste your **Client ID** and **Client Secret**
4. Save

### Step 3: Test
Click the GitHub button on the auth page - it should redirect to GitHub for authentication.

---

## 5. Google OAuth Setup

### Step 1: Create Google Cloud Project
1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Create a new project or select existing
3. Enable the **Google+ API** (or Google Identity)

### Step 2: Configure OAuth Consent Screen
1. Go to **APIs & Services → OAuth consent screen**
2. Choose **External** user type
3. Fill in app information:
   - App name: Verity Systems
   - User support email: your-email
   - Authorized domains: your-domain.com
   - Developer contact: your-email

### Step 3: Create OAuth Credentials
1. Go to **APIs & Services → Credentials**
2. Click **Create Credentials → OAuth client ID**
3. Choose **Web application**
4. Add authorized redirect URI:
   - `https://your-project.supabase.co/auth/v1/callback`
5. Copy **Client ID** and **Client Secret**

### Step 4: Configure in Supabase
1. Go to **Authentication → Providers** in Supabase Dashboard
2. Find **Google** and enable it
3. Paste your **Client ID** and **Client Secret**
4. Save

---

## 6. Security Enhancements

### Free/Open Source Security Tools Implemented

#### 1. Rate Limiting (Built-in)
The API server includes rate limiting via `security_utils.py`:
```python
from security_utils import RateLimiter
limiter = RateLimiter(requests_per_minute=100)
```

#### 2. Helmet.js Equivalent Headers
Security headers are automatically added:
- X-Content-Type-Options: nosniff
- X-Frame-Options: DENY
- X-XSS-Protection: 1; mode=block
- Strict-Transport-Security
- Content-Security-Policy
- Referrer-Policy

#### 3. Input Validation
All inputs are sanitized via `InputValidator`:
```python
from security_utils import InputValidator
clean_input = InputValidator.sanitize_text(user_input)
```

#### 4. AES-256 Encryption
Sensitive data encrypted at rest:
```python
from security_utils import EncryptionService
encrypted = encryption.encrypt(data)
```

### Additional Security Recommendations

#### Add these to your deployment:

**1. Cloudflare (Free tier)**
- DDoS protection
- Web Application Firewall (WAF)
- Bot protection
- Free SSL

**2. Fail2Ban (Self-hosted)**
```bash
sudo apt install fail2ban
# Blocks IPs with too many failed attempts
```

**3. Let's Encrypt SSL**
```bash
sudo apt install certbot
certbot --nginx -d yourdomain.com
```

**4. Content Security Policy**
Already implemented in middleware but can be customized:
```python
response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' https://js.stripe.com"
```

---

## 7. Running the Servers

### Development Mode

**Terminal 1 - Frontend:**
```bash
cd public
python -m http.server 8000
```

**Terminal 2 - API Server:**
```bash
cd python-tools
pip install -r requirements.txt
python api_server_v3.py
```

### Production Mode

**Using Docker:**
```bash
docker-compose up -d
```

**Using PM2 (Node.js process manager):**
```bash
# Install PM2
npm install -g pm2

# Start API server
pm2 start "cd python-tools && python api_server_v3.py" --name verity-api

# Start frontend with nginx (recommended)
```

**Using Gunicorn:**
```bash
cd python-tools
pip install gunicorn
gunicorn api_server_v3:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8081
```

---

## 8. Troubleshooting

### Payments Not Working

**Issue**: "Payment service not configured"
- **Solution**: Add `STRIPE_SECRET_KEY` to `.env` and restart the API server

**Issue**: Checkout redirects fail
- **Solution**: Ensure your domain is in Stripe's allowed domains and CORS is configured

**Issue**: Webhooks not receiving
- **Solution**: Check webhook signing secret and ensure endpoint is publicly accessible

### Authentication Not Working

**Issue**: OAuth buttons do nothing
- **Solution**: Enable providers in Supabase Dashboard → Authentication → Providers

**Issue**: "Provider not enabled" error
- **Solution**: Each OAuth provider needs Client ID/Secret configured in Supabase

**Issue**: Redirect loop after OAuth
- **Solution**: Check redirect URLs in Supabase URL Configuration

### API Errors

**Issue**: CORS errors
- **Solution**: Add your domain to `allow_origins` in `api_server_v3.py`

**Issue**: Rate limit exceeded
- **Solution**: Upgrade plan or wait for rate limit reset (shown in X-RateLimit-Reset header)

### General

**Issue**: Changes not reflecting
- **Solution**: Clear browser cache or use incognito mode

**Issue**: Console errors
- **Solution**: Check browser Developer Tools → Console for specific errors

---

## Quick Checklist

- [ ] `.env` file created with all keys
- [ ] Stripe products and prices created
- [ ] Stripe webhook endpoint configured
- [ ] GitHub OAuth app created
- [ ] Google OAuth credentials created
- [ ] OAuth providers enabled in Supabase
- [ ] Redirect URLs configured in Supabase
- [ ] Frontend files updated with correct keys
- [ ] API server running
- [ ] Frontend server running
- [ ] SSL certificate installed (production)
- [ ] Cloudflare configured (recommended)

---

## Support

If you encounter issues not covered here:
1. Check the API documentation at `/docs`
2. Review server logs for errors
3. Contact support@verity.systems
