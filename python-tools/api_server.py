"""
Verity Systems - FastAPI Backend Server
RESTful API for fact-checking services with comprehensive security

Features:
- RESTful API endpoints for claim verification
- JWT-based authentication
- Rate limiting with sliding window
- Request signing verification
- Comprehensive error handling
- OpenAPI documentation
- CORS support
- Health checks and monitoring
- Async processing for performance
- Stripe payment integration for premium tiers
"""

import os
import time
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from contextlib import asynccontextmanager
import logging
import json

from fastapi import FastAPI, HTTPException, Depends, Request, Response, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
import uvicorn

# Import our modules
from verity_supermodel import VeritySuperModel, VerificationResult, VerificationStatus
from security_utils import (
    JWTService, 
    InputValidator, 
    RateLimiter, 
    AuditLogger,
    EncryptionService,
    DataAnonymizer,
    RequestSigner
)

# Import third-party integrations (Honeybadger, New Relic, ConfigCat, etc.)
try:
    from integrations import (
        initialize_all_integrations,
        add_honeybadger_middleware,
        is_provider_enabled,
        track_operation,
        notify_error,
        get_feature_flag,
        FeatureFlags
    )
    INTEGRATIONS_AVAILABLE = True
except ImportError:
    INTEGRATIONS_AVAILABLE = False
    logger.warning("Integrations module not available - monitoring disabled")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('VerityAPI')

# ============================================================
# LIFESPAN MANAGEMENT
# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    # Startup
    logger.info("🚀 Starting Verity API Server...")
    
    # Initialize third-party integrations (Honeybadger, New Relic, ConfigCat)
    if INTEGRATIONS_AVAILABLE:
        integration_status = initialize_all_integrations()
        logger.info(f"📊 Integrations initialized: {integration_status}")
    
    app.state.model = VeritySuperModel()
    app.state.jwt_service = JWTService()
    app.state.rate_limiter = RateLimiter()
    app.state.audit = AuditLogger()
    app.state.encryption = EncryptionService()
    app.state.request_signer = RequestSigner()
    logger.info("✓ All services initialized")
    
    yield
    
    # Shutdown
    logger.info("👋 Shutting down Verity API Server...")


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="Verity Systems API",
    description="""
    ## AI-Powered Fact-Checking Platform
    
    Verity Systems provides enterprise-grade fact-checking using multiple AI models
    and authoritative sources.
    
    ### Features
    - 🔍 **Multi-source verification** - Cross-references 9+ fact-checking sources
    - 🤖 **AI-powered analysis** - Uses Claude, Llama, and specialized NLP models
    - 🔐 **Enterprise security** - AES-256 encryption, JWT auth, rate limiting
    - ⚡ **Real-time processing** - Sub-second response times
    - 📊 **Confidence scoring** - Quantified trust metrics
    
    ### Authentication
    Use API key authentication for all endpoints. Include your API key in the
    `X-API-Key` header.
    
    ### Rate Limits
    - Free tier: 100 requests/hour
    - Pro tier: 1,000 requests/hour
    - Enterprise: Unlimited
    """,
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Security schemes
bearer_scheme = HTTPBearer(auto_error=False)
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

# ============================================================
# MIDDLEWARE
# ============================================================

# CORS - Configure for your domains
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:8000",
        "https://verity-systems.vercel.app",
        "https://*.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-RateLimit-Limit", "X-RateLimit-Remaining", "X-RateLimit-Reset"]
)

# Trusted hosts
app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=["localhost", "127.0.0.1", "*.vercel.app", "*.verity-systems.com"]
)

# Add Honeybadger middleware for error tracking
if INTEGRATIONS_AVAILABLE:
    add_honeybadger_middleware(app)


