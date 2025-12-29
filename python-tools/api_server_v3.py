"""
Verity Systems - Enhanced API Server v3.0
Industry-Leading Fact-Checking API

This is the enhanced API server that integrates:
- 28+ AI models and data sources
- Advanced consensus engine
- Evidence chain tracking
- Bias detection
- Detailed explanations
- Real-time webhooks
- Analytics dashboard endpoints
- Multi-language support
"""

import os
import time
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from contextlib import asynccontextmanager
import logging
import json
import hashlib

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Loaded environment variables from .env")
except ImportError:
    print("⚠️ python-dotenv not installed, using system environment variables")

from fastapi import FastAPI, HTTPException, Depends, Request, Response, status, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field, validator
import uvicorn

# Import our enhanced modules
from verity_supermodel import VeritySuperModel, VerificationResult, VerificationStatus
from enhanced_providers import get_all_enhanced_providers, PROVIDER_INFO
from verity_engine import (
    VerityEngine, 
    EnhancedVerificationResult,
    VerdictType,
    ClaimAnalyzer
)
from security_utils import (
    JWTService, 
    InputValidator, 
    RateLimiter, 
    AuditLogger,
    EncryptionService,
    DataAnonymizer,
    RequestSigner
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('VerityAPIv3')


# ============================================================
# LIFESPAN MANAGEMENT
# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    logger.info("🚀 Starting Verity API Server v3.0...")
    
    # Initialize core services
    app.state.model = VeritySuperModel()
    app.state.engine = VerityEngine()
    app.state.analyzer = ClaimAnalyzer()
    
    # Add enhanced providers
    enhanced = get_all_enhanced_providers()
    app.state.model.providers.extend(enhanced)
    
    # Security services
    app.state.jwt_service = JWTService()
    app.state.rate_limiter = RateLimiter()
    app.state.audit = AuditLogger()
    app.state.encryption = EncryptionService()
    app.state.request_signer = RequestSigner()
    
    # Analytics tracking
    app.state.analytics = {
        'total_requests': 0,
        'verdicts': {},
        'avg_response_time': 0,
        'total_response_time': 0
    }
    
    # Webhook subscriptions
    app.state.webhooks = {}
    
    logger.info(f"✓ Initialized with {len(app.state.model.providers)} providers")
    logger.info("✓ All services ready")
    
    yield
    
    logger.info("👋 Shutting down Verity API Server v3.0...")


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="Verity Systems API v3",
    description="""
    ## 🎯 Industry-Leading AI-Powered Fact-Checking Platform
    
    Verity Systems v3 provides the most comprehensive fact-checking solution available,
    combining **28+ AI models** and **data sources** with advanced **consensus algorithms**.
    
    ### 🚀 What's New in v3
    
    - **Enhanced Verification Engine** - Multi-model consensus with confidence calibration
    - **Evidence Chain Tracking** - Full audit trail of evidence and reasoning
    - **Bias Detection** - Identifies potential bias in claims and sources
    - **Claim Decomposition** - Breaks complex claims into verifiable sub-claims
    - **Detailed Explanations** - Human-readable analysis with recommendations
    - **Real-time Webhooks** - Get notified when verifications complete
    - **Analytics Dashboard** - Track usage and accuracy metrics
    
    ### 🤖 AI Models Integrated
    
    **Premium AI:**
    - Anthropic Claude 3.5 Sonnet
    - GPT-4 (via Azure)
    - Google Gemini Pro
    - Mistral Large
    
    **Open Source (via Groq/Together):**
    - Llama 3 70B
    - Mixtral 8x7B
    - Qwen 72B
    - DeepSeek
    
    **Specialized:**
    - Perplexity AI (web search)
    - Cohere Command (classification)
    - Hugging Face (NLI models)
    
    ### 📚 Data Sources
    
    - Google Fact Check API
    - Wikipedia & Wikidata
    - Semantic Scholar (academic)
    - PubMed (medical)
    - CrossRef (citations)
    - NewsAPI
    - Snopes, PolitiFact, Full Fact
    
    ### 🔐 Security
    
    - AES-256-GCM encryption
    - JWT authentication
    - Rate limiting
    - Request signing
    - GDPR-compliant data handling
    
    ---
    
    ### Quick Start
    
    ```python
    import requests
    
    response = requests.post(
        "https://api.verity-systems.com/v3/verify",
        headers={"X-API-Key": "your-api-key"},
        json={"claim": "The Earth is approximately 4.5 billion years old"}
    )
    print(response.json())
    ```
    """,
    version="3.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
    contact={
        "name": "Verity Systems Support",
        "url": "https://verity-systems.com/support",
        "email": "api@verity-systems.com"
    },
    license_info={
        "name": "Proprietary",
        "url": "https://verity-systems.com/license"
    }
)

