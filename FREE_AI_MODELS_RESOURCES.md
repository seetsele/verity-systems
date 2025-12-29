# Free AI Models & Resources for Verity Systems

> **Comprehensive guide to all free/open-source AI models and resources available for implementation**
> 
> Last Updated: December 29, 2025

---

## 📊 Summary

| Category | Count | Status |
|----------|-------|--------|
| Free LLM APIs | 15+ | Available |
| Local Models (Ollama) | 20+ | Available |
| Open Source Models | 50+ | Available |
| Free Search APIs | 8+ | Available |
| Academic APIs | 6+ | Available |
| Free Tiers (Paid Services) | 10+ | Available |

---

## 🤖 FREE LLM APIs (No Cost)

### 1. **Groq** ⭐ (RECOMMENDED - Fastest)
- **URL**: https://console.groq.com/
- **Free Tier**: Unlimited (rate limited)
- **Models Available**:
  - `llama-3.3-70b-versatile` - Best quality, 131K context
  - `llama-3.1-8b-instant` - Fast, 131K context
  - `mixtral-8x7b-32768` - MoE architecture, 32K context
  - `gemma2-9b-it` - Google's model, 8K context
  - `llama-guard-3-8b` - Content moderation
- **Rate Limits**: ~30 RPM, 14,400 RPD
- **Latency**: ~100-500ms (fastest available)
- **Implementation**: ✅ Already integrated

### 2. **OpenRouter Free Models** ⭐
- **URL**: https://openrouter.ai/
- **Free Tier**: Multiple free models
- **Models Available (Free)**:
  - `meta-llama/llama-3.2-3b-instruct:free`
  - `meta-llama/llama-3.1-8b-instruct:free`
  - `mistralai/mistral-7b-instruct:free`
  - `google/gemma-2-9b-it:free`
  - `microsoft/phi-3-mini-128k-instruct:free`
  - `huggingfaceh4/zephyr-7b-beta:free`
  - `openchat/openchat-7b:free`
  - `teknium/openhermes-2.5-mistral-7b:free`
  - `nousresearch/nous-capybara-7b:free`
  - `gryphe/mythomist-7b:free`
- **Rate Limits**: Varies by model
- **Implementation**: ✅ Already integrated

### 3. **HuggingFace Inference API**
- **URL**: https://huggingface.co/inference-api
- **Free Tier**: Rate limited access
- **Models Available**:
  - `meta-llama/Llama-3.2-3B-Instruct`
  - `mistralai/Mistral-7B-Instruct-v0.3`
  - `google/gemma-2-9b-it`
  - `microsoft/Phi-3-mini-4k-instruct`
  - `Qwen/Qwen2.5-7B-Instruct`
  - Thousands more open models
- **Rate Limits**: ~1000 requests/day
- **Implementation**: 🔄 Can be added

### 4. **Cloudflare Workers AI**
- **URL**: https://developers.cloudflare.com/workers-ai/
- **Free Tier**: 10,000 neurons/day (~100k tokens)
- **Models Available**:
  - `@cf/meta/llama-3.1-8b-instruct`
  - `@cf/mistral/mistral-7b-instruct-v0.2`
  - `@cf/google/gemma-7b-it`
  - `@cf/qwen/qwen1.5-7b-chat`
- **Implementation**: 🔄 Can be added

### 5. **Google AI Studio (Gemini)**
- **URL**: https://aistudio.google.com/
- **Free Tier**: 60 RPM, 1,500 RPD
- **Models Available**:
  - `gemini-1.5-flash` - Fast, 1M context
  - `gemini-1.5-pro` - Best quality
  - `gemini-2.0-flash-exp` - Experimental
- **Implementation**: 🔄 Can be added (API key required)

### 6. **Cohere**
- **URL**: https://cohere.com/
- **Free Tier**: Trial API access
- **Models Available**:
  - `command-r` - Good for RAG
  - `command-r-plus` - Best quality
- **Implementation**: 🔄 Can be added

