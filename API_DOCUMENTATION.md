# Verity Systems - Super Fact-Checking Platform

## 🎯 Overview

Verity Systems is an enterprise-grade AI-powered fact-checking platform that combines **14+ free and open-source APIs** into a single "super model" for maximum accuracy and reliability.

## 🚀 Key Features

- **Multi-Source Verification**: Aggregates 14+ fact-checking sources
- **AI-Powered Analysis**: Claude, GPT-4, Llama 3.1, Perplexity, and specialized NLP models
- **Enterprise Security**: AES-256-GCM encryption, JWT auth, HMAC signing, rate limiting
- **Real-Time Processing**: Async architecture for sub-2-second response times
- **Consensus Algorithm**: Weighted voting across AI models for accurate verdicts
- **GDPR Compliant**: Built-in PII anonymization and audit logging

---

## 📦 Integrated APIs & Services (14 Providers)

### AI/LLM Providers

| Provider | Model | Free Tier | Special Access |
|----------|-------|-----------|----------------|
| **Anthropic** | Claude 3.5 Sonnet | - | GitHub Education: $25/mo |
| **Azure OpenAI** | GPT-4 | - | GitHub Education: $100 credits |
| **Groq** | Llama 3.1 70B | 30 req/min | ✅ Free |
| **Perplexity AI** | Sonar (Llama) | Limited | Citations included |
| **Hugging Face** | NLI/Stance models | 1000 req/day | Extra credits |
| **OpenRouter** | Gemma 2 9B | Free models | Multi-model access |

### Fact-Checking & Search APIs

| Provider | Type | Free Tier | API Key Required |
|----------|------|-----------|------------------|
| **Google Fact Check** | Fact-check aggregator | 10,000/day | Yes |
| **Serper** | Google Search API | 2,500/month | Yes |
| **NewsAPI** | News search | 100/day | Yes |
| **ClaimBuster** | Claim detection | Research use | Yes |
| **Polygon.io** | Financial data | 5/min | Yes |

### Knowledge Bases (No API Key Required)

| Provider | Type | Rate Limit |
|----------|------|------------|
| **Wikipedia** | Encyclopedia | Unlimited |
| **Wikidata** | Structured knowledge | Unlimited |
| **DuckDuckGo** | Instant answers | Unlimited |

### GitHub Education Pack Benefits Used

| Service | Benefit | Value |
|---------|---------|-------|
| **Anthropic** | Monthly API credits | $25/month |
| **Microsoft Azure** | Azure OpenAI credits | $100 |
| **DigitalOcean** | Platform credits | $200 |
| **MongoDB Atlas** | Database credits | $50 + cert |
| **Heroku** | Hosting credits | $312 (2 years) |
| **JetBrains** | All IDEs | Free subscription |
| **Sentry** | Error tracking | 50K events/mo |
| **DataDog** | Monitoring | Free Pro |
| **DataCamp** | Learning | 3 months free |

---

## 🔐 Security Features

### Encryption
- **AES-256-GCM**: Authenticated encryption for sensitive data
- **PBKDF2**: Key derivation with 600,000 iterations (OWASP recommended)
- **Fernet**: Simple encryption for less sensitive data

### Authentication
- **JWT Tokens**: Access and refresh token pairs (RS256/HS256)
- **API Keys**: Secure key generation with `vrt_` prefix
- **HMAC Signing**: Request integrity verification

### Data Protection
- **Input Sanitization**: SQL injection, XSS, path traversal prevention
- **PII Anonymization**: Automatic redaction of emails, phones, SSNs
- **Rate Limiting**: Sliding window algorithm (configurable)
- **Audit Logging**: Tamper-evident logs with HMAC hash chaining

---

## 🛠️ Installation

### Prerequisites
- Python 3.10+
- pip or conda
- Git

### Setup

```bash
# Clone the repository
git clone https://github.com/your-org/verity-systems.git
cd verity-systems

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r python-tools/requirements.txt

# Copy environment template
cp .env.example .env

# Edit .env with your API keys
nano .env  # or use any text editor
```

### Configuration

1. **Get API Keys** (see table below)
2. **Copy `.env.example` to `.env`**
3. **Fill in your API keys**
4. **Generate security keys**:

```bash
# Generate secure keys
python -c "import secrets; print('VERITY_MASTER_KEY=' + secrets.token_hex(32))"
python -c "import secrets; print('JWT_SECRET_KEY=' + secrets.token_hex(32))"
```

---

## 🔑 Getting API Keys

### Free APIs (No Credit Card Required)

#### Google Fact Check API
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable "Fact Check Tools API"
4. Create credentials (API Key)
5. Copy to `GOOGLE_FACTCHECK_API_KEY`