# Security schemes
bearer_scheme = HTTPBearer(auto_error=False)
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


# ============================================================
# MIDDLEWARE
# ============================================================

# Compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:5500",
        "https://verity-systems.vercel.app",
        "https://*.vercel.app",
        "https://verity-systems.com",
        "https://*.verity-systems.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=[
        "X-RateLimit-Limit", 
        "X-RateLimit-Remaining", 
        "X-RateLimit-Reset",
        "X-Request-ID",
        "X-Process-Time"
    ]
)

# Trusted hosts
app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=["localhost", "127.0.0.1", "*.vercel.app", "*.verity-systems.com"]
)


@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    """Add security headers"""
    response = await call_next(request)
    
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    
    return response


@app.middleware("http")
async def request_tracking_middleware(request: Request, call_next):
    """Track requests and add timing"""
    start_time = time.time()
    
    request_id = f"vrt_{int(time.time() * 1000)}_{hashlib.md5(str(request.url).encode()).hexdigest()[:8]}"
    request.state.request_id = request_id
    
    logger.info(f"[{request_id}] {request.method} {request.url.path}")
    
    response = await call_next(request)
    
    process_time = (time.time() - start_time) * 1000
    response.headers["X-Process-Time"] = f"{process_time:.2f}ms"
    response.headers["X-Request-ID"] = request_id
    
    # Update analytics
    app.state.analytics['total_requests'] += 1
    app.state.analytics['total_response_time'] += process_time
    app.state.analytics['avg_response_time'] = (
        app.state.analytics['total_response_time'] / 
        app.state.analytics['total_requests']
    )
    
    logger.info(f"[{request_id}] Completed in {process_time:.2f}ms - Status: {response.status_code}")
    
    return response


# ============================================================
# REQUEST/RESPONSE MODELS
# ============================================================

class ClaimRequestV3(BaseModel):
    """Enhanced claim verification request"""
    claim: str = Field(..., min_length=10, max_length=10000, description="The claim to verify")
    providers: Optional[List[str]] = Field(None, description="Specific providers to use")
    detail_level: str = Field("standard", description="Response detail: minimal, standard, or comprehensive")
    deep_analysis: bool = Field(False, description="Enable thorough multi-pass analysis (slower but more accurate)")
    include_sources: bool = Field(True, description="Include source details")
    include_evidence: bool = Field(True, description="Include evidence chain")
    include_reasoning: bool = Field(True, description="Include reasoning chain")
    language: str = Field("en", description="Response language (en, es, fr, de, etc.)")
    webhook_url: Optional[str] = Field(None, description="URL to POST results when complete")
    
    @validator('claim')
    def validate_claim(cls, v):
        return InputValidator.sanitize_text(v)
    
    @validator('detail_level')
    def validate_detail_level(cls, v):
        if v not in ['minimal', 'standard', 'comprehensive']:
            raise ValueError('detail_level must be minimal, standard, or comprehensive')
        return v


class QuickCheckRequest(BaseModel):
    """Quick fact-check request for simple claims"""
    claim: str = Field(..., min_length=5, max_length=500)
    
    @validator('claim')
    def validate_claim(cls, v):
        return InputValidator.sanitize_text(v)


class BatchClaimRequestV3(BaseModel):
    """Batch verification request"""
    claims: List[str] = Field(..., min_items=1, max_items=25)
    providers: Optional[List[str]] = None
    detail_level: str = Field("minimal")


class WebhookRegistration(BaseModel):
    """Webhook registration model"""
    url: str
    events: List[str] = Field(default=['verification_complete'])
    secret: Optional[str] = None


