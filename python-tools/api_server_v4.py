"""
Verity Systems - API Server v4.0
Production-Ready with Enhanced Infrastructure

Integrates:
- Enhanced verification engine with LiteLLM, Groq, OpenRouter, DeepSeek
- Redis caching for horizontal scaling
- Circuit breakers and retry logic
- Extended data sources (Academic, News, Knowledge bases)
- Prometheus metrics endpoint
- Health monitoring
- Graceful shutdown

Author: Verity Systems
License: MIT
"""

import os
import time
import asyncio
import signal
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from contextlib import asynccontextmanager
import logging
import json
import hashlib

from fastapi import FastAPI, HTTPException, Depends, Request, Response, status, BackgroundTasks
from fastapi.security import HTTPBearer, APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import BaseModel, Field, field_validator
import uvicorn

# Import enhanced modules
from verity_enhanced_orchestrator import (
    EnhancedVerifier,
    VerifierConfig,
    EnhancedVerificationResult,
    get_verifier,
    shutdown_verifier,
    RateLimitExceededError
)
from verity_resilience import (
    StructuredLogger,
    MetricsCollector,
    GracefulShutdown
)

# Import modules integration layer
from verity_modules_integration import (
    get_modules_integrator,
    VerityModulesIntegrator,
    IntegratedAnalysis
)

# Import quota manager
from verity_quota_manager import (
    get_quota_manager,
    PlanTier,
    PlanLimits,
    QuotaManager
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = StructuredLogger('VerityAPIv4')


# ============================================================
# CONFIGURATION
# ============================================================

class AppConfig:
    """Application configuration"""
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"
    API_VERSION = "4.0.0"
    
    # Server settings
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", 8000))
    
    # Rate limiting
    RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", 100))
    RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", 60))
    
    # CORS
    ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")
    
    # Cache
    REDIS_URL = os.getenv("REDIS_URL")
    
    # Timeouts
    REQUEST_TIMEOUT = float(os.getenv("REQUEST_TIMEOUT", 60.0))


config = AppConfig()


# ============================================================
# LIFESPAN MANAGEMENT
# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    logger.info("Starting Verity API Server v4.0...")
    
    # Initialize verifier
    verifier_config = VerifierConfig(
        enable_llm_verification=True,
        enable_caching=True,
        enable_data_sources=True,
        redis_url=config.REDIS_URL,
        request_timeout_seconds=config.REQUEST_TIMEOUT
    )
    
    app.state.verifier = await get_verifier(verifier_config)
    app.state.metrics = MetricsCollector()
    app.state.shutdown = GracefulShutdown()
    
    # Track startup
    app.state.startup_time = datetime.now()
    app.state.request_count = 0
    
    logger.info("All services initialized successfully")
    
    yield
    
    # Graceful shutdown
    logger.info("Shutting down Verity API Server v4.0...")
    await shutdown_verifier()
    logger.info("Shutdown complete")


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="Verity Systems API v4",
    description="""
## 🚀 Production-Ready AI Fact-Checking Platform

### Features

- **Multi-LLM Verification**: LiteLLM, Groq, OpenRouter, DeepSeek, Together AI
- **Extended Data Sources**: Semantic Scholar, PubMed, arXiv, NewsAPI, Wikidata
- **Redis Caching**: Horizontal scaling with distributed cache
- **Circuit Breakers**: Automatic failover and recovery
- **Prometheus Metrics**: Full observability
- **Health Monitoring**: Real-time health checks

### Quick Start

```python
import requests

response = requests.post(
    "http://localhost:8000/api/v4/verify",
    json={"claim": "The Earth is approximately 4.5 billion years old"}
)
print(response.json())
```

### Endpoints

- `POST /api/v4/verify` - Verify a single claim
- `POST /api/v4/batch` - Verify multiple claims
- `GET /health` - Health check
- `GET /health/detailed` - Detailed component health
- `GET /metrics` - Prometheus metrics
- `GET /status` - API status and uptime
    """,
    version="4.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)


# ============================================================
# MIDDLEWARE
# ============================================================

app.add_middleware(GZipMiddleware, minimum_size=1000)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ALLOWED_ORIGINS if config.ALLOWED_ORIGINS != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=[
        "X-Request-ID",
        "X-Process-Time",
        "X-RateLimit-Limit",
        "X-RateLimit-Remaining"
    ]
)


@app.middleware("http")
async def request_middleware(request: Request, call_next):
    """Add request tracking and timing"""
    start_time = time.time()
    
    # Generate request ID
    request_id = hashlib.md5(
        f"{time.time()}{request.client.host}".encode()
    ).hexdigest()[:16]
    request.state.request_id = request_id
    
    # Process request
    response = await call_next(request)
    
    # Calculate timing
    process_time = (time.time() - start_time) * 1000
    
    # Add headers
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time"] = f"{process_time:.2f}ms"
    
    # Log request
    logger.info(
        f"{request.method} {request.url.path} - {response.status_code} - {process_time:.2f}ms",
        request_id=request_id
    )
    
    # Track metrics
    app.state.request_count += 1
    app.state.metrics.record_request(
        endpoint=request.url.path,
        method=request.method,
        status_code=response.status_code,
        duration=process_time / 1000
    )
    
    return response