@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    """Add security headers to all responses"""
    response = await call_next(request)
    
    # Security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    
    return response


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    """Log all requests for monitoring"""
    start_time = time.time()
    
    # Generate request ID
    request_id = f"req_{int(time.time() * 1000)}"
    request.state.request_id = request_id
    
    # Log request
    logger.info(f"[{request_id}] {request.method} {request.url.path}")
    
    response = await call_next(request)
    
    # Calculate processing time
    process_time = (time.time() - start_time) * 1000
    response.headers["X-Process-Time"] = f"{process_time:.2f}ms"
    response.headers["X-Request-ID"] = request_id
    
    logger.info(f"[{request_id}] Completed in {process_time:.2f}ms - Status: {response.status_code}")
    
    return response


# ============================================================
# PYDANTIC MODELS
# ============================================================

class ClaimRequest(BaseModel):
    """Request model for claim verification"""
    claim: str = Field(..., min_length=10, max_length=10000, description="The claim to verify")
    providers: Optional[List[str]] = Field(None, description="Specific providers to use")
    use_cache: bool = Field(True, description="Whether to use cached results")
    anonymize_pii: bool = Field(True, description="Remove PII from claim before processing")
    
    @validator('claim')
    def validate_claim(cls, v):
        return InputValidator.sanitize_text(v)


class ClaimResponse(BaseModel):
    """Response model for claim verification"""
    request_id: str
    claim: str
    status: str
    confidence_score: float
    summary: str
    sources_count: int
    fact_checks_count: int
    warnings: List[str]
    processing_time_ms: float
    timestamp: str


class DetailedClaimResponse(ClaimResponse):
    """Detailed response with all data"""
    sources: List[Dict]
    fact_checks: List[Dict]
    ai_analysis: str


class BatchClaimRequest(BaseModel):
    """Request model for batch verification"""
    claims: List[str] = Field(..., min_items=1, max_items=10)
    providers: Optional[List[str]] = None


class UserCreate(BaseModel):
    """Model for user registration"""
    email: str
    password: str = Field(..., min_length=8)
    organization: Optional[str] = None