class AnalyticsQuery(BaseModel):
    """Analytics query parameters"""
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    group_by: str = Field("day", description="day, week, or month")


# Response models
class VerificationResponseV3(BaseModel):
    """Standard verification response"""
    request_id: str
    claim: str
    verdict: str
    confidence: float
    summary: str
    recommendation: str
    sources_count: int
    processing_time_ms: float
    timestamp: str


class DetailedVerificationResponse(VerificationResponseV3):
    """Detailed verification response"""
    confidence_breakdown: Dict[str, float]
    evidence: Dict[str, Any]
    reasoning_chain: List[Dict]
    bias_indicators: List[Dict]
    sources: List[Dict]
    ai_analysis: Dict[str, str]
    warnings: List[str]


class QuickCheckResponse(BaseModel):
    """Quick check response"""
    claim: str
    verdict: str
    confidence: float
    one_line_summary: str


# ============================================================
# DEPENDENCIES
# ============================================================

async def get_api_key(
    api_key: Optional[str] = Depends(api_key_header),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme)
) -> str:
    """Validate API key or Bearer token"""
    if api_key:
        if api_key.startswith('vrt_') or InputValidator.validate_api_key(api_key):
            return api_key
        raise HTTPException(status_code=401, detail="Invalid API key format")
    
    if credentials:
        jwt_service = JWTService()
        payload = jwt_service.verify_token(credentials.credentials)
        if payload:
            return payload.get('user_id', 'authenticated')
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    # Allow unauthenticated access for demo (with stricter rate limits)
    return "demo_user"


async def check_rate_limit(request: Request, client_id: str = Depends(get_api_key)):
    """Check rate limits"""
    rate_limiter: RateLimiter = request.app.state.rate_limiter
    
    # Different limits for different users
    if client_id == "demo_user":
        limit, window = 10, 3600  # 10/hour for demo
    elif client_id.startswith('vrt_'):
        limit, window = 1000, 3600  # 1000/hour for API key users
    else:
        limit, window = 100, 3600  # 100/hour default
    
    allowed, info = rate_limiter.check_rate_limit(client_id, limit, window)
    request.state.rate_limit_info = info
    
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail={
                "error": "Rate limit exceeded",
                "limit": info['limit'],
                "reset_at": info['reset'],
                "retry_after": info['window_seconds']
            }
        )
    
    return client_id


# ============================================================
# API ENDPOINTS - GENERAL
# ============================================================

@app.get("/", tags=["General"])
async def root():
    """API root - service information"""
    return {
        "service": "Verity Systems API",
        "version": "3.0.0",
        "status": "operational",
        "documentation": "/docs",
        "endpoints": {
            "verify": "/v3/verify",
            "quick_check": "/v3/quick-check",
            "batch": "/v3/verify/batch",
            "health": "/health",
            "providers": "/v3/providers",
            "analytics": "/v3/analytics"
        }
    }


@app.get("/health", tags=["General"])
async def health_check(request: Request):
    """Comprehensive health check"""
    model: VeritySuperModel = request.app.state.model
    
    # Check provider status
    providers_status = {}
    available_count = 0
    for provider in model.providers:
        is_available = provider.is_available
        providers_status[provider.name] = is_available
        if is_available:
            available_count += 1
    
    # Overall health
    health_status = "healthy" if available_count >= 5 else "degraded" if available_count >= 2 else "unhealthy"
    
    return {
        "status": health_status,
        "version": "3.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "providers": {
            "total": len(model.providers),
            "available": available_count,
            "details": providers_status
        },
        "analytics": {
            "total_requests": request.app.state.analytics['total_requests'],
            "avg_response_time_ms": round(request.app.state.analytics['avg_response_time'], 2)
        }
    }