### 7. **Mistral AI (La Plateforme)**
- **URL**: https://console.mistral.ai/
- **Free Tier**: Limited free credits
- **Models Available**:
  - `mistral-small-latest`
  - `mistral-medium-latest`
  - `mistral-large-latest`
- **Implementation**: 🔄 Can be added

---

## 🖥️ LOCAL MODELS (Ollama - Completely Free)

### Setup
```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Or on Windows
winget install Ollama.Ollama
```

### Available Models (Pull with `ollama pull <model>`)

#### Large Models (Require 16GB+ RAM)
| Model | Size | Context | Use Case |
|-------|------|---------|----------|
| `llama3.1:70b` | 40GB | 128K | Best quality |
| `mixtral:8x7b` | 26GB | 32K | MoE, diverse |
| `qwen2.5:32b` | 18GB | 128K | Multilingual |
| `deepseek-coder:33b` | 19GB | 16K | Code |

#### Medium Models (8-16GB RAM)
| Model | Size | Context | Use Case |
|-------|------|---------|----------|
| `llama3.2:11b` | 7GB | 128K | Balanced |
| `mistral:7b` | 4GB | 32K | Fast, quality |
| `gemma2:9b` | 5GB | 8K | Google |
| `qwen2.5:14b` | 9GB | 128K | Best medium |

#### Small Models (4-8GB RAM)
| Model | Size | Context | Use Case |
|-------|------|---------|----------|
| `llama3.2:3b` | 2GB | 128K | Very fast |
| `phi3:3.8b` | 2.3GB | 128K | Microsoft |
| `gemma2:2b` | 1.4GB | 8K | Tiny |
| `qwen2.5:3b` | 2GB | 128K | Multilingual |

#### Specialized Models
| Model | Size | Use Case |
|-------|------|----------|
| `llava:7b` | 4.7GB | Vision |
| `codellama:7b` | 4GB | Code |
| `deepseek-coder:6.7b` | 4GB | Code |
| `neural-chat:7b` | 4GB | Conversation |
| `starling-lm:7b` | 4GB | Reasoning |
| `solar:10.7b` | 6GB | Korean + English |
| `yi:34b` | 19GB | Chinese + English |

### Implementation Status
✅ Already integrated in `verity_unified_llm.py`

---

## 🔍 FREE SEARCH APIs

### 1. **DuckDuckGo Instant Answer API** ⭐
- **URL**: https://api.duckduckgo.com/
- **Cost**: Completely FREE
- **Rate Limit**: Reasonable use
- **Features**: Instant answers, related topics
- **Implementation**: ✅ Integrated

### 2. **Brave Search API**
- **URL**: https://brave.com/search/api/
- **Free Tier**: 2,000 queries/month
- **Features**: Web search, news, images
- **Implementation**: ✅ Integrated

### 3. **Serper (Google Search)**
- **URL**: https://serper.dev/
- **Free Tier**: 2,500 queries/month
- **Features**: Google results, knowledge graph
- **Implementation**: ✅ Integrated

### 4. **Tavily AI**
- **URL**: https://tavily.com/
- **Free Tier**: 1,000 queries/month
- **Features**: AI-powered search, summaries
- **Implementation**: ✅ Integrated

### 5. **SearX/SearXNG**
- **URL**: Public instances (see list below)
- **Cost**: Completely FREE
- **Features**: Meta-search, multiple engines
- **Implementation**: ✅ Integrated

Public SearX Instances:
- https://searx.be
- https://search.sapti.me
- https://searx.tiekoetter.com
- https://searx.work
- https://search.ononoki.org

### 6. **Wikipedia/MediaWiki API**
- **URL**: https://en.wikipedia.org/w/api.php
- **Cost**: Completely FREE
- **Features**: Full Wikipedia access
- **Implementation**: ✅ Integrated (via DBpedia/Wikidata)

---

## 📚 FREE ACADEMIC APIs

### 1. **Semantic Scholar** ⭐
- **URL**: https://api.semanticscholar.org/
- **Cost**: FREE (API key for higher limits)
- **Rate Limit**: 5,000/5min with key
- **Features**: 200M+ papers, citations
- **Implementation**: ✅ Integrated