# ============================================================
# REQUEST/RESPONSE MODELS
# ============================================================

class VerifyRequest(BaseModel):
    """Verification request model"""
    claim: str = Field(..., min_length=10, max_length=10000, description="The claim to verify")
    options: Optional[Dict[str, Any]] = Field(None, description="Optional verification settings")
    
    @field_validator('claim')
    @classmethod
    def sanitize_claim(cls, v: str) -> str:
        # Basic sanitization
        v = v.strip()
        v = ' '.join(v.split())  # Normalize whitespace
        return v


class BatchVerifyRequest(BaseModel):
    """Batch verification request"""
    claims: List[str] = Field(..., min_length=1, max_length=10, description="Claims to verify")
    options: Optional[Dict[str, Any]] = None


class VerifyResponse(BaseModel):
    """Verification response model"""
    request_id: str
    claim: str
    verdict: str
    confidence: float
    summary: str
    explanation: str
    source_count: int
    warnings: List[str]
    processing_time_ms: float
    cache_hit: bool
    timestamp: str


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    version: str
    uptime_seconds: float
    timestamp: str


# ============================================================
# QUOTA & TIER HELPERS
# ============================================================

def get_user_tier(request: Request) -> tuple:
    """
    Extract user ID and tier from request.
    In production, this would validate JWT or API key against database.
    """
    # Check for API key header
    api_key = request.headers.get("X-API-Key", "")
    
    # Check for Authorization header (JWT)
    auth_header = request.headers.get("Authorization", "")
    
    # For demo: parse tier from header or default to free
    tier = request.headers.get("X-User-Tier", "free").lower()
    
    # Get user ID from various sources
    if api_key:
        # Hash API key to create user ID
        user_id = hashlib.md5(api_key.encode()).hexdigest()
    elif auth_header.startswith("Bearer "):
        # In production, decode JWT to get user ID
        token = auth_header[7:]
        user_id = hashlib.md5(token.encode()).hexdigest()
    else:
        # Use IP as fallback for anonymous users
        user_id = f"anon_{request.client.host if request.client else 'unknown'}"
        tier = "free"  # Anonymous users are always free tier
    
    return user_id, tier


def check_feature_access(tier: str, feature: str) -> bool:
    """Check if a tier has access to a feature"""
    try:
        plan_tier = PlanTier(tier.lower())
    except ValueError:
        plan_tier = PlanTier.FREE
    
    limits = PlanLimits.get_limits(plan_tier)
    
    feature_map = {
        "api_access": limits.api_access,
        "nlp_analysis": limits.nlp_analysis,
        "source_credibility": limits.source_credibility,
        "monte_carlo": limits.monte_carlo,
        "temporal_geo": limits.temporal_geo,
        "similar_claims": limits.similar_claims,
    }
    
    return feature_map.get(feature, True)  # Default allow for basic features


# ============================================================
# API ENDPOINTS
# ============================================================