@app.get("/v3/providers", tags=["Information"])
async def list_providers(request: Request):
    """List all available providers with details"""
    model: VeritySuperModel = request.app.state.model
    
    providers = []
    categories = {
        'ai_models': [],
        'fact_checkers': [],
        'search_engines': [],
        'academic': [],
        'other': []
    }
    
    for provider in model.providers:
        info = {
            'name': provider.name,
            'available': provider.is_available,
            'type': type(provider).__name__
        }
        providers.append(info)
        
        # Categorize
        name_lower = provider.name.lower()
        if any(ai in name_lower for ai in ['claude', 'gpt', 'llama', 'gemini', 'mistral', 'groq', 'cohere']):
            categories['ai_models'].append(info)
        elif any(fc in name_lower for fc in ['fact', 'snopes', 'politifact', 'fullfact']):
            categories['fact_checkers'].append(info)
        elif any(se in name_lower for se in ['search', 'tavily', 'brave', 'serper', 'duck']):
            categories['search_engines'].append(info)
        elif any(ac in name_lower for ac in ['semantic', 'pubmed', 'crossref', 'wikidata']):
            categories['academic'].append(info)
        else:
            categories['other'].append(info)
    
    return {
        'total_providers': len(providers),
        'available_providers': sum(1 for p in providers if p['available']),
        'categories': categories,
        'all_providers': providers
    }


# ============================================================
# API ENDPOINTS - VERIFICATION
# ============================================================

@app.post("/v3/verify", tags=["Verification"])
async def verify_claim_v3(
    request: Request,
    claim_request: ClaimRequestV3,
    background_tasks: BackgroundTasks,
    client_id: str = Depends(check_rate_limit)
):
    """
    🎯 Main Verification Endpoint
    
    Performs comprehensive fact-checking using multiple AI models and sources.
    
    **Features:**
    - Multi-model consensus
    - Evidence chain tracking
    - Bias detection
    - Detailed explanations
    
    **Detail Levels:**
    - `minimal`: Just verdict and confidence
    - `standard`: Verdict, summary, key sources
    - `comprehensive`: Full analysis with reasoning chain
    
    **Deep Analysis Mode:**
    When `deep_analysis=true`, the system performs:
    - Multi-pass claim decomposition
    - Cross-reference verification
    - Source reliability analysis
    - Temporal context checking
    - Bias and manipulation detection
    - Expert source prioritization
    
    This mode takes longer (10-30 seconds) but provides higher accuracy.
    """
    model: VeritySuperModel = request.app.state.model
    engine: VerityEngine = request.app.state.engine
    audit: AuditLogger = request.app.state.audit
    
    try:
        start_time = time.time()
        
        # Anonymize PII
        claim = DataAnonymizer.anonymize_text(claim_request.claim)
        
        # Determine timeout and provider set based on analysis mode
        if claim_request.deep_analysis:
            timeout = 45.0  # Longer timeout for deep analysis
            logger.info(f"Deep analysis mode enabled for claim: {claim[:50]}...")
        else:
            timeout = 30.0
        
        # Run verification through super model
        basic_result = await model.verify_claim(
            claim=claim,
            client_id=client_id,
            use_cache=not claim_request.deep_analysis,  # Don't use cache for deep analysis
            providers=claim_request.providers
        )
        
        # Get provider results for enhanced analysis
        provider_results = []
        providers_to_check = model.providers
        
        # For deep analysis, ensure we check ALL available providers
        if claim_request.deep_analysis:
            # First pass: gather all provider results
            tasks = []
            for provider in providers_to_check:
                if provider.is_available:
                    tasks.append(asyncio.create_task(
                        asyncio.wait_for(
                            provider.check_claim(claim),
                            timeout=timeout
                        )
                    ))
            
            if tasks:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                for i, result in enumerate(results):
                    if not isinstance(result, Exception) and result:
                        provider = providers_to_check[i]
                        provider_results.append({
                            'provider': provider.name,
                            'results': result,
                            'success': True
                        })
            
            # Second pass: Re-query high-value providers for confirmation
            high_value_providers = ['Claude', 'GPT4', 'Perplexity', 'GoogleFactCheck']
            for provider in providers_to_check:
                if provider.name in high_value_providers and provider.is_available:
                    try:
                        # Ask for explicit analysis with reasoning
                        confirmation = await asyncio.wait_for(
                            provider.check_claim(f"Analyze this claim step by step: {claim}"),
                            timeout=20.0
                        )
                        if confirmation:
                            provider_results.append({
                                'provider': f"{provider.name}_confirmation",
                                'results': confirmation,
                                'success': True
                            })
                    except:
                        pass
        else:
            # Standard mode: single pass
            for provider in providers_to_check:
                if provider.is_available:
                    try:
                        results = await asyncio.wait_for(
                            provider.check_claim(claim),
                            timeout=timeout
                        )
                        provider_results.append({
                            'provider': provider.name,
                            'results': results,
                            'success': True
                        })
                    except:
                        pass
        
        # Run through enhanced engine with deep analysis flag
        enhanced_result = await engine.verify(
            claim, 
            provider_results, 
            client_id,
            deep_mode=claim_request.deep_analysis
        )
        
        # Update analytics
        verdict_key = enhanced_result.primary_verdict.value
        request.app.state.analytics['verdicts'][verdict_key] = \
            request.app.state.analytics['verdicts'].get(verdict_key, 0) + 1
        
        # Audit log
        audit.log(
            action='claim_verification_v3',
            actor=client_id,
            resource='verify',
            details={
                'claim_hash': enhanced_result.claim_hash,
                'verdict': enhanced_result.primary_verdict.value,
                'confidence': enhanced_result.confidence_score,
                'providers_used': len(provider_results)
            }
        )
        
        # Send webhook if configured
        if claim_request.webhook_url:
            background_tasks.add_task(
                send_webhook,
                claim_request.webhook_url,
                enhanced_result.to_dict()
            )
        
        processing_time = (time.time() - start_time) * 1000
        
        # Build response based on detail level
        if claim_request.detail_level == 'minimal':
            return {
                'request_id': enhanced_result.request_id,
                'verdict': enhanced_result.primary_verdict.value,
                'confidence': round(enhanced_result.confidence_score, 2),
                'processing_time_ms': round(processing_time, 2)
            }
        
        elif claim_request.detail_level == 'standard':
            return {
                'request_id': enhanced_result.request_id,
                'claim': claim,
                'verdict': enhanced_result.primary_verdict.value,
                'confidence': round(enhanced_result.confidence_score, 2),
                'summary': enhanced_result.executive_summary,
                'recommendation': enhanced_result.recommendation,
                'sources_count': len(enhanced_result.sources_consulted),
                'high_quality_sources': enhanced_result.high_quality_source_count,
                'warnings': enhanced_result.warnings,
                'processing_time_ms': round(processing_time, 2),
                'timestamp': enhanced_result.timestamp.isoformat()
            }
        
        else:  # comprehensive
            return enhanced_result.to_dict()
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception(f"Verification error: {e}")
        raise HTTPException(status_code=500, detail="Verification failed. Please try again.")