#### NewsAPI
1. Go to [newsapi.org](https://newsapi.org/)
2. Sign up for free account
3. Copy API key to `NEWS_API_KEY`

#### Groq (Fast Llama Inference)
1. Go to [console.groq.com](https://console.groq.com/)
2. Sign up for free account
3. Create API key
4. Copy to `GROQ_API_KEY`

#### Hugging Face
1. Go to [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)
2. Create access token
3. Copy to `HUGGINGFACE_API_KEY`

#### ClaimBuster (Research/Education)
1. Go to [ClaimBuster](https://idir.uta.edu/claimbuster/)
2. Request API access for research
3. Copy to `CLAIMBUSTER_API_KEY`

### GitHub Education Pack

If you're a student, apply for [GitHub Education](https://education.github.com/pack) to get:
- **Anthropic**: $25/month for Claude API
- **DigitalOcean**: $200 cloud credits
- **And many more!**

---

## 🚀 Running the Application

### Start the API Server

```bash
cd python-tools
python api_server.py
```

The server will start at `http://localhost:8000`

### API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Test the Super Model

```bash
cd python-tools
python verity_supermodel.py
```

---

## 📡 API Endpoints

### Verify a Claim
```bash
curl -X POST "http://localhost:8000/v1/verify" \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{"claim": "The Earth is approximately 4.5 billion years old."}'
```

### Response
```json
{
  "request_id": "abc123...",
  "claim": "The Earth is approximately 4.5 billion years old.",
  "status": "verified_true",
  "confidence_score": 0.95,
  "summary": "This claim appears to be TRUE. Analyzed using 7 sources. 5 high-credibility sources referenced.",
  "sources_count": 7,
  "fact_checks_count": 2,
  "warnings": [],
  "processing_time_ms": 1250.5
}
```

### Batch Verification
```bash
curl -X POST "http://localhost:8000/v1/verify/batch" \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{"claims": ["Claim 1", "Claim 2", "Claim 3"]}'
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     VERITY SUPER MODEL                       │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │  Anthropic  │  │    Groq     │  │ Hugging Face │         │
│  │   Claude    │  │  Llama 3.1  │  │     NLI     │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│         │               │                │                  │
│         └───────────────┴────────────────┘                  │
│                         │                                   │
│                   ┌─────┴─────┐                             │
│                   │ Consensus │                             │
│                   │  Engine   │                             │
│                   └─────┬─────┘                             │
│         ┌───────────────┼───────────────┐                  │
│  ┌──────┴──────┐ ┌──────┴──────┐ ┌──────┴──────┐          │
│  │   Google    │ │  Wikipedia  │ │   NewsAPI   │          │
│  │ Fact Check  │ │  + Wikidata │ │ + DuckDuckGo│          │
│  └─────────────┘ └─────────────┘ └─────────────┘          │
├─────────────────────────────────────────────────────────────┤
│                    SECURITY LAYER                           │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐      │
│  │ AES-256  │ │   JWT    │ │  Rate    │ │  Audit   │      │
│  │ Encrypt  │ │  Auth    │ │ Limiting │ │ Logging  │      │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘      │
└─────────────────────────────────────────────────────────────┘
```

---

## 📊 Verification Process

1. **Input Sanitization**: Remove XSS, SQL injection, validate length
2. **PII Anonymization**: Redact emails, phones, sensitive data
3. **Parallel API Calls**: Query all available providers concurrently
4. **Result Aggregation**: Collect responses from all sources
5. **Consensus Calculation**: Weight sources by credibility
6. **Confidence Scoring**: Calculate final confidence (0-100%)
7. **Response Generation**: Format results with sources and analysis

---

## 🔧 Configuration Options

### Provider Selection
```python
# Use specific providers only
result = await model.verify_claim(
    claim="Your claim here",
    providers=["Google Fact Check", "Wikipedia", "Anthropic Claude"]
)
```

### Security Settings
```python
# Custom rate limits
rate_limiter = RateLimiter()
allowed, info = rate_limiter.check_rate_limit(
    client_id="user123",
    limit=1000,  # requests
    window_seconds=3600  # per hour
)
```

---

## 🧪 Testing

```bash
# Run all tests
pytest python-tools/tests/

# Run with coverage
pytest --cov=python-tools python-tools/tests/

# Run security tests
python python-tools/security_utils.py
```

---

## 📁 Project Structure

```
verity-systems/
├── python-tools/
│   ├── verity_supermodel.py    # Main fact-checking engine
│   ├── security_utils.py       # Security utilities
│   ├── api_server.py           # FastAPI backend
│   ├── fact_checker.py         # Legacy simple checker
│   └── requirements.txt        # Python dependencies
├── public/
│   ├── index.html              # Frontend
│   └── assets/                 # CSS, JS, images
├── .env.example                # Environment template
├── package.json                # Node.js config
├── vercel.json                 # Vercel deployment
└── README.md                   # This file
```

---

## 🚢 Deployment

### Vercel (Frontend)
```bash
vercel deploy
```

### DigitalOcean (API Server)
Use GitHub Education credits ($200) for:
1. Create Droplet (Ubuntu)
2. Install Python and dependencies
3. Set up systemd service
4. Configure nginx reverse proxy

### Docker
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY python-tools/ .
RUN pip install -r requirements.txt
CMD ["python", "api_server.py"]
```

---

## 📄 License

MIT License - See LICENSE file

---

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing`)
5. Open a Pull Request

---

## 📞 Support

- **Documentation**: `/docs` endpoint
- **Issues**: GitHub Issues
- **Email**: support@verity-systems.com

---

## 🙏 Acknowledgments

- GitHub Education for providing free API credits
- Open-source fact-checking community
- All API providers offering free tiers

---

*Built with ❤️ for truth and accuracy*