### 2. **PubMed/NCBI**
- **URL**: https://eutils.ncbi.nlm.nih.gov/
- **Cost**: Completely FREE
- **Rate Limit**: 3/second, 10/second with key
- **Features**: 35M+ biomedical papers
- **Implementation**: ✅ Integrated

### 3. **arXiv API**
- **URL**: https://arxiv.org/help/api
- **Cost**: Completely FREE
- **Rate Limit**: Reasonable use
- **Features**: 2M+ preprints
- **Implementation**: ✅ Integrated

### 4. **CrossRef**
- **URL**: https://api.crossref.org/
- **Cost**: FREE (polite pool)
- **Rate Limit**: 50/second with mailto
- **Features**: 140M+ DOIs, metadata
- **Implementation**: ✅ Integrated

### 5. **OpenAlex**
- **URL**: https://openalex.org/
- **Cost**: Completely FREE
- **Features**: 250M+ works, open access
- **Implementation**: 🔄 Can be added

### 6. **CORE**
- **URL**: https://core.ac.uk/
- **Cost**: FREE (API key required)
- **Features**: 200M+ open access papers
- **Implementation**: 🔄 Can be added

---

## 📰 FREE NEWS APIs

### 1. **NewsAPI**
- **URL**: https://newsapi.org/
- **Free Tier**: 100 requests/day
- **Features**: Headlines, search
- **Implementation**: ✅ Integrated

### 2. **MediaStack**
- **URL**: https://mediastack.com/
- **Free Tier**: 500 requests/month
- **Features**: Global news
- **Implementation**: ✅ Integrated

### 3. **GNews**
- **URL**: https://gnews.io/
- **Free Tier**: 100 requests/day
- **Implementation**: 🔄 Can be added

### 4. **Currents API**
- **URL**: https://currentsapi.services/
- **Free Tier**: 600 requests/day
- **Implementation**: 🔄 Can be added

---

## 🌐 FREE KNOWLEDGE BASE APIs

### 1. **Wikidata**
- **URL**: https://www.wikidata.org/
- **Cost**: Completely FREE
- **Features**: Structured data, entities
- **Implementation**: ✅ Integrated

### 2. **DBpedia**
- **URL**: https://www.dbpedia.org/
- **Cost**: Completely FREE
- **Features**: Wikipedia as linked data
- **Implementation**: ✅ Integrated

### 3. **Wolfram Alpha**
- **URL**: https://www.wolframalpha.com/
- **Free Tier**: 2,000 queries/month
- **Features**: Computational knowledge
- **Implementation**: ✅ Integrated (via ultimate_orchestrator)

---

## 🏛️ FREE OFFICIAL/GOVERNMENT APIs

### 1. **WHO (World Health Organization)**
- **URL**: https://www.who.int/data/gho/
- **Cost**: Completely FREE
- **Features**: Health indicators
- **Implementation**: ✅ Integrated

### 2. **CDC (Centers for Disease Control)**
- **URL**: https://data.cdc.gov/
- **Cost**: Completely FREE
- **Features**: US health data
- **Implementation**: ✅ Integrated

### 3. **Data.gov**
- **URL**: https://catalog.data.gov/
- **Cost**: Completely FREE
- **Features**: US government data
- **Implementation**: 🔄 Can be added

### 4. **EU Open Data Portal**
- **URL**: https://data.europa.eu/
- **Cost**: Completely FREE
- **Features**: European datasets
- **Implementation**: 🔄 Can be added

---

## 🔧 LOW-COST APIs (Cheap Tier)

### 1. **DeepSeek** ⭐ (VERY CHEAP)
- **URL**: https://www.deepseek.com/
- **Pricing**: $0.14/M input, $0.28/M output
- **Models**:
  - `deepseek-chat` - General purpose
  - `deepseek-reasoner` (R1) - Best reasoning
- **Implementation**: ✅ Integrated