@app.post("/v3/quick-check", response_model=QuickCheckResponse, tags=["Verification"])
async def quick_check(
    request: Request,
    check_request: QuickCheckRequest,
    client_id: str = Depends(check_rate_limit)
):
    """
    ⚡ Quick Fact-Check
    
    Fast verification for simple claims. Returns verdict in under 2 seconds.
    Best for straightforward factual statements.
    """
    model: VeritySuperModel = request.app.state.model
    
    try:
        claim = check_request.claim
        
        # Use only the fastest providers
        fast_result = await model.verify_claim(
            claim=claim,
            client_id=client_id,
            providers=['Wikipedia', 'DuckDuckGo', 'Groq']
        )
        
        # Map to simple verdict
        verdict_map = {
            VerificationStatus.VERIFIED_TRUE: "TRUE",
            VerificationStatus.VERIFIED_FALSE: "FALSE",
            VerificationStatus.PARTIALLY_TRUE: "PARTIALLY_TRUE",
            VerificationStatus.UNVERIFIABLE: "UNVERIFIABLE",
            VerificationStatus.NEEDS_CONTEXT: "NEEDS_CONTEXT",
            VerificationStatus.DISPUTED: "DISPUTED"
        }
        
        return QuickCheckResponse(
            claim=claim,
            verdict=verdict_map.get(fast_result.status, "UNVERIFIABLE"),
            confidence=round(fast_result.confidence_score, 2),
            one_line_summary=fast_result.analysis_summary[:200]
        )
    
    except Exception as e:
        logger.exception(f"Quick check error: {e}")
        raise HTTPException(status_code=500, detail="Quick check failed")