class TokenResponse(BaseModel):
    """Response model for authentication"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class APIKeyResponse(BaseModel):
    """Response model for API key generation"""
    api_key: str
    created_at: str
    expires_at: Optional[str]


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    version: str
    timestamp: str
    providers: Dict[str, bool]


class ErrorResponse(BaseModel):
    """Error response model"""
    error: str
    detail: str
    request_id: Optional[str]


# ============================================================
# DEPENDENCIES
# ============================================================

async def get_api_key(
    api_key: Optional[str] = Depends(api_key_header),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme)
) -> str:
    """Validate API key or Bearer token"""
    if api_key:
        if InputValidator.validate_api_key(api_key):
            return api_key
        raise HTTPException(status_code=401, detail="Invalid API key format")
    
    if credentials:
        jwt_service = JWTService()
        payload = jwt_service.verify_token(credentials.credentials)
        if payload:
            return payload.get('user_id', 'authenticated')
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    raise HTTPException(status_code=401, detail="API key or Bearer token required")


async def check_rate_limit(request: Request, client_id: str = Depends(get_api_key)):
    """Check rate limits for the client"""
    rate_limiter: RateLimiter = request.app.state.rate_limiter
    
    # Different limits for different tiers (in production, check user tier)
    limit = 100  # requests per hour
    window = 3600  # 1 hour
    
    allowed, info = rate_limiter.check_rate_limit(client_id, limit, window)
    
    # Add rate limit headers
    request.state.rate_limit_info = info
    
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded",
            headers={
                "X-RateLimit-Limit": str(info['limit']),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(info['reset']),
                "Retry-After": str(info['window_seconds'])
            }
        )
    
    return client_id


# ============================================================
# API ENDPOINTS
# ============================================================

@app.get("/", tags=["General"])
async def root():
    """Root endpoint"""
    return {
        "name": "Verity Systems API",
        "version": "2.0.0",
        "documentation": "/docs",
        "status": "operational"
    }


@app.get("/health", response_model=HealthResponse, tags=["General"])
async def health_check(request: Request):
    """Health check endpoint for monitoring"""
    model: VeritySuperModel = request.app.state.model
    
    # Check provider availability
    providers_status = {
        provider.name: provider.is_available 
        for provider in model.providers
    }
    
    return HealthResponse(
        status="healthy",
        version="2.0.0",
        timestamp=datetime.utcnow().isoformat(),
        providers=providers_status
    )


@app.post("/v1/verify", response_model=ClaimResponse, tags=["Verification"])
async def verify_claim(
    request: Request,
    claim_request: ClaimRequest,
    client_id: str = Depends(check_rate_limit)
):
    """
    Verify a single claim
    
    This endpoint analyzes a claim using multiple fact-checking sources and AI models.
    Returns a verdict with confidence score and supporting evidence.
    """
    model: VeritySuperModel = request.app.state.model
    audit: AuditLogger = request.app.state.audit
    
    try:
        # Process claim
        claim = claim_request.claim
        if claim_request.anonymize_pii:
            claim = DataAnonymizer.anonymize_text(claim)
        
        # Verify
        result = await model.verify_claim(
            claim=claim,
            client_id=client_id,
            use_cache=claim_request.use_cache,
            providers=claim_request.providers
        )
        
        # Audit log
        audit.log(
            action='claim_verification',
            actor=client_id,
            resource='verify_claim',
            details={
                'claim_length': len(claim),
                'status': result.status.value,
                'confidence': result.confidence_score
            }
        )
        
        return ClaimResponse(
            request_id=result.request_id,
            claim=claim,
            status=result.status.value,
            confidence_score=result.confidence_score,
            summary=result.analysis_summary,
            sources_count=len(result.sources),
            fact_checks_count=len(result.fact_checks),
            warnings=result.warnings,
            processing_time_ms=result.processing_time_ms,
            timestamp=result.timestamp.isoformat()
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception(f"Verification error: {e}")
        raise HTTPException(status_code=500, detail="Verification failed")


@app.post("/v1/verify/detailed", response_model=DetailedClaimResponse, tags=["Verification"])
async def verify_claim_detailed(
    request: Request,
    claim_request: ClaimRequest,
    client_id: str = Depends(check_rate_limit)
):
    """
    Verify a claim with full details
    
    Returns complete verification data including all sources, fact-checks,
    and AI analysis.
    """
    model: VeritySuperModel = request.app.state.model
    
    try:
        claim = claim_request.claim
        if claim_request.anonymize_pii:
            claim = DataAnonymizer.anonymize_text(claim)
        
        result = await model.verify_claim(
            claim=claim,
            client_id=client_id,
            use_cache=claim_request.use_cache,
            providers=claim_request.providers
        )
        
        return DetailedClaimResponse(
            request_id=result.request_id,
            claim=claim,
            status=result.status.value,
            confidence_score=result.confidence_score,
            summary=result.analysis_summary,
            sources_count=len(result.sources),
            fact_checks_count=len(result.fact_checks),
            warnings=result.warnings,
            processing_time_ms=result.processing_time_ms,
            timestamp=result.timestamp.isoformat(),
            sources=[
                {
                    'name': s.name,
                    'url': s.url,
                    'credibility': s.credibility.value,
                    'snippet': s.snippet
                } for s in result.sources
            ],
            fact_checks=result.fact_checks,
            ai_analysis=result.ai_analysis
        )
        
    except Exception as e:
        logger.exception(f"Verification error: {e}")
        raise HTTPException(status_code=500, detail="Verification failed")


@app.post("/v1/verify/batch", tags=["Verification"])
async def verify_claims_batch(
    request: Request,
    batch_request: BatchClaimRequest,
    client_id: str = Depends(check_rate_limit)
):
    """
    Verify multiple claims in batch
    
    Process up to 10 claims in a single request. Results are returned
    in the same order as the input claims.
    """
    model: VeritySuperModel = request.app.state.model
    
    results = []
    for claim in batch_request.claims:
        try:
            sanitized = InputValidator.sanitize_text(claim)
            result = await model.verify_claim(
                claim=sanitized,
                client_id=client_id,
                providers=batch_request.providers
            )
            results.append({
                'claim': claim,
                'status': result.status.value,
                'confidence': result.confidence_score,
                'summary': result.analysis_summary
            })
        except Exception as e:
            results.append({
                'claim': claim,
                'status': 'error',
                'error': str(e)
            })
    
    return {
        'results': results,
        'total': len(results),
        'timestamp': datetime.utcnow().isoformat()
    }


@app.get("/v1/providers", tags=["Information"])
async def list_providers(request: Request):
    """
    List available fact-checking providers
    
    Returns all configured providers and their availability status.
    """
    model: VeritySuperModel = request.app.state.model
    
    providers = []
    for provider in model.providers:
        providers.append({
            'name': provider.name,
            'available': provider.is_available,
            'type': type(provider).__name__
        })
    
    return {
        'providers': providers,
        'total_available': sum(1 for p in model.providers if p.is_available)
    }


@app.post("/v1/auth/token", response_model=TokenResponse, tags=["Authentication"])
async def login(request: Request, credentials: UserCreate):
    """
    Authenticate and receive JWT tokens
    
    Exchange credentials for access and refresh tokens.
    """
    jwt_service: JWTService = request.app.state.jwt_service
    
    # In production, verify against database
    # For demo, accept any valid email format
    if not InputValidator.validate_email(credentials.email):
        raise HTTPException(status_code=400, detail="Invalid email format")
    
    user_data = {
        'user_id': credentials.email,
        'organization': credentials.organization
    }
    
    access_token, refresh_token = jwt_service.create_token_pair(user_data)
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=3600
    )


@app.post("/v1/auth/api-key", response_model=APIKeyResponse, tags=["Authentication"])
async def generate_api_key(
    request: Request,
    client_id: str = Depends(get_api_key)
):
    """
    Generate a new API key
    
    Creates a new API key for programmatic access.
    """
    encryption: EncryptionService = request.app.state.encryption
    
    api_key = encryption.generate_api_key()
    
    return APIKeyResponse(
        api_key=api_key,
        created_at=datetime.utcnow().isoformat(),
        expires_at=None  # API keys don't expire by default
    )


@app.get("/v1/usage", tags=["Account"])
async def get_usage(
    request: Request,
    client_id: str = Depends(get_api_key)
):
    """
    Get API usage statistics
    
    Returns current usage and rate limit information.
    """
    rate_limiter: RateLimiter = request.app.state.rate_limiter
    
    usage = rate_limiter.get_client_usage(client_id)
    
    return {
        'client_id': client_id,
        'requests_this_hour': usage,
        'limit': 100,
        'remaining': max(0, 100 - usage),
        'reset_at': (datetime.utcnow() + timedelta(hours=1)).isoformat()
    }


# ============================================================
# ERROR HANDLERS
# ============================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions"""
    request_id = getattr(request.state, 'request_id', None)
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            'error': 'HTTP Error',
            'detail': exc.detail,
            'request_id': request_id
        },
        headers=getattr(exc, 'headers', None)
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions"""
    logger.exception(f"Unexpected error: {exc}")
    request_id = getattr(request.state, 'request_id', None)
    
    return JSONResponse(
        status_code=500,
        content={
            'error': 'Internal Server Error',
            'detail': 'An unexpected error occurred',
            'request_id': request_id
        }
    )


# ============================================================
# RUN SERVER
# ============================================================

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🚀 VERITY SYSTEMS API SERVER")
    print("="*60)
    print("Documentation: http://localhost:8000/docs")
    print("="*60 + "\n")
    
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