### 2. **Together AI**
- **URL**: https://www.together.ai/
- **Free Tier**: $5 credits
- **Pricing**: ~$0.20/M tokens
- **Models**: Llama, Mixtral, etc.
- **Implementation**: ✅ Integrated

### 3. **Fireworks AI**
- **URL**: https://fireworks.ai/
- **Free Tier**: $1 credits
- **Pricing**: ~$0.20/M tokens
- **Implementation**: 🔄 Can be added

### 4. **Anyscale**
- **URL**: https://www.anyscale.com/
- **Free Tier**: Limited
- **Models**: Llama, Mistral
- **Implementation**: 🔄 Can be added

---

## 📊 IMPLEMENTATION STATUS

### Currently Integrated in Verity Systems

```
FREE LLMs:
├── Groq (4 models) ✅
├── OpenRouter (10 free models) ✅
└── Ollama (10+ local models) ✅

CHEAP LLMs:
├── DeepSeek (2 models) ✅
└── Together AI (2 models) ✅

SEARCH ENGINES:
├── DuckDuckGo ✅
├── Brave Search ✅
├── Serper (Google) ✅
├── Tavily ✅
└── SearX (public instances) ✅

ACADEMIC SOURCES:
├── Semantic Scholar ✅
├── PubMed ✅
├── arXiv ✅
└── CrossRef ✅

NEWS SOURCES:
├── NewsAPI ✅
└── MediaStack ✅

KNOWLEDGE BASES:
├── Wikidata ✅
├── DBpedia ✅
└── Wolfram Alpha ✅

OFFICIAL SOURCES:
├── WHO ✅
└── CDC ✅
```

---

## 🚀 RECOMMENDED ADDITIONS

### Priority 1: More Free LLMs
1. **HuggingFace Inference API** - Access to thousands of models
2. **Cloudflare Workers AI** - Edge deployment
3. **Google Gemini** - 60 RPM free tier

### Priority 2: More Search
1. **OpenAlex** - Open academic data
2. **CORE** - Open access papers
3. **GNews** - More news sources

### Priority 3: Specialized
1. **FactCheck.org API** - Fact-check database
2. **Snopes API** - Fact-check database
3. **PolitiFact API** - Political fact-checks

---

## 💰 COST ANALYSIS

### Completely Free Operation
Using only free APIs, Verity can process:
- **~50,000+ verifications/month** with Groq
- **~2,000 web searches/month** with Brave
- **~2,500 Google searches/month** with Serper
- **Unlimited** academic searches
- **Unlimited** local model processing with Ollama

### Low-Cost Operation (~$10/month)
Adding paid APIs:
- DeepSeek: ~$5 for 35M tokens
- Additional search APIs: ~$5

### Enterprise Operation (~$100/month)
Full capacity:
- Multiple LLM providers
- High-volume search APIs
- Premium news access

---

## 📝 API KEY SETUP

```bash
# Add to .env file

# FREE LLMs
GROQ_API_KEY=gsk_...
OPENROUTER_API_KEY=sk-or-...

# CHEAP LLMs
DEEPSEEK_API_KEY=sk-...
TOGETHER_API_KEY=...

# SEARCH
BRAVE_API_KEY=BSA...
SERPER_API_KEY=...
TAVILY_API_KEY=tvly-...

# ACADEMIC
SEMANTIC_SCHOLAR_API_KEY=...

# NEWS
NEWSAPI_KEY=...
MEDIASTACK_API_KEY=...

# OPTIONAL
GOOGLE_API_KEY=...
WOLFRAM_ALPHA_APP_ID=...
```

---

## 🎯 CONCLUSION

Verity Systems can operate **completely free** using:
- **Groq** for LLM inference (fastest)
- **OpenRouter free models** for diversity
- **Ollama** for local/private processing
- **DuckDuckGo + SearX** for web search
- **Academic APIs** for research sources
- **Knowledge bases** for facts

Total monthly cost for basic operation: **$0**

For high-volume production: **$10-100/month**

---

*This document is maintained as part of the Verity Systems Deep Research Mode implementation.*