@app.post("/v3/verify/batch", tags=["Verification"])
async def verify_batch_v3(
    request: Request,
    batch_request: BatchClaimRequestV3,
    background_tasks: BackgroundTasks,
    client_id: str = Depends(check_rate_limit)
):
    """
    📦 Batch Verification
    
    Verify up to 25 claims in a single request.
    Results are returned in the same order as input claims.
    """
    model: VeritySuperModel = request.app.state.model
    
    results = []
    for i, claim in enumerate(batch_request.claims):
        try:
            sanitized = InputValidator.sanitize_text(claim)
            result = await model.verify_claim(
                claim=sanitized,
                client_id=client_id,
                providers=batch_request.providers
            )
            
            results.append({
                'index': i,
                'claim': claim[:100] + '...' if len(claim) > 100 else claim,
                'verdict': result.status.value,
                'confidence': round(result.confidence_score, 2),
                'summary': result.analysis_summary[:200]
            })
        except Exception as e:
            results.append({
                'index': i,
                'claim': claim[:100],
                'verdict': 'error',
                'error': str(e)
            })
    
    return {
        'results': results,
        'total': len(results),
        'successful': sum(1 for r in results if r.get('verdict') != 'error'),
        'timestamp': datetime.utcnow().isoformat()
    }


@app.post("/v3/analyze-claim", tags=["Analysis"])
async def analyze_claim(
    request: Request,
    claim_request: QuickCheckRequest,
    client_id: str = Depends(check_rate_limit)
):
    """
    🔍 Claim Analysis
    
    Analyze a claim without full verification.
    Returns claim type, entities, and potential bias indicators.
    """
    analyzer: ClaimAnalyzer = request.app.state.analyzer
    
    claim = claim_request.claim
    
    return {
        'claim': claim,
        'analysis': {
            'claim_type': analyzer.classify_claim(claim).value,
            'sub_claims': [
                {'text': text, 'importance': imp}
                for text, imp in analyzer.decompose_claim(claim)
            ],
            'entities': analyzer.extract_entities(claim),
            'bias_indicators': [
                b.to_dict() for b in analyzer.detect_bias(claim)
            ]
        }
    }


# ============================================================
# API ENDPOINTS - WEBHOOKS
# ============================================================

@app.post("/v3/webhooks/register", tags=["Webhooks"])
async def register_webhook(
    webhook: WebhookRegistration,
    client_id: str = Depends(check_rate_limit),
    request: Request = None
):
    """
    🔔 Register Webhook
    
    Register a URL to receive verification results.
    """
    webhook_id = f"wh_{hashlib.md5(webhook.url.encode()).hexdigest()[:12]}"
    
    request.app.state.webhooks[webhook_id] = {
        'url': webhook.url,
        'events': webhook.events,
        'secret': webhook.secret,
        'client_id': client_id,
        'created_at': datetime.utcnow().isoformat()
    }
    
    return {
        'webhook_id': webhook_id,
        'url': webhook.url,
        'events': webhook.events,
        'status': 'registered'
    }


@app.delete("/v3/webhooks/{webhook_id}", tags=["Webhooks"])
async def delete_webhook(
    webhook_id: str,
    client_id: str = Depends(check_rate_limit),
    request: Request = None
):
    """Delete a registered webhook"""
    if webhook_id in request.app.state.webhooks:
        del request.app.state.webhooks[webhook_id]
        return {'status': 'deleted', 'webhook_id': webhook_id}
    
    raise HTTPException(status_code=404, detail="Webhook not found")


async def send_webhook(url: str, data: Dict):
    """Send webhook notification"""
    import aiohttp
    try:
        async with aiohttp.ClientSession() as session:
            await session.post(
                url,
                json=data,
                headers={'Content-Type': 'application/json'},
                timeout=aiohttp.ClientTimeout(total=10)
            )
    except Exception as e:
        logger.error(f"Webhook delivery failed: {e}")


# ============================================================
# API ENDPOINTS - ANALYTICS
# ============================================================

@app.get("/v3/analytics", tags=["Analytics"])
async def get_analytics(
    request: Request,
    client_id: str = Depends(check_rate_limit)
):
    """
    📊 Usage Analytics
    
    Get API usage statistics and verdict distribution.
    """
    analytics = request.app.state.analytics
    
    return {
        'summary': {
            'total_requests': analytics['total_requests'],
            'avg_response_time_ms': round(analytics['avg_response_time'], 2)
        },
        'verdicts': analytics['verdicts'],
        'timestamp': datetime.utcnow().isoformat()
    }