@app.get("/", include_in_schema=False)
async def root():
    """Root endpoint - redirect to docs"""
    return {"message": "Verity API v4.0 - Visit /docs for documentation"}


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Basic health check"""
    uptime = (datetime.now() - app.state.startup_time).total_seconds()
    
    return HealthResponse(
        status="healthy",
        version=config.API_VERSION,
        uptime_seconds=uptime,
        timestamp=datetime.now().isoformat()
    )


@app.get("/health/detailed", tags=["Health"])
async def detailed_health():
    """Detailed component health check"""
    verifier: EnhancedVerifier = app.state.verifier
    health = await verifier.get_health_status()
    
    # Add API-level info
    uptime = (datetime.now() - app.state.startup_time).total_seconds()
    health["api"] = {
        "version": config.API_VERSION,
        "uptime_seconds": uptime,
        "total_requests": app.state.request_count
    }
    
    return health


@app.get("/metrics", response_class=PlainTextResponse, tags=["Monitoring"])
async def prometheus_metrics():
    """Prometheus-compatible metrics endpoint"""
    metrics = app.state.metrics
    
    # Build Prometheus format
    lines = []
    
    # Request counts
    lines.append("# HELP verity_requests_total Total number of requests")
    lines.append("# TYPE verity_requests_total counter")
    lines.append(f'verity_requests_total {app.state.request_count}')
    
    # Get detailed metrics
    all_metrics = metrics.get_all_metrics()
    
    # Request latencies
    lines.append("# HELP verity_request_duration_seconds Request duration in seconds")
    lines.append("# TYPE verity_request_duration_seconds histogram")
    for endpoint, data in all_metrics.get("latencies", {}).items():
        avg = data.get("avg", 0)
        lines.append(f'verity_request_duration_seconds_sum{{endpoint="{endpoint}"}} {avg * data.get("count", 1)}')
        lines.append(f'verity_request_duration_seconds_count{{endpoint="{endpoint}"}} {data.get("count", 0)}')
    
    # Circuit breaker status
    lines.append("# HELP verity_circuit_breaker_status Circuit breaker status (0=closed, 1=open, 2=half-open)")
    lines.append("# TYPE verity_circuit_breaker_status gauge")
    for provider, status in all_metrics.get("circuit_breakers", {}).items():
        status_value = {"closed": 0, "open": 1, "half_open": 2}.get(status.lower(), 0)
        lines.append(f'verity_circuit_breaker_status{{provider="{provider}"}} {status_value}')
    
    # Uptime
    uptime = (datetime.now() - app.state.startup_time).total_seconds()
    lines.append("# HELP verity_uptime_seconds Server uptime in seconds")
    lines.append("# TYPE verity_uptime_seconds gauge")
    lines.append(f"verity_uptime_seconds {uptime}")
    
    return "\n".join(lines)


@app.get("/status", tags=["Status"])
async def api_status():
    """API status and statistics"""
    uptime = (datetime.now() - app.state.startup_time).total_seconds()
    
    return {
        "status": "operational",
        "version": config.API_VERSION,
        "uptime_seconds": uptime,
        "uptime_human": str(timedelta(seconds=int(uptime))),
        "total_requests": app.state.request_count,
        "timestamp": datetime.now().isoformat()
    }


# ============================================================
# QUOTA ENDPOINTS
# ============================================================

@app.get("/api/v4/quota", tags=["Quota"])
async def get_quota_status(req: Request):
    """
    Get current usage quota status for the authenticated user.
    
    Returns daily and monthly usage limits and remaining quota.
    """
    user_id, tier = get_user_tier(req)
    quota_manager = get_quota_manager()
    
    usage = quota_manager.get_usage(user_id, tier)
    
    return {
        "user_id": usage["user_id"],
        "tier": tier,
        "usage": usage["usage"],
        "features": usage["features"],
        "upgrade_url": "/pricing.html" if tier == "free" else None,
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/v4/plans", tags=["Quota"])
async def get_available_plans():
    """
    Get all available subscription plans and their features.
    """
    plans = []
    
    for plan_tier in PlanTier:
        limits = PlanLimits.get_limits(plan_tier)
        
        pricing = {
            "free": {"monthly": 0, "annual": 0},
            "pro": {"monthly": 29, "annual": 23},
            "team": {"monthly": 99, "annual": 79},
            "enterprise": {"monthly": None, "annual": None}
        }
        
        plans.append({
            "tier": plan_tier.value,
            "name": plan_tier.value.title(),
            "pricing": pricing.get(plan_tier.value, {}),
            "limits": {
                "verifications_per_month": limits.verifications_per_month if limits.verifications_per_month < 999999 else "unlimited",
                "verifications_per_day": limits.verifications_per_day if limits.verifications_per_day < 999999 else "unlimited",
                "data_sources": limits.data_sources,
                "team_members": limits.team_members if limits.team_members < 999999 else "unlimited"
            },
            "features": {
                "api_access": limits.api_access,
                "nlp_analysis": limits.nlp_analysis,
                "source_credibility": limits.source_credibility,
                "monte_carlo": limits.monte_carlo,
                "temporal_geo": limits.temporal_geo,
                "similar_claims": limits.similar_claims,
                "priority_support": limits.priority_support
            }
        })
    
    return {
        "plans": plans,
        "current_promotion": None,
        "timestamp": datetime.now().isoformat()
    }


@app.post("/api/v4/verify", response_model=VerifyResponse, tags=["Verification"])
async def verify_claim(request: VerifyRequest, req: Request):
    """
    Verify a single claim.
    
    This endpoint uses multiple AI models, fact-checking APIs, and
    academic sources to verify the truthfulness of a claim.
    
    **Example:**
    ```json
    {
        "claim": "The Great Wall of China is visible from space"
    }
    ```
    """
    start_time = time.time()
    request_id = req.state.request_id
    
    try:
        # Check quota
        user_id, tier = get_user_tier(req)
        quota_manager = get_quota_manager()
        
        allowed, quota_details = quota_manager.check_quota(user_id, tier)
        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=quota_details
            )
        
        verifier: EnhancedVerifier = app.state.verifier
        
        # Perform verification
        result = await verifier.verify_claim(
            claim=request.claim,
            user_id=user_id,
            options=request.options
        )
        
        # Record usage on success
        quota_manager.record_usage(user_id, tier)
        
        processing_time = (time.time() - start_time) * 1000
        
        return VerifyResponse(
            request_id=request_id,
            claim=request.claim,
            verdict=result.status.value,
            confidence=round(result.confidence_score, 4),
            summary=result.summary,
            explanation=result.explanation,
            source_count=len(result.traditional_sources) + len(result.extended_sources),
            warnings=result.warnings,
            processing_time_ms=round(processing_time, 2),
            cache_hit=result.cache_hit,
            timestamp=datetime.now().isoformat()
        )
        
    except RateLimitExceededError as e:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please try again later."
        )
    except Exception as e:
        logger.error(f"Verification error: {e}", request_id=request_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Verification failed: {str(e)}"
        )


@app.post("/api/v4/verify/detailed", tags=["Verification"])
async def verify_claim_detailed(request: VerifyRequest, req: Request):
    """
    Verify a claim with full detailed response.
    
    Returns complete information including:
    - All sources consulted
    - LLM analysis from multiple models
    - Supporting and contradicting evidence
    - Processing metadata
    """
    start_time = time.time()
    request_id = req.state.request_id
    
    try:
        verifier: EnhancedVerifier = app.state.verifier
        client_id = req.client.host if req.client else "unknown"
        
        result = await verifier.verify_claim(
            claim=request.claim,
            user_id=client_id,
            options=request.options
        )
        
        # Return full result
        return result.to_dict()
        
    except RateLimitExceededError:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded"
        )
    except Exception as e:
        logger.error(f"Verification error: {e}", request_id=request_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.post("/api/v4/batch", tags=["Verification"])
async def batch_verify(request: BatchVerifyRequest, req: Request, background_tasks: BackgroundTasks):
    """
    Verify multiple claims in a single request.
    
    Limited to 10 claims per request to prevent abuse.
    Claims are processed in parallel for efficiency.
    """
    request_id = req.state.request_id
    start_time = time.time()
    
    try:
        verifier: EnhancedVerifier = app.state.verifier
        client_id = req.client.host if req.client else "unknown"
        
        # Process claims in parallel
        tasks = [
            verifier.verify_claim(claim, user_id=client_id, options=request.options)
            for claim in request.claims
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Format results
        formatted = []
        for claim, result in zip(request.claims, results):
            if isinstance(result, Exception):
                formatted.append({
                    "claim": claim,
                    "error": str(result),
                    "verdict": None
                })
            else:
                formatted.append({
                    "claim": claim,
                    "verdict": result.status.value,
                    "confidence": round(result.confidence_score, 4),
                    "summary": result.summary
                })
        
        processing_time = (time.time() - start_time) * 1000
        
        return {
            "request_id": request_id,
            "claims_processed": len(request.claims),
            "results": formatted,
            "processing_time_ms": round(processing_time, 2),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Batch verification error: {e}", request_id=request_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.get("/api/v4/providers", tags=["Info"])
async def list_providers():
    """List all available verification providers"""
    verifier: EnhancedVerifier = app.state.verifier
    health = await verifier.get_health_status()
    
    providers = {
        "traditional_apis": health["components"].get("traditional_apis", {}).get("available_providers", []),
        "llm_providers": health["components"].get("llm_gateway", {}).get("available_providers", []),
        "data_sources": health["components"].get("data_sources", {}).get("available_sources", [])
    }
    
    total = sum(len(v) for v in providers.values())
    
    return {
        "total_providers": total,
        "providers": providers
    }


# ============================================================
# ADVANCED ANALYSIS ENDPOINTS
# ============================================================

class NLPAnalysisRequest(BaseModel):
    """Request for NLP analysis"""
    claim: str = Field(..., min_length=5, max_length=10000)


class SimilarityRequest(BaseModel):
    """Request for similar claims search"""
    claim: str = Field(..., min_length=5, max_length=10000)
    limit: int = Field(10, ge=1, le=50)


class SourceCredibilityRequest(BaseModel):
    """Request for source credibility check"""
    domains: Optional[List[str]] = Field(None, min_length=1, max_length=50, alias="sources")
    sources: Optional[List[str]] = Field(None, min_length=1, max_length=50)
    
    @property
    def get_domains(self) -> List[str]:
        return self.domains or self.sources or []


class MonteCarloRequest(BaseModel):
    """Request for Monte Carlo confidence analysis"""
    claim: Optional[str] = Field(None, min_length=5)
    evidence: Optional[List[Dict[str, Any]]] = None
    evidence_scores: Optional[List[float]] = None
    
    @property
    def get_evidence(self) -> List[Dict[str, Any]]:
        if self.evidence:
            return self.evidence
        if self.evidence_scores:
            return [{"score": s, "source": f"source_{i}"} for i, s in enumerate(self.evidence_scores)]
        return []


class ComprehensiveAnalysisRequest(BaseModel):
    """Request for comprehensive claim analysis"""
    claim: str = Field(..., min_length=5, max_length=10000)
    evidence: Optional[List[Dict[str, Any]]] = None
    sources_used: Optional[List[str]] = None


@app.get("/api/v4/modules", tags=["Advanced Analysis"])
async def list_modules():
    """
    List all available analysis modules and their status.
    
    Shows which advanced capabilities are active.
    """
    integrator = get_modules_integrator()
    status = integrator.get_module_status()
    
    active = sum(1 for v in status.values() if v)
    
    return {
        "total_modules": len(status),
        "active_modules": active,
        "modules": status,
        "descriptions": {
            "advanced_nlp": "Fallacy, propaganda, and bias detection",
            "claim_similarity": "Find similar fact-checked claims",
            "monte_carlo": "Probabilistic confidence intervals",
            "source_database": "Source credibility ratings",
            "consensus_engine": "Multi-source voting aggregation",
            "evidence_graph": "Knowledge graph analysis",
            "numerical_verification": "Statistics and numbers validation",
            "temporal_reasoning": "Time-based claim verification",
            "geospatial_reasoning": "Location-based verification",
            "social_media": "Viral claim tracking",
            "adaptive_learning": "Self-improving AI"
        }
    }


@app.post("/api/v4/analyze/nlp", tags=["Advanced Analysis"])
async def analyze_nlp(request: NLPAnalysisRequest, req: Request):
    """
    Perform advanced NLP analysis on a claim.
    
    **Requires Pro tier or higher.**
    
    Detects:
    - **Logical fallacies** (ad hominem, strawman, etc.)
    - **Propaganda techniques** (fear mongering, loaded language, etc.)
    - **Bias indicators** (political, emotional, sensational)
    - **Named entities** (people, organizations, locations, numbers)
    - **Sentiment and subjectivity scores**
    - **Verifiability assessment**
    
    This is useful for understanding the rhetorical structure of a claim
    before fact-checking it.
    """
    # Check feature access
    user_id, tier = get_user_tier(req)
    if not check_feature_access(tier, "nlp_analysis"):
        raise HTTPException(
            status_code=403,
            detail={
                "error": "feature_not_available",
                "message": "NLP analysis requires Pro tier or higher",
                "current_tier": tier,
                "required_tier": "pro",
                "upgrade_url": "/pricing.html"
            }
        )
    
    integrator = get_modules_integrator()
    
    result = integrator.analyze_nlp(request.claim)
    
    if result is None:
        raise HTTPException(
            status_code=503,
            detail="NLP analysis module not available"
        )
    
    return {
        "claim": request.claim,
        "analysis": result,
        "timestamp": datetime.now().isoformat()
    }


@app.post("/api/v4/analyze/similar", tags=["Advanced Analysis"])
async def find_similar_claims(request: SimilarityRequest):
    """
    Find similar claims that have been previously fact-checked.
    
    Uses TF-IDF and semantic similarity to find related claims.
    This helps avoid redundant fact-checking and leverage existing work.
    
    Returns:
    - Similar claim text
    - Similarity score (0-1)
    - Previous verdict (if available)
    - Source of original fact-check
    """
    integrator = get_modules_integrator()
    
    results = integrator.find_similar_claims(request.claim, limit=request.limit)
    
    if not results and not integrator._module_status.get("claim_similarity"):
        raise HTTPException(
            status_code=503,
            detail="Claim similarity module not available"
        )
    
    return {
        "claim": request.claim,
        "similar_claims": results,
        "count": len(results),
        "timestamp": datetime.now().isoformat()
    }


@app.post("/api/v4/analyze/sources", tags=["Advanced Analysis"])
async def check_source_credibility(request: SourceCredibilityRequest, req: Request):
    """
    Check the credibility of news sources and websites.
    
    **Requires Pro tier or higher.**
    
    Database includes ratings for:
    - Major news organizations
    - Scientific journals
    - Government sources
    - Known misinformation sources
    
    Returns:
    - Credibility score (0-100)
    - Factual reporting rating
    - Political bias rating
    - Credibility tier (1-5)
    """
    # Check feature access
    user_id, tier = get_user_tier(req)
    if not check_feature_access(tier, "source_credibility"):
        raise HTTPException(
            status_code=403,
            detail={
                "error": "feature_not_available",
                "message": "Source credibility requires Pro tier or higher",
                "current_tier": tier,
                "required_tier": "pro",
                "upgrade_url": "/pricing.html"
            }
        )
    
    integrator = get_modules_integrator()
    
    domains = request.get_domains
    if not domains:
        raise HTTPException(status_code=400, detail="Must provide 'sources' or 'domains' field")
    
    results = integrator.get_batch_source_credibility(domains)
    
    if not results and not integrator._module_status.get("source_database"):
        raise HTTPException(
            status_code=503,
            detail="Source credibility module not available"
        )
    
    return {
        "sources_requested": len(domains),
        "sources_found": len(results),
        "results": results,
        "not_found": [d for d in domains if d not in results],
        "timestamp": datetime.now().isoformat()
    }


@app.post("/api/v4/analyze/confidence", tags=["Advanced Analysis"])
async def monte_carlo_confidence(request: MonteCarloRequest, req: Request):
    """
    Calculate probabilistic confidence using Monte Carlo simulation.
    
    **Requires Team tier or higher.**
    
    Provide evidence from multiple sources, each with:
    - source_name: Name of the source
    - verdict: 'true', 'false', 'mixed', or 'unknown'
    - confidence: How confident the source is (0-1)
    - credibility: How credible the source is (0-1)
    
    Or simply provide evidence_scores as a list of floats.
    
    Returns:
    - Final verdict with probability
    - 95% confidence interval
    - Probability distribution across verdicts
    - Convergence score
    """
    # Check feature access
    user_id, tier = get_user_tier(req)
    if not check_feature_access(tier, "monte_carlo"):
        raise HTTPException(
            status_code=403,
            detail={
                "error": "feature_not_available",
                "message": "Monte Carlo confidence requires Team tier or higher",
                "current_tier": tier,
                "required_tier": "team",
                "upgrade_url": "/pricing.html"
            }
        )
    
    integrator = get_modules_integrator()
    
    evidence = request.get_evidence
    if not evidence:
        raise HTTPException(status_code=400, detail="Must provide 'evidence' or 'evidence_scores' field")
    
    result = integrator.calculate_monte_carlo_confidence(evidence)
    
    if result is None:
        raise HTTPException(
            status_code=503,
            detail="Monte Carlo module not available"
        )
    
    return {
        "evidence_count": len(evidence),
        "result": result,
        "timestamp": datetime.now().isoformat()
    }


@app.post("/api/v4/analyze/numerical", tags=["Advanced Analysis"])
async def analyze_numerical_claims(request: NLPAnalysisRequest):
    """
    Analyze numerical claims and statistics in text.
    
    Detects and validates:
    - Percentages
    - Statistics
    - Comparisons
    - Growth rates
    - Financial figures
    """
    integrator = get_modules_integrator()
    
    result = integrator.analyze_numerical_claims(request.claim)
    
    if result is None:
        raise HTTPException(
            status_code=503,
            detail="Numerical verification module not available"
        )
    
    return {
        "claim": request.claim,
        "analysis": result,
        "timestamp": datetime.now().isoformat()
    }


@app.post("/api/v4/analyze/temporal", tags=["Advanced Analysis"])
async def analyze_temporal_claims(request: NLPAnalysisRequest):
    """
    Analyze time-based claims in text.
    
    Detects:
    - Date references
    - Time periods
    - Historical sequences
    - Anachronisms
    """
    integrator = get_modules_integrator()
    
    result = integrator.analyze_temporal_claims(request.claim)
    
    if result is None:
        raise HTTPException(
            status_code=503,
            detail="Temporal reasoning module not available"
        )
    
    return {
        "claim": request.claim,
        "analysis": result,
        "timestamp": datetime.now().isoformat()
    }


@app.post("/api/v4/analyze/geospatial", tags=["Advanced Analysis"])
async def analyze_geospatial_claims(request: NLPAnalysisRequest):
    """
    Analyze location-based claims in text.
    
    Detects:
    - Place names
    - Geographic relationships
    - Distance claims
    - Location inconsistencies
    """
    integrator = get_modules_integrator()
    
    result = integrator.analyze_geospatial_claims(request.claim)
    
    if result is None:
        raise HTTPException(
            status_code=503,
            detail="Geospatial reasoning module not available"
        )
    
    return {
        "claim": request.claim,
        "analysis": result,
        "timestamp": datetime.now().isoformat()
    }


@app.post("/api/v4/analyze/comprehensive", tags=["Advanced Analysis"])
async def comprehensive_analysis(request: ComprehensiveAnalysisRequest):
    """
    Perform COMPREHENSIVE analysis using ALL available modules.
    
    This is the ultimate analysis endpoint that combines:
    - NLP analysis (fallacies, propaganda, bias)
    - Similar claims search
    - Monte Carlo confidence (if evidence provided)
    - Source credibility (if sources provided)
    - Numerical verification
    - Temporal reasoning
    - Geospatial analysis
    
    Use this for deep investigation of complex claims.
    """
    integrator = get_modules_integrator()
    
    result = await integrator.analyze_complete(
        claim=request.claim,
        evidence=request.evidence,
        sources_used=request.sources_used
    )
    
    return result.to_dict()


# ============================================================
# V3 COMPATIBILITY ENDPOINTS
# ============================================================
# These endpoints maintain backwards compatibility with the frontend

class V3VerifyRequest(BaseModel):
    """V3 API verification request"""
    claim: str = Field(..., min_length=5, max_length=10000)
    check_type: Optional[str] = Field("comprehensive", description="Type of check: quick, standard, comprehensive")


@app.post("/v3/verify", tags=["V3 Compatibility"])
async def v3_verify(request: V3VerifyRequest, req: Request):
    """
    V3-compatible verification endpoint.
    
    Provides backwards compatibility with older frontend versions.
    """
    try:
        verifier: EnhancedVerifier = app.state.verifier
        client_id = req.client.host if req.client else "unknown"
        
        result = await verifier.verify_claim(
            claim=request.claim,
            user_id=client_id,
            options={"check_type": request.check_type}
        )
        
        # Format in V3 style
        return {
            "success": True,
            "claim": request.claim,
            "result": {
                "verdict": result.status.value,
                "confidence": round(result.confidence_score, 4),
                "summary": result.summary,
                "explanation": result.explanation
            },
            "sources": {
                "count": len(result.traditional_sources) + len(result.extended_sources),
                "providers": result.providers_used
            },
            "warnings": result.warnings,
            "cached": result.cache_hit,
            "timestamp": datetime.now().isoformat()
        }
    except RateLimitExceededError:
        return {"success": False, "error": "Rate limit exceeded"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/v3/quick-check", tags=["V3 Compatibility"])
async def v3_quick_check(request: V3VerifyRequest, req: Request):
    """Quick check endpoint for V3 compatibility"""
    request.check_type = "quick"
    return await v3_verify(request, req)


@app.post("/v3/verify/batch", tags=["V3 Compatibility"])
async def v3_batch_verify(claims: List[str], req: Request):
    """Batch verification for V3 compatibility"""
    results = []
    for claim in claims[:10]:  # Limit to 10
        try:
            v3_req = V3VerifyRequest(claim=claim)
            result = await v3_verify(v3_req, req)
            results.append(result)
        except Exception as e:
            results.append({"success": False, "claim": claim, "error": str(e)})
    
    return {
        "success": True,
        "count": len(results),
        "results": results,
        "timestamp": datetime.now().isoformat()
    }


@app.get("/v3/providers", tags=["V3 Compatibility"])
async def v3_list_providers():
    """List providers for V3 compatibility"""
    return await list_providers()


# ============================================================
# STRIPE SUBSCRIPTION ENDPOINTS
# ============================================================

# Stripe Price IDs - configure in environment or Stripe dashboard
STRIPE_PRICE_IDS = {
    "pro_monthly": os.getenv("STRIPE_PRO_MONTHLY_PRICE_ID", "price_pro_monthly"),
    "pro_annual": os.getenv("STRIPE_PRO_ANNUAL_PRICE_ID", "price_pro_annual"),
    "team_monthly": os.getenv("STRIPE_TEAM_MONTHLY_PRICE_ID", "price_team_monthly"),
    "team_annual": os.getenv("STRIPE_TEAM_ANNUAL_PRICE_ID", "price_team_annual"),
    "enterprise_monthly": os.getenv("STRIPE_ENTERPRISE_MONTHLY_PRICE_ID", "price_enterprise_monthly"),
    "enterprise_annual": os.getenv("STRIPE_ENTERPRISE_ANNUAL_PRICE_ID", "price_enterprise_annual"),
}


class CreateCheckoutRequest(BaseModel):
    """Checkout session request"""
    plan: str = Field(..., description="Plan name: pro, team, enterprise")
    billing_cycle: str = Field(default="monthly", description="monthly or annual")
    email: Optional[str] = Field(None, description="Customer email")
    success_url: Optional[str] = Field(None, description="Redirect URL on success")
    cancel_url: Optional[str] = Field(None, description="Redirect URL on cancel")


class SubscriptionRequest(BaseModel):
    """Subscription management request"""
    subscription_id: str = Field(..., description="Stripe subscription ID")


@app.post("/api/v4/checkout", tags=["Subscription"])
async def create_checkout_session(
    request: CreateCheckoutRequest,
    req: Request
):
    """
    Create a Stripe checkout session for subscription.
    
    Returns a URL to redirect the user to Stripe checkout.
    """
    try:
        from stripe_handler import StripePaymentHandler
        
        # Determine price ID
        price_key = f"{request.plan}_{request.billing_cycle}"
        price_id = STRIPE_PRICE_IDS.get(price_key)
        
        if not price_id:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid plan/billing combination: {request.plan}/{request.billing_cycle}"
            )
        
        # Get user ID from headers or generate
        user_id, _ = get_user_tier(req)
        
        # Build URLs
        base_url = str(req.base_url).rstrip("/")
        success_url = request.success_url or f"{base_url}/dashboard.html?checkout=success"
        cancel_url = request.cancel_url or f"{base_url}/pricing.html?checkout=cancelled"
        
        # Create checkout session
        result = StripePaymentHandler.create_checkout_session(
            user_id=user_id,
            price_id=price_id,
            success_url=success_url,
            cancel_url=cancel_url,
            customer_email=request.email
        )
        
        return {
            "success": True,
            "checkout_url": result["url"],
            "session_id": result["session_id"]
        }
        
    except ImportError:
        # Stripe not configured - return mock for demo
        logger.warning("Stripe handler not available, returning demo checkout")
        return {
            "success": True,
            "checkout_url": f"/pricing.html?demo=true&plan={request.plan}",
            "session_id": f"demo_{request.plan}_{int(time.time())}",
            "demo_mode": True,
            "message": "Stripe not configured. Set STRIPE_SECRET_KEY to enable payments."
        }
    except Exception as e:
        logger.error(f"Checkout error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v4/subscription", tags=["Subscription"])
async def get_subscription(
    req: Request,
    subscription_id: Optional[str] = None
):
    """
    Get current subscription details.
    
    If no subscription_id provided, looks up by user.
    """
    try:
        from stripe_handler import StripePaymentHandler
        
        if not subscription_id:
            # In production, look up from database
            user_id, tier = get_user_tier(req)
            return {
                "success": True,
                "has_subscription": tier != "free",
                "tier": tier,
                "message": "Provide subscription_id for full details"
            }
        
        result = StripePaymentHandler.get_subscription(subscription_id)
        
        return {
            "success": True,
            "subscription": result
        }
        
    except ImportError:
        user_id, tier = get_user_tier(req)
        return {
            "success": True,
            "has_subscription": tier != "free",
            "tier": tier,
            "demo_mode": True
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v4/subscription/cancel", tags=["Subscription"])
async def cancel_subscription(
    request: SubscriptionRequest,
    req: Request
):
    """
    Cancel a subscription (at period end by default).
    """
    try:
        from stripe_handler import StripePaymentHandler
        
        result = StripePaymentHandler.cancel_subscription(
            request.subscription_id,
            at_period_end=True
        )
        
        return {
            "success": True,
            "subscription": result,
            "message": "Subscription will be cancelled at end of billing period"
        }
        
    except ImportError:
        return {
            "success": True,
            "demo_mode": True,
            "message": "Demo mode: Subscription would be cancelled"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v4/subscription/upgrade", tags=["Subscription"])
async def upgrade_subscription(
    request: CreateCheckoutRequest,
    req: Request,
    subscription_id: Optional[str] = None
):
    """
    Upgrade or change subscription plan.
    
    If no active subscription, creates a new checkout session.
    """
    try:
        from stripe_handler import StripePaymentHandler
        
        if not subscription_id:
            # Create new checkout session for upgrade
            return await create_checkout_session(request, req)
        
        # Update existing subscription
        price_key = f"{request.plan}_{request.billing_cycle}"
        price_id = STRIPE_PRICE_IDS.get(price_key)
        
        if not price_id:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid plan: {request.plan}"
            )
        
        result = StripePaymentHandler.update_subscription(
            subscription_id,
            price_id=price_id
        )
        
        return {
            "success": True,
            "subscription": result,
            "message": f"Upgraded to {request.plan} plan"
        }
        
    except ImportError:
        return {
            "success": True,
            "demo_mode": True,
            "message": f"Demo mode: Would upgrade to {request.plan}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v4/webhook/stripe", tags=["Subscription"])
async def stripe_webhook(req: Request):
    """
    Handle Stripe webhooks for subscription events.
    
    This endpoint should be registered in your Stripe dashboard.
    """
    try:
        from stripe_handler import StripePaymentHandler
        
        # Get raw body and signature
        body = await req.body()
        signature = req.headers.get("stripe-signature", "")
        
        # Process webhook
        event = StripePaymentHandler.handle_webhook(body.decode(), signature)
        
        # Handle different event types
        event_type = event.get("event_type")
        
        if event_type == "subscription_created":
            # Update user's tier in database
            logger.info(f"New subscription: {event.get('subscription_id')}")
            # TODO: Update user tier in database
            
        elif event_type == "subscription_deleted":
            # Downgrade user to free tier
            logger.info(f"Subscription cancelled: {event.get('subscription_id')}")
            # TODO: Reset user to free tier
            
        elif event_type == "payment_failed":
            # Handle failed payment (send email, etc.)
            logger.warning(f"Payment failed for: {event.get('customer_id')}")
            
        return {"success": True, "event": event_type}
        
    except ImportError:
        return {"success": True, "demo_mode": True, "message": "Webhook received (demo mode)"}
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================
# ERROR HANDLERS
# ============================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.detail,
            "status_code": exc.status_code,
            "request_id": getattr(request.state, "request_id", "unknown")
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "message": "Internal server error",
            "request_id": getattr(request.state, "request_id", "unknown")
        }
    )


# ============================================================
# MAIN
# ============================================================

def run():
    """Run the server"""
    uvicorn.run(
        "api_server_v4:app",
        host=config.HOST,
        port=config.PORT,
        reload=config.DEBUG,
        log_level="info"
    )


if __name__ == "__main__":
    run()