@app.get("/v3/analytics/verdicts", tags=["Analytics"])
async def get_verdict_distribution(
    request: Request,
    client_id: str = Depends(check_rate_limit)
):
    """Get verdict distribution statistics"""
    verdicts = request.app.state.analytics['verdicts']
    total = sum(verdicts.values()) if verdicts else 1
    
    distribution = {
        k: {
            'count': v,
            'percentage': round(v / total * 100, 2)
        }
        for k, v in verdicts.items()
    }
    
    return {
        'total_verifications': total,
        'distribution': distribution
    }


# ============================================================
# API ENDPOINTS - AUTHENTICATION
# ============================================================

@app.post("/v3/auth/api-key", tags=["Authentication"])
async def generate_api_key(
    request: Request,
    client_id: str = Depends(get_api_key)
):
    """
    🔑 Generate API Key
    
    Create a new API key for programmatic access.
    """
    encryption: EncryptionService = request.app.state.encryption
    api_key = encryption.generate_api_key()
    
    return {
        'api_key': api_key,
        'created_at': datetime.utcnow().isoformat(),
        'usage': 'Include in X-API-Key header'
    }


# ============================================================
# STRIPE PAYMENT ENDPOINTS
# ============================================================

# Stripe price IDs - configured via environment variables (loaded from .env)
STRIPE_PRICE_MAP = {
    'starter': os.getenv('STRIPE_STARTER_PRICE_ID', 'price_1SjCYA9HThAyZpOKDiiLhwm2'),
    'pro': os.getenv('STRIPE_PROFESSIONAL_PRICE_ID', 'price_1SjCb99HThAyZpOKiRzqSyIg'),
    'professional': os.getenv('STRIPE_PROFESSIONAL_PRICE_ID', 'price_1SjCb99HThAyZpOKiRzqSyIg'),
    'business': os.getenv('STRIPE_BUSINESS_PRICE_ID', 'price_1SjClu9HThAyZpOKI9tX9bHO'),
}


class CheckoutRequest(BaseModel):
    """Stripe checkout session request"""
    price_id: str
    customer_email: str
    success_url: Optional[str] = None
    cancel_url: Optional[str] = None


class PortalRequest(BaseModel):
    """Stripe customer portal request"""
    return_url: str


@app.post("/v1/checkout", tags=["Payments"], summary="Create Stripe Checkout Session")
async def create_checkout_session(request: Request, checkout_data: CheckoutRequest):
    """
    Create a Stripe Checkout session for subscription payment.
    
    Returns a checkout URL that the client should redirect to.
    """
    try:
        import stripe
        
        stripe_secret = os.getenv('STRIPE_SECRET_KEY')
        if not stripe_secret:
            raise HTTPException(
                status_code=503,
                detail="Payment service not configured. Contact support."
            )
        
        stripe.api_key = stripe_secret
        
        # Determine success and cancel URLs
        origin = request.headers.get('origin', 'http://localhost:8000')
        success_url = checkout_data.success_url or f"{origin}/billing.html?success=true"
        cancel_url = checkout_data.cancel_url or f"{origin}/billing.html?canceled=true"
        
        # Create checkout session
        session = stripe.checkout.Session.create(
            customer_email=checkout_data.customer_email,
            payment_method_types=['card'],
            line_items=[{
                'price': checkout_data.price_id,
                'quantity': 1,
            }],
            mode='subscription',
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={
                'customer_email': checkout_data.customer_email
            }
        )
        
        logger.info(f"Created checkout session {session.id} for {checkout_data.customer_email}")
        
        return {
            'session_id': session.id,
            'checkout_url': session.url
        }
        
    except ImportError:
        raise HTTPException(
            status_code=503,
            detail="Stripe SDK not installed. Run: pip install stripe"
        )
    except Exception as e:
        logger.error(f"Stripe checkout error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Payment error: {str(e)}"
        )


@app.post("/v1/customer-portal", tags=["Payments"], summary="Create Customer Portal Session")
async def create_customer_portal(request: Request, portal_data: PortalRequest):
    """
    Create a Stripe Customer Portal session for subscription management.
    
    Allows customers to manage their subscription, update payment methods, and view invoices.
    """
    try:
        import stripe
        
        stripe_secret = os.getenv('STRIPE_SECRET_KEY')
        if not stripe_secret:
            raise HTTPException(
                status_code=503,
                detail="Payment service not configured."
            )
        
        stripe.api_key = stripe_secret
        
        # In production, you would look up the Stripe customer ID from your database
        # For now, we'll return an error indicating the need for customer lookup
        customer_id = request.headers.get('X-Stripe-Customer-ID')
        
        if not customer_id:
            raise HTTPException(
                status_code=400,
                detail="Customer ID required. Please contact support for portal access."
            )
        
        session = stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=portal_data.return_url
        )
        
        return {
            'portal_url': session.url
        }
        
    except ImportError:
        raise HTTPException(
            status_code=503,
            detail="Stripe SDK not installed."
        )
    except Exception as e:
        logger.error(f"Customer portal error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Portal error: {str(e)}"
        )


@app.post("/v1/webhook/stripe", tags=["Payments"], summary="Stripe Webhook Handler")
async def stripe_webhook(request: Request):
    """
    Handle Stripe webhook events for payment and subscription updates.
    """
    try:
        import stripe
        
        stripe_secret = os.getenv('STRIPE_SECRET_KEY')
        webhook_secret = os.getenv('STRIPE_WEBHOOK_SECRET')
        
        if not stripe_secret:
            raise HTTPException(status_code=503, detail="Stripe not configured")
        
        stripe.api_key = stripe_secret
        
        payload = await request.body()
        sig_header = request.headers.get('stripe-signature')
        
        if webhook_secret and sig_header:
            try:
                event = stripe.Webhook.construct_event(
                    payload, sig_header, webhook_secret
                )
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid payload")
            except stripe.error.SignatureVerificationError:
                raise HTTPException(status_code=400, detail="Invalid signature")
        else:
            # Without webhook secret, parse directly (only for development)
            event = json.loads(payload)
        
        event_type = event.get('type', event.get('event_type', ''))
        
        logger.info(f"Received Stripe webhook: {event_type}")
        
        # Handle specific events
        if event_type == 'checkout.session.completed':
            session = event['data']['object']
            customer_email = session.get('customer_email') or session.get('metadata', {}).get('customer_email')
            logger.info(f"Checkout completed for {customer_email}")
            # Update user subscription in database
            
        elif event_type == 'customer.subscription.updated':
            subscription = event['data']['object']
            logger.info(f"Subscription updated: {subscription['id']}")
            
        elif event_type == 'customer.subscription.deleted':
            subscription = event['data']['object']
            logger.info(f"Subscription cancelled: {subscription['id']}")
            
        elif event_type == 'invoice.payment_failed':
            invoice = event['data']['object']
            logger.warning(f"Payment failed for invoice: {invoice['id']}")
        
        return {'received': True, 'event_type': event_type}
        
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# ERROR HANDLERS
# ============================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    request_id = getattr(request.state, 'request_id', None)
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            'error': True,
            'status_code': exc.status_code,
            'message': exc.detail,
            'request_id': request_id
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unexpected error: {exc}")
    request_id = getattr(request.state, 'request_id', None)
    
    return JSONResponse(
        status_code=500,
        content={
            'error': True,
            'status_code': 500,
            'message': 'An unexpected error occurred',
            'request_id': request_id
        }
    )


# ============================================================
# RUN SERVER
# ============================================================

if __name__ == "__main__":
    print("\n" + "="*70)
    print("🚀 VERITY SYSTEMS API SERVER v3.0")
    print("="*70)
    print("Industry-Leading AI-Powered Fact-Checking")
    print("-"*70)
    print("📚 Documentation: http://localhost:8000/docs")
    print("🔍 ReDoc:         http://localhost:8000/redoc")
    print("❤️  Health:       http://localhost:8000/health")
    print("-"*70)
    print(PROVIDER_INFO)
    print("="*70 + "\n")
    
    uvicorn.run(
        "api_server_v3:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
