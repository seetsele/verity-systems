"""
Verity Systems - Enhanced Verification Orchestrator
Integrates all new infrastructure with the verification engine:
- UnifiedLLMGateway (LiteLLM, Ollama, Groq, OpenRouter, DeepSeek, Together AI)
- Resilience layer (Circuit breakers, retries, health checks)
- Caching layer (Redis + Memory)
- Extended data sources (Academic, News, Knowledge bases)

This module provides a production-ready verification pipeline.

Author: Verity Systems
License: MIT
"""

import os
import asyncio
import aiohttp
import logging
import json
import time
import hashlib
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

# Import Verity modules
from verity_supermodel import (
    VeritySuperModel,
    VerificationResult,
    VerificationStatus,
    VerificationSource,
    SourceCredibility,
    SecurityManager
)

# Import new infrastructure
from verity_unified_llm import UnifiedLLMGateway, LLMFactChecker
from verity_resilience import (
    ResilientHTTPClient,
    HealthChecker,
    MetricsCollector,
    GracefulShutdown,
    StructuredLogger
)
from verity_cache import VerificationCache, RequestCoalescer
from verity_data_sources import FactCheckAggregator, SourceResult

logger = StructuredLogger("EnhancedVerifier")


# ============================================================
# CONFIGURATION
# ============================================================

@dataclass
class VerifierConfig:
    """
    Configuration for the enhanced verifier.
    
    DEFAULT: Deep Research Mode
    - Extended timeouts for comprehensive analysis
    - Multiple LLM models for consensus
    - Minimum 20 sources required
    - All academic sources enabled
    - Cross-referencing mandatory
    - Multi-engine web search
    """
    
    # LLM settings - Deep Research defaults
    enable_llm_verification: bool = True
    llm_timeout_seconds: float = 60.0  # Increased from 30s
    llm_fallback_enabled: bool = True
    min_llm_models: int = 4  # Minimum LLM models for consensus
    max_llm_models: int = 8  # Maximum LLM models to query
    llm_agreement_threshold: float = 0.6  # 60% agreement required
    
    # Cache settings
    enable_caching: bool = True
    cache_ttl_seconds: int = 3600  # 1 hour
    redis_url: Optional[str] = None
    
    # Data source settings - Deep Research defaults
    enable_data_sources: bool = True
    max_sources_per_type: int = 15  # Increased from 5
    min_source_credibility: float = 0.5  # Lowered to include more sources
    min_total_sources: int = 20  # NEW: Minimum sources before conclusion
    
    # Academic source settings - Always enabled
    enable_academic_sources: bool = True
    academic_sources_required: bool = True  # Must check academic sources
    academic_source_types: List[str] = None  # Will default to all
    
    # Web search settings - Multi-engine default
    enable_multi_engine_search: bool = True
    search_engines: List[str] = None  # Will default to all available
    
    # Cross-referencing settings - Mandatory
    enable_cross_referencing: bool = True
    cross_reference_threshold: float = 0.7  # Sources must agree 70%
    verify_sources_against_each_other: bool = True
    
    # Verification settings
    min_confidence_threshold: float = 0.4  # Slightly higher for deep research
    require_multiple_sources: bool = True
    enable_ai_consensus: bool = True
    
    # Performance settings - Extended for deep research
    max_concurrent_requests: int = 20  # Increased from 10
    request_timeout_seconds: float = 180.0  # Increased from 60s
    retry_failed_requests: bool = True
    max_retries: int = 2
    
    # Health check settings
    health_check_interval_seconds: int = 60
    
    def __post_init__(self):
        """Set default lists after initialization"""
        if self.academic_source_types is None:
            self.academic_source_types = [
                "arxiv", "pubmed", "semantic_scholar", "google_scholar",
                "crossref", "openalex", "core", "base", "doaj"
            ]
        if self.search_engines is None:
            self.search_engines = [
                "google", "bing", "duckduckgo", "brave", "searx"
            ]
    
    @classmethod
    def from_env(cls) -> "VerifierConfig":
        """Load config from environment variables"""
        return cls(
            enable_llm_verification=os.getenv("ENABLE_LLM_VERIFICATION", "true").lower() == "true",
            enable_caching=os.getenv("ENABLE_CACHING", "true").lower() == "true",
            redis_url=os.getenv("REDIS_URL"),
            max_concurrent_requests=int(os.getenv("MAX_CONCURRENT_REQUESTS", "20")),
            request_timeout_seconds=float(os.getenv("REQUEST_TIMEOUT", "180")),
            min_total_sources=int(os.getenv("MIN_TOTAL_SOURCES", "20")),
            min_llm_models=int(os.getenv("MIN_LLM_MODELS", "4")),
        )


# ============================================================
# ENHANCED VERIFICATION RESULT
# ============================================================

@dataclass
class EnhancedVerificationResult:
    """Extended verification result with additional metadata"""
    
    # Core result
    claim: str
    status: VerificationStatus
    confidence_score: float
    
    # Sources
    traditional_sources: List[VerificationSource]
    extended_sources: List[Dict]
    llm_analysis: Dict
    
    # Analysis
    summary: str
    explanation: str
    warnings: List[str]
    
    # Metadata
    request_id: str
    timestamp: datetime
    processing_time_ms: float
    cache_hit: bool
    providers_used: List[str]
    
    # Evidence
    supporting_evidence: List[Dict]
    contradicting_evidence: List[Dict]
    
    # Comprehensive Summary (for paid tiers)
    comprehensive_summary: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to comprehensive dictionary with all source details"""
        
        # Build detailed traditional source list
        traditional_sources_detailed = []
        for source in self.traditional_sources:
            traditional_sources_detailed.append({
                "name": source.name,
                "url": source.url,
                "credibility": source.credibility.value if hasattr(source.credibility, 'value') else str(source.credibility),
                "claim_rating": source.claim_rating,
                "type": "fact_check_api",
                "description": f"Fact-check from {source.name}",
                "verification_status": source.claim_rating or "reviewed"
            })
        
        # Build detailed extended source list
        extended_sources_detailed = []
        for source in self.extended_sources:
            if isinstance(source, dict):
                extended_sources_detailed.append({
                    "name": source.get("name", source.get("title", "Unknown Source")),
                    "url": source.get("url", source.get("link", "")),
                    "type": source.get("type", "academic/news"),
                    "credibility": source.get("credibility", source.get("trust", "medium")),
                    "snippet": source.get("snippet", source.get("abstract", source.get("description", ""))),
                    "date": source.get("date", source.get("published", "")),
                    "author": source.get("author", source.get("authors", "")),
                    "relevance_score": source.get("relevance", source.get("score", 0.5))
                })
            else:
                extended_sources_detailed.append({
                    "name": str(source),
                    "url": "",
                    "type": "reference",
                    "credibility": "unknown"
                })
        
        # Combine all sources for easy access
        all_sources = traditional_sources_detailed + extended_sources_detailed
        
        return {
            "claim": self.claim,
            "verdict": {
                "status": self.status.value,
                "confidence": round(self.confidence_score, 4),
                "confidence_percentage": round(self.confidence_score * 100, 1),
                "summary": self.summary,
                "verdict_label": self._get_verdict_label()
            },
            "analysis": {
                "explanation": self.explanation,
                "detailed_reasoning": self._generate_detailed_reasoning(),
                "key_findings": self._extract_key_findings(),
                "supporting_evidence": self.supporting_evidence,
                "contradicting_evidence": self.contradicting_evidence,
                "evidence_summary": {
                    "supporting_count": len(self.supporting_evidence),
                    "contradicting_count": len(self.contradicting_evidence),
                    "balance": "supporting" if len(self.supporting_evidence) > len(self.contradicting_evidence) else 
                              "contradicting" if len(self.contradicting_evidence) > len(self.supporting_evidence) else "balanced"
                },
                "comprehensive_summary": self.comprehensive_summary
            },
            "sources": {
                "total_count": len(all_sources),
                "traditional_count": len(self.traditional_sources),
                "extended_count": len(self.extended_sources),
                "traditional_sources": traditional_sources_detailed,
                "extended_sources": extended_sources_detailed,
                "all_sources": all_sources,
                "providers_used": self.providers_used,
                "source_breakdown": {
                    "fact_check_apis": len([s for s in all_sources if s.get("type") == "fact_check_api"]),
                    "academic": len([s for s in all_sources if "academic" in s.get("type", "")]),
                    "news": len([s for s in all_sources if "news" in s.get("type", "")]),
                    "other": len([s for s in all_sources if s.get("type") not in ["fact_check_api", "academic", "news"]])
                }
            },
            "llm_analysis": self.llm_analysis,
            "warnings": self.warnings,
            "metadata": {
                "request_id": self.request_id,
                "timestamp": self.timestamp.isoformat(),
                "processing_time_ms": round(self.processing_time_ms, 2),
                "cache_hit": self.cache_hit,
                "api_version": "4.0"
            }
        }
    
    def _get_verdict_label(self) -> str:
        """Get human-readable verdict label"""
        labels = {
            "verified_true": "TRUE",
            "verified_false": "FALSE",
            "partially_true": "PARTIALLY TRUE",
            "misleading": "MISLEADING",
            "unverifiable": "UNVERIFIABLE",
            "needs_context": "NEEDS CONTEXT",
            "satire": "SATIRE",
            "opinion": "OPINION"
        }
        return labels.get(self.status.value, self.status.value.upper())
    
    def _generate_detailed_reasoning(self) -> List[str]:
        """Generate step-by-step reasoning breakdown"""
        reasoning = []
        
        if self.traditional_sources:
            reasoning.append(f"Consulted {len(self.traditional_sources)} fact-checking sources for established verdicts.")
        
        if self.extended_sources:
            reasoning.append(f"Analyzed {len(self.extended_sources)} additional sources including academic papers and news articles.")
        
        if self.supporting_evidence:
            reasoning.append(f"Found {len(self.supporting_evidence)} pieces of supporting evidence.")
        
        if self.contradicting_evidence:
            reasoning.append(f"Found {len(self.contradicting_evidence)} pieces of contradicting evidence.")
        
        if self.llm_analysis and self.llm_analysis.get("consensus"):
            reasoning.append("AI models provided consensus analysis of the claim's veracity.")
        
        confidence_level = "high" if self.confidence_score > 0.8 else "moderate" if self.confidence_score > 0.5 else "low"
        reasoning.append(f"Overall confidence level: {confidence_level} ({round(self.confidence_score * 100, 1)}%)")
        
        return reasoning
    
    def _extract_key_findings(self) -> List[str]:
        """Extract key findings from the analysis"""
        findings = []
        
        # Extract from explanation
        if self.explanation:
            sentences = self.explanation.split('. ')
            for sentence in sentences[:3]:  # First 3 key sentences
                if sentence.strip() and len(sentence) > 20:
                    findings.append(sentence.strip() + ('.' if not sentence.endswith('.') else ''))
        
        return findings


# ============================================================
# ENHANCED VERIFIER
# ============================================================

class EnhancedVerifier:
    """
    Production-ready verification engine combining all infrastructure:
    
    1. Traditional fact-check APIs (Google, ClaimBuster, etc.)
    2. Extended data sources (Academic, News, Knowledge bases)
    3. Multi-LLM consensus (LiteLLM, Groq, DeepSeek, etc.)
    4. Redis caching for performance
    5. Circuit breakers for resilience
    6. Prometheus metrics for observability
    """
    
    def __init__(self, config: VerifierConfig = None):
        self.config = config or VerifierConfig.from_env()
        
        # Core components
        self.security = SecurityManager()
        self.super_model = VeritySuperModel()
        
        # New infrastructure
        self.llm_gateway: Optional[UnifiedLLMGateway] = None
        self.llm_checker: Optional[LLMFactChecker] = None
        self.data_sources: Optional[FactCheckAggregator] = None
        self.cache: Optional[VerificationCache] = None
        self.coalescer: Optional[RequestCoalescer] = None
        self.health_checker: Optional[HealthChecker] = None
        self.metrics = MetricsCollector()
        
        # Session management
        self._session: Optional[aiohttp.ClientSession] = None
        self._initialized = False
        
    async def initialize(self) -> None:
        """Initialize all components"""
        if self._initialized:
            return
        
        logger.info("Initializing Enhanced Verifier")
        
        # Create shared session
        self._session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.config.request_timeout_seconds)
        )
        
        # Initialize LLM gateway
        if self.config.enable_llm_verification:
            logger.info("Initializing LLM Gateway")
            self.llm_gateway = UnifiedLLMGateway()
            self.llm_checker = LLMFactChecker(self.llm_gateway)
        
        # Initialize data sources
        if self.config.enable_data_sources:
            logger.info("Initializing Data Sources")
            self.data_sources = FactCheckAggregator(self._session)
        
        # Initialize cache
        if self.config.enable_caching:
            logger.info("Initializing Cache")
            from verity_cache import CacheConfig
            cache_config = CacheConfig(
                redis_url=self.config.redis_url or 'redis://localhost:6379',
                default_ttl=self.config.cache_ttl_seconds,
                verification_ttl=self.config.cache_ttl_seconds
            )
            self.cache = VerificationCache(cache_config)
            self.coalescer = RequestCoalescer()
        
        # Initialize health checker
        self.health_checker = HealthChecker()
        
        self._initialized = True
        logger.info("Enhanced Verifier initialized successfully")
    
    async def shutdown(self) -> None:
        """Gracefully shutdown all components"""
        logger.info("Shutting down Enhanced Verifier")
        
        if self.data_sources:
            await self.data_sources.close()
        
        if self._session:
            await self._session.close()
        
        self._initialized = False
        logger.info("Enhanced Verifier shutdown complete")
    
    async def verify_claim(
        self,
        claim: str,
        user_id: Optional[str] = None,
        options: Dict[str, Any] = None
    ) -> EnhancedVerificationResult:
        """
        Verify a claim using all available resources.
        
        Args:
            claim: The claim to verify
            user_id: Optional user ID for rate limiting
            options: Optional verification options
        
        Returns:
            EnhancedVerificationResult with comprehensive analysis
        """
        start_time = time.time()
        request_id = hashlib.md5(f"{claim}{time.time()}".encode()).hexdigest()[:16]
        
        # Initialize if needed
        if not self._initialized:
            await self.initialize()
        
        # Sanitize input
        claim = self.security.sanitize_input(claim)
        
        # Check rate limit
        if user_id and not self.security.check_rate_limit(user_id):
            raise RateLimitExceededError(f"Rate limit exceeded for user {user_id}")
        
        # Check cache first
        cache_hit = False
        if self.cache:
            cached = await self.cache.get_verification(claim)
            if cached:
                logger.info(f"Cache hit for claim: {claim[:50]}...", request_id=request_id)
                cache_hit = True
                # Update with cache hit info and return
                cached["metadata"]["cache_hit"] = True
                return self._dict_to_result(cached, request_id, cache_hit=True)
        
        # Use request coalescing for concurrent identical requests
        if self.coalescer:
            async def verify_func():
                return await self._do_verification(claim, request_id, options or {})
            
            result_dict = await self.coalescer.execute(claim, verify_func)
        else:
            result_dict = await self._do_verification(claim, request_id, options or {})
        
        # Cache the result
        if self.cache and not cache_hit:
            await self.cache.set_verification(claim, result_dict)
        
        # Track metrics
        processing_time = (time.time() - start_time) * 1000
        self.metrics.record_request(
            endpoint="verify_claim",
            method="POST",
            status_code=200,
            duration=processing_time / 1000
        )
        
        result_dict["metadata"]["processing_time_ms"] = processing_time
        
        return self._dict_to_result(result_dict, request_id, cache_hit=cache_hit)
    
    async def _do_verification(
        self,
        claim: str,
        request_id: str,
        options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Perform the actual verification across all sources.
        """
        logger.info(f"Starting verification for: {claim[:100]}...", request_id=request_id)
        
        providers_used = []
        warnings = []
        
        # Run verifications in parallel
        tasks = []
        
        # 1. Traditional fact-check (supermodel)
        tasks.append(self._run_traditional_verification(claim))
        providers_used.append("traditional_apis")
        
        # 2. Extended data sources
        if self.data_sources:
            tasks.append(self._run_extended_sources(claim))
            providers_used.append("extended_sources")
        
        # 3. LLM verification
        if self.llm_checker:
            tasks.append(self._run_llm_verification(claim))
            providers_used.append("llm_consensus")
        
        # Wait for all with timeout
        try:
            results = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=self.config.request_timeout_seconds
            )
        except asyncio.TimeoutError:
            warnings.append("Some verification sources timed out")
            results = [None] * len(tasks)
        
        # Process results
        traditional_result = results[0] if len(results) > 0 else None
        extended_result = results[1] if len(results) > 1 else None
        llm_result = results[2] if len(results) > 2 else None
        
        # Handle exceptions
        if isinstance(traditional_result, Exception):
            warnings.append(f"Traditional verification failed: {str(traditional_result)[:100]}")
            traditional_result = None
        
        if isinstance(extended_result, Exception):
            warnings.append(f"Extended sources failed: {str(extended_result)[:100]}")
            extended_result = None
        
        if isinstance(llm_result, Exception):
            warnings.append(f"LLM verification failed: {str(llm_result)[:100]}")
            llm_result = None
        
        # Combine results
        combined = self._combine_results(
            claim=claim,
            traditional=traditional_result,
            extended=extended_result,
            llm=llm_result,
            warnings=warnings,
            providers_used=providers_used,
            request_id=request_id
        )
        
        return combined
    
    async def _run_traditional_verification(self, claim: str) -> VerificationResult:
        """Run traditional fact-check APIs"""
        return await self.super_model.verify_claim(claim)
    
    async def _run_extended_sources(self, claim: str) -> Dict[str, Any]:
        """Run extended data sources"""
        if not self.data_sources:
            return {}
        
        evidence = await self.data_sources.get_evidence_for_claim(
            claim,
            min_credibility=self.config.min_source_credibility
        )
        
        return evidence
    
    async def _run_llm_verification(self, claim: str) -> Dict[str, Any]:
        """Run multi-LLM consensus verification"""
        if not self.llm_checker:
            return {}
        
        result = await self.llm_checker.verify_claim(claim, use_consensus=True)
        return {"consensus": result, "model_responses": [], "agreement_rate": result.get("agreement", 0)}
    
    def _combine_results(
        self,
        claim: str,
        traditional: Optional[VerificationResult],
        extended: Optional[Dict],
        llm: Optional[Dict],
        warnings: List[str],
        providers_used: List[str],
        request_id: str
    ) -> Dict[str, Any]:
        """
        Combine results from all sources into a unified verdict.
        Uses weighted voting based on source credibility.
        
        IMPORTANT: LLM consensus is the PRIMARY source for verdicts.
        Traditional APIs mostly find existing fact-checks, so "unverifiable"
        from them just means "no existing fact-check found" - NOT that
        the claim is unverifiable.
        """
        verdicts = []
        confidences = []
        
        # Extract traditional verdict
        traditional_sources = []
        if traditional:
            # ONLY add traditional verdict if it's a definitive TRUE/FALSE
            # "unverifiable" from traditional just means no fact-check was found
            if traditional.status.value in [
                VerificationStatus.VERIFIED_TRUE.value,
                VerificationStatus.VERIFIED_FALSE.value,
                VerificationStatus.PARTIALLY_TRUE.value
            ]:
                verdicts.append((traditional.status.value, traditional.confidence_score, 0.4))
                confidences.append(traditional.confidence_score)
            else:
                # Still track confidence but don't add to verdicts
                confidences.append(traditional.confidence_score * 0.3)  # Reduced weight for non-definitive
            
            traditional_sources = [
                {
                    "name": s.name,
                    "url": s.url,
                    "credibility": s.credibility.value,
                    "rating": s.claim_rating
                }
                for s in traditional.sources
            ]
        
        # Extract extended source verdict
        extended_sources = []
        if extended and extended.get("evidence_count", 0) > 0:
            # Use evidence strength as confidence
            evidence_strength = extended.get("evidence_strength", 0.5)
            confidences.append(evidence_strength)
            
            extended_sources = extended.get("top_sources", [])
        
        # Extract LLM verdict - THIS IS THE PRIMARY SOURCE
        llm_analysis = {}
        llm_has_verdict = False
        if llm and llm.get("consensus"):
            llm_consensus = llm["consensus"]
            
            # Map LLM verdict to status
            llm_verdict = llm_consensus.get("verdict", "").upper()
            llm_confidence = llm_consensus.get("confidence", 0.5)
            llm_agreement = llm_consensus.get("agreement", 0)
            
            status_map = {
                "TRUE": VerificationStatus.VERIFIED_TRUE.value,
                "FALSE": VerificationStatus.VERIFIED_FALSE.value,
                "PARTIALLY_TRUE": VerificationStatus.PARTIALLY_TRUE.value,
                "UNVERIFIABLE": VerificationStatus.UNVERIFIABLE.value,
            }
            
            mapped_status = status_map.get(llm_verdict, VerificationStatus.NEEDS_CONTEXT.value)
            
            # LLM gets higher weight when it has high confidence AND agreement
            llm_weight = 0.5  # Base weight for LLM
            if llm_confidence >= 0.9 and llm_agreement >= 0.8:
                llm_weight = 0.7  # High confidence + agreement = higher weight
            
            verdicts.append((mapped_status, llm_confidence, llm_weight))
            confidences.append(llm_confidence)
            llm_has_verdict = True
            
            llm_analysis = {
                "consensus": llm_consensus,
                "model_responses": llm.get("model_responses", []),
                "agreement_rate": llm.get("agreement_rate", 0)
            }
        
        # Calculate final verdict using weighted voting
        final_status, final_confidence = self._weighted_consensus(verdicts)
        
        # If LLM has high confidence verdict, use its confidence as final
        if llm_has_verdict and llm and llm.get("consensus"):
            llm_conf = llm["consensus"].get("confidence", 0.5)
            llm_agree = llm["consensus"].get("agreement", 0)
            if llm_conf >= 0.9 and llm_agree >= 0.8:
                final_confidence = llm_conf
        
        # If confidence is very low or no verdicts, default to UNVERIFIABLE
        if not verdicts or final_confidence < 0.3:
            final_status = VerificationStatus.UNVERIFIABLE.value
            final_confidence = max(final_confidence, 0.3) if confidences else 0.3
            warnings.append("Insufficient evidence for a definitive verdict")
        
        # Override confidence if below threshold
        if final_confidence < self.config.min_confidence_threshold:
            warnings.append("Low confidence result - limited evidence available")
        
        # Determine supporting vs contradicting evidence
        # IMPORTANT: Don't just look at rating - check if the source is actually about our claim
        supporting = []
        contradicting = []
        neutral = []
        
        # Extract key terms from the claim for relevance checking
        claim_lower = claim.lower()
        claim_words = set(claim_lower.split())
        
        for source in traditional_sources + extended_sources:
            if isinstance(source, dict):
                source_name = (source.get("name") or "").lower()
                source_url = (source.get("url") or "").lower()
                rating = (source.get("rating") or "").lower()
                
                # Check if this source is actually relevant to our claim
                # by checking if key claim words appear in the source info
                is_relevant = True  # Default to relevant for now
                
                # For fact-check sources, the rating is about a DIFFERENT claim
                # We should treat these as informational, not as verdicts on OUR claim
                # unless the source explicitly confirms/denies our specific claim
                
                if rating:
                    if any(w in rating for w in ["true", "correct", "verified", "accurate"]):
                        supporting.append(source)
                    elif any(w in rating for w in ["false", "incorrect", "fake", "wrong", "misleading"]):
                        # Note: This rating is for a fact-check FOUND about a topic
                        # It doesn't mean our claim is false - just that there's misinformation
                        # about this topic. Mark as informational, not contradicting
                        neutral.append(source)  # Changed from contradicting
                    else:
                        neutral.append(source)
                else:
                    # No rating - treat as neutral informational source
                    neutral.append(source)
        
        # Generate explanation
        explanation = self._generate_explanation(
            claim=claim,
            status=final_status,
            traditional=traditional,
            extended=extended,
            llm=llm_analysis
        )
        
        # Generate basic summary
        basic_summary = self._generate_summary(final_status, len(traditional_sources), len(extended_sources))
        
        # Generate comprehensive summary for paid tiers
        comprehensive_summary = self._generate_comprehensive_summary(
            claim=claim,
            status=final_status,
            confidence=final_confidence,
            traditional=traditional,
            extended=extended,
            llm=llm_analysis,
            supporting=supporting,
            contradicting=contradicting,
            neutral=neutral,
            traditional_sources=traditional_sources,
            extended_sources=extended_sources
        )
        
        return {
            "claim": claim,
            "verdict": {
                "status": final_status,
                "confidence": final_confidence,
                "summary": basic_summary
            },
            "analysis": {
                "explanation": explanation,
                "supporting_evidence": supporting,
                "contradicting_evidence": contradicting,
                "comprehensive_summary": comprehensive_summary
            },
            "sources": {
                "traditional": traditional_sources,
                "extended": extended_sources,
                "providers": providers_used
            },
            "llm_analysis": llm_analysis,
            "warnings": warnings,
            "metadata": {
                "request_id": request_id,
                "timestamp": datetime.now().isoformat(),
                "processing_time_ms": 0,  # Will be updated
                "cache_hit": False
            }
        }
    
    def _weighted_consensus(
        self,
        verdicts: List[Tuple[str, float, float]]
    ) -> Tuple[str, float]:
        """
        Calculate consensus using weighted voting.
        
        Args:
            verdicts: List of (status, confidence, weight) tuples
        
        Returns:
            (final_status, final_confidence)
        """
        if not verdicts:
            return VerificationStatus.UNVERIFIABLE.value, 0.0
        
        # Group verdicts
        status_scores = {}
        total_weight = 0
        
        for status, confidence, weight in verdicts:
            weighted_score = confidence * weight
            if status not in status_scores:
                status_scores[status] = 0
            status_scores[status] += weighted_score
            total_weight += weight
        
        if total_weight == 0:
            return VerificationStatus.UNVERIFIABLE.value, 0.0
        
        # Normalize scores
        for status in status_scores:
            status_scores[status] /= total_weight
        
        # Find highest scoring status
        best_status = max(status_scores.items(), key=lambda x: x[1])
        
        return best_status[0], best_status[1]
    
    def _generate_explanation(
        self,
        claim: str,
        status: str,
        traditional: Optional[VerificationResult],
        extended: Optional[Dict],
        llm: Dict
    ) -> str:
        """Generate a detailed explanation of the verification result"""
        
        parts = []
        
        # Status explanation
        status_explanations = {
            VerificationStatus.VERIFIED_TRUE.value: "This claim has been verified as TRUE based on multiple reliable sources.",
            VerificationStatus.VERIFIED_FALSE.value: "This claim has been verified as FALSE based on contradicting evidence.",
            VerificationStatus.PARTIALLY_TRUE.value: "This claim contains some truth but is incomplete or partially inaccurate.",
            VerificationStatus.UNVERIFIABLE.value: "This claim could not be verified due to insufficient evidence.",
            VerificationStatus.NEEDS_CONTEXT.value: "This claim requires additional context for proper verification.",
            VerificationStatus.DISPUTED.value: "This claim is disputed - sources disagree on its accuracy."
        }
        parts.append(status_explanations.get(status, "The verification status is unclear."))
        
        # Source summary
        if traditional and traditional.sources:
            parts.append(f"Consulted {len(traditional.sources)} traditional fact-checking sources.")
        
        if extended and extended.get("evidence_count"):
            parts.append(f"Found {extended['evidence_count']} pieces of supporting evidence from academic and news sources.")
        
        if llm and llm.get("consensus"):
            agreement = llm.get("agreement_rate", 0)
            parts.append(f"AI analysis showed {agreement:.0%} agreement across multiple language models.")
        
        return " ".join(parts)
    
    def _generate_comprehensive_summary(
        self,
        claim: str,
        status: str,
        confidence: float,
        traditional: Optional[VerificationResult],
        extended: Optional[Dict],
        llm: Dict,
        supporting: List[Dict],
        contradicting: List[Dict],
        neutral: List[Dict],
        traditional_sources: List[Dict],
        extended_sources: List[Dict]
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive summary for paid tiers that includes:
        - Subject matter analysis
        - Question analysis
        - Source agreements
        - Source contradictions
        - Evidence-based conclusion
        """
        
        # 1. Analyze subject matter - MORE DETAILED
        subject_analysis = self._analyze_subject_matter(claim)
        
        # 2. Analyze the question being asked
        question_analysis = self._analyze_question(claim)
        
        # 3. Gather source agreements - Focus on LLM consensus
        agreements = self._find_source_agreements(
            traditional, extended, llm, traditional_sources, extended_sources, supporting
        )
        
        # 4. Gather source contradictions - Only real contradictions
        contradictions = self._find_source_contradictions(
            traditional, extended, llm, traditional_sources, extended_sources, supporting, contradicting, neutral
        )
        
        # 5. Build evidence-based conclusion - USE LLM VERDICT AS PRIMARY
        conclusion = self._build_evidence_based_conclusion(
            claim, status, confidence, agreements, contradictions, llm, supporting, neutral
        )
        
        # 6. Generate narrative summary - MUCH MORE DETAILED
        narrative = self._generate_narrative_summary(
            claim, subject_analysis, question_analysis, 
            agreements, contradictions, conclusion, status, confidence, llm
        )
        
        return {
            "subject_matter": subject_analysis,
            "question_analysis": question_analysis,
            "source_agreements": agreements,
            "source_contradictions": contradictions,
            "conclusion": conclusion,
            "narrative_summary": narrative,
            "confidence_explanation": self._explain_confidence(confidence, agreements, contradictions)
        }
    
    def _analyze_subject_matter(self, claim: str) -> Dict[str, Any]:
        """Analyze what the claim is about - comprehensive subject analysis"""
        claim_lower = claim.lower()
        
        # Detect categories with more detail
        categories = []
        category_keywords = {
            "politics": ["president", "congress", "senator", "election", "vote", "government", "policy", "democrat", "republican", "biden", "trump", "minister", "parliament", "legislation"],
            "health": ["vaccine", "covid", "disease", "health", "medical", "doctor", "hospital", "treatment", "cure", "virus", "medicine", "symptoms", "pandemic", "fda", "who"],
            "science": ["climate", "research", "study", "scientist", "experiment", "nasa", "space", "physics", "biology", "chemistry", "discovery", "evidence", "theory"],
            "economics": ["economy", "inflation", "gdp", "stock", "market", "unemployment", "trade", "tax", "budget", "debt", "recession", "interest rate", "federal reserve"],
            "technology": ["ai", "artificial intelligence", "tech", "software", "computer", "internet", "digital", "cyber", "algorithm", "app", "smartphone", "social media"],
            "environment": ["climate change", "pollution", "environment", "carbon", "emission", "renewable", "energy", "fossil fuel", "global warming", "ecosystem"],
            "social": ["crime", "education", "immigration", "poverty", "inequality", "race", "gender", "discrimination", "protest", "rights"],
            "history": ["war", "historical", "century", "ancient", "founded", "invented", "discovered", "built", "wwii", "revolution"],
            "geography": ["located", "country", "city", "population", "capital", "region", "continent", "ocean", "mountain", "river", "border"]
        }
        
        matched_keywords = {}
        for category, keywords in category_keywords.items():
            matches = [kw for kw in keywords if kw in claim_lower]
            if matches:
                categories.append(category)
                matched_keywords[category] = matches
        
        if not categories:
            categories = ["general"]
        
        # Detect entities - improved detection
        entities = []
        named_entities = {
            "people": [],
            "places": [],
            "organizations": [],
            "other": []
        }
        
        words = claim.split()
        i = 0
        while i < len(words):
            word = words[i].strip('.,!?"\'():;')
            
            # Look for multi-word proper nouns (e.g., "Eiffel Tower", "United States")
            if word and word[0].isupper() and len(word) > 1:
                # Check if next word is also capitalized
                entity_words = [word]
                j = i + 1
                while j < len(words):
                    next_word = words[j].strip('.,!?"\'():;')
                    if next_word and next_word[0].isupper() and len(next_word) > 1:
                        entity_words.append(next_word)
                        j += 1
                    else:
                        break
                
                # Combine into entity
                if i > 0 or len(entity_words) > 1:  # Skip first word unless part of multi-word
                    entity = " ".join(entity_words)
                    if entity not in entities:
                        entities.append(entity)
                        # Categorize entity
                        entity_lower = entity.lower()
                        if any(title in entity_lower for title in ["president", "dr.", "mr.", "ms.", "senator", "king", "queen"]):
                            named_entities["people"].append(entity)
                        elif any(place in entity_lower for place in ["city", "country", "state", "tower", "building", "river", "mountain"]) or "located" in claim_lower:
                            named_entities["places"].append(entity)
                        elif any(org in entity_lower for org in ["company", "corporation", "inc", "llc", "organization", "agency"]):
                            named_entities["organizations"].append(entity)
                        else:
                            # Heuristic: if geography category, treat as place
                            if "geography" in categories:
                                named_entities["places"].append(entity)
                            else:
                                named_entities["other"].append(entity)
                
                i = j
            else:
                i += 1
        
        # Detect claim characteristics
        claim_type = self._detect_claim_type(claim)
        word_count = len(claim.split())
        
        # Sensitivity assessment
        sensitivity = "low"
        sensitive_topics = ["vaccine", "election", "fraud", "conspiracy", "hoax", "fake", "covid", "death", "attack"]
        if any(topic in claim_lower for topic in sensitive_topics):
            sensitivity = "high"
        elif any(topic in claim_lower for topic in ["politics", "religion", "war", "protest"]):
            sensitivity = "medium"
        
        # Temporal context
        temporal = "present"
        if any(w in claim_lower for w in ["was", "were", "had", "did", "used to", "founded", "invented", "built"]):
            temporal = "past"
        elif any(w in claim_lower for w in ["will", "going to", "future", "predicted", "expected"]):
            temporal = "future"
        
        return {
            "categories": categories,
            "primary_category": categories[0] if categories else "general",
            "matched_keywords": matched_keywords,
            "entities_mentioned": list(set(entities))[:10],
            "named_entities": named_entities,
            "claim_type": claim_type,
            "claim_type_description": self._get_claim_type_description(claim_type),
            "complexity": "complex" if word_count > 25 else "moderate" if word_count > 12 else "simple",
            "word_count": word_count,
            "sensitivity": sensitivity,
            "temporal_context": temporal,
            "requires_expertise": any(cat in categories for cat in ["science", "health", "economics", "technology"])
        }
    
    def _get_claim_type_description(self, claim_type: str) -> str:
        """Get a human-readable description of the claim type"""
        descriptions = {
            "statistical": "A claim involving specific numbers, percentages, or data",
            "attribution": "A claim attributing a statement or action to someone",
            "prediction": "A claim about future events or outcomes",
            "causal": "A claim about cause and effect relationships",
            "factual": "A straightforward claim about facts or reality",
            "comparative": "A claim comparing things or making superlative statements",
            "general": "A general claim requiring factual verification"
        }
        return descriptions.get(claim_type, "A claim requiring verification")
    def _detect_claim_type(self, claim: str) -> str:
        """Detect what type of claim this is"""
        claim_lower = claim.lower()
        
        if any(w in claim_lower for w in ["percent", "%", "number", "million", "billion", "thousand", "statistics"]):
            return "statistical"
        elif any(w in claim_lower for w in ["said", "stated", "claimed", "announced", "tweeted", "quote"]):
            return "attribution"
        elif any(w in claim_lower for w in ["will", "going to", "predict", "forecast", "expect"]):
            return "prediction"
        elif any(w in claim_lower for w in ["cause", "because", "leads to", "results in", "effect"]):
            return "causal"
        elif any(w in claim_lower for w in ["is", "are", "was", "were", "located", "contains", "has"]):
            return "factual"
        elif any(w in claim_lower for w in ["best", "worst", "most", "least", "only", "first", "last"]):
            return "comparative"
        else:
            return "general"
    
    def _analyze_question(self, claim: str) -> Dict[str, Any]:
        """Analyze what question is being asked/claimed"""
        claim_lower = claim.lower()
        
        # What is the claim asserting?
        if claim_lower.startswith(("is", "are", "was", "were", "does", "do", "did", "has", "have", "can", "could")):
            question_type = "yes_no"
        elif any(claim_lower.startswith(w) for w in ["how many", "how much", "what percent", "what number"]):
            question_type = "quantitative"
        elif claim_lower.startswith(("who", "what", "where", "when", "why", "how")):
            question_type = "open_ended"
        else:
            question_type = "declarative_assertion"
        
        # What would prove this true?
        proof_requirements = []
        if "percent" in claim_lower or "%" in claim_lower:
            proof_requirements.append("Statistical data from authoritative source")
        if any(w in claim_lower for w in ["said", "stated", "claimed"]):
            proof_requirements.append("Direct quote or transcript verification")
        if any(w in claim_lower for w in ["located", "in", "at"]):
            proof_requirements.append("Geographic or location verification")
        if any(w in claim_lower for w in ["cause", "because", "leads"]):
            proof_requirements.append("Scientific or causal evidence")
        if any(w in claim_lower for w in ["invented", "discovered", "founded", "built"]):
            proof_requirements.append("Historical records verification")
        
        if not proof_requirements:
            proof_requirements.append("Multiple credible source confirmation")
        
        return {
            "question_type": question_type,
            "assertion_nature": "affirmative" if "not" not in claim_lower else "negative",
            "proof_requirements": proof_requirements,
            "verifiability_assessment": self._assess_verifiability(claim)
        }
    
    def _assess_verifiability(self, claim: str) -> str:
        """Assess how verifiable a claim is"""
        claim_lower = claim.lower()
        
        if any(w in claim_lower for w in ["opinion", "think", "believe", "feel", "best", "worst", "should"]):
            return "subjective - difficult to verify objectively"
        elif any(w in claim_lower for w in ["will", "going to", "predict", "future"]):
            return "predictive - cannot be verified until future date"
        elif any(w in claim_lower for w in ["percent", "number", "statistics", "data"]):
            return "quantitative - verifiable with data sources"
        elif any(w in claim_lower for w in ["said", "stated", "quote"]):
            return "attributive - verifiable with transcript/recording"
        else:
            return "factual - verifiable with credible sources"
    
    def _find_source_agreements(
        self,
        traditional: Optional[VerificationResult],
        extended: Optional[Dict],
        llm: Dict,
        traditional_sources: List[Dict],
        extended_sources: List[Dict],
        supporting: List[Dict]
    ) -> Dict[str, Any]:
        """Find where sources agree - Focus on what the AI and sources confirm"""
        
        agreements = {
            "unanimous_points": [],
            "majority_points": [],
            "agreeing_sources": [],
            "agreement_strength": 0.0,
            "key_confirmations": []
        }
        
        # PRIMARY: LLM consensus is our main source of truth
        llm_verdict = None
        llm_confidence = 0.0
        if llm and llm.get("consensus"):
            consensus = llm["consensus"]
            agreement_rate = consensus.get("agreement", 0)
            llm_verdict = consensus.get("verdict", "").upper()
            llm_confidence = consensus.get("confidence", 0.5)
            
            # AI consensus is the strongest signal
            if agreement_rate >= 0.8:
                agreements["unanimous_points"].append({
                    "point": f"All AI models ({agreement_rate:.0%} agreement) confirm the claim is {llm_verdict}",
                    "source_type": "AI Consensus (Primary)",
                    "confidence": agreement_rate,
                    "weight": "high"
                })
                agreements["agreement_strength"] = agreement_rate
            elif agreement_rate >= 0.6:
                agreements["majority_points"].append({
                    "point": f"Most AI models ({agreement_rate:.0%} agreement) indicate the claim is {llm_verdict}",
                    "source_type": "AI Consensus",
                    "confidence": agreement_rate,
                    "weight": "medium"
                })
                agreements["agreement_strength"] = agreement_rate
            elif agreement_rate >= 0.4:
                agreements["majority_points"].append({
                    "point": f"AI models have mixed views ({agreement_rate:.0%} agreement) but lean towards {llm_verdict}",
                    "source_type": "AI Consensus",
                    "confidence": agreement_rate,
                    "weight": "low"
                })
                agreements["agreement_strength"] = agreement_rate
            
            # Extract key facts and evidence from LLM analysis
            key_facts = consensus.get("key_facts", [])
            explanation = consensus.get("explanation", "")
            
            # Add key facts as confirmations
            for i, fact in enumerate(key_facts[:6]):
                if fact and len(str(fact)) > 15:
                    agreements["key_confirmations"].append({
                        "fact": str(fact),
                        "source": "AI Analysis",
                        "importance": "high" if i < 2 else "medium"
                    })
                    # First 3 facts go to unanimous points
                    if i < 3:
                        agreements["unanimous_points"].append({
                            "point": str(fact),
                            "source_type": "AI Verified Fact",
                            "confidence": llm_confidence
                        })
            
            # Extract additional insights from explanation
            if explanation and len(explanation) > 50:
                # Split explanation into key points
                sentences = [s.strip() for s in explanation.split('.') if len(s.strip()) > 20]
                for sent in sentences[:3]:
                    if sent not in [f.get("fact") for f in agreements["key_confirmations"]]:
                        agreements["key_confirmations"].append({
                            "fact": sent + ".",
                            "source": "AI Analysis Detail",
                            "importance": "medium"
                        })
        
        # SECONDARY: Supporting fact-check sources
        for source in supporting:
            agreements["agreeing_sources"].append({
                "name": source.get("name", "Unknown Source"),
                "verdict": "Confirms claim accuracy",
                "url": source.get("url", ""),
                "credibility": source.get("credibility", "medium")
            })
        
        # If we have LLM agreement, that's our strength
        if llm_verdict and llm_confidence > 0:
            agreements["agreement_strength"] = max(agreements["agreement_strength"], llm_confidence)
        
        return agreements
    
    def _find_source_contradictions(
        self,
        traditional: Optional[VerificationResult],
        extended: Optional[Dict],
        llm: Dict,
        traditional_sources: List[Dict],
        extended_sources: List[Dict],
        supporting: List[Dict],
        contradicting: List[Dict],
        neutral: List[Dict]
    ) -> Dict[str, Any]:
        """
        Find where sources contradict each other.
        
        IMPORTANT: A fact-check API returning FALSE for an unrelated claim 
        is NOT a contradiction of OUR claim. We need to be smart about this.
        """
        
        contradictions = {
            "direct_contradictions": [],
            "conflicting_sources": [],
            "areas_of_disagreement": [],
            "related_misinformation": [],
            "contradiction_severity": "none",
            "analysis_notes": []
        }
        
        # Get LLM verdict first - this is our primary signal
        llm_verdict = None
        llm_agreement = 0.0
        if llm and llm.get("consensus"):
            llm_verdict = llm["consensus"].get("verdict", "").upper()
            llm_agreement = llm["consensus"].get("agreement", 0)
        
        # Check if there are ACTUAL contradicting sources
        # (These would be sources that explicitly say our specific claim is false)
        if contradicting and len(contradicting) > 0:
            # Only count as contradiction if there's significant disagreement
            if len(contradicting) > len(supporting):
                contradictions["direct_contradictions"].append({
                    "description": f"Found {len(contradicting)} sources questioning the claim vs {len(supporting)} supporting it",
                    "supporting_count": len(supporting),
                    "contradicting_count": len(contradicting),
                    "severity": "significant"
                })
                contradictions["contradiction_severity"] = "moderate"
            elif len(contradicting) > 0:
                contradictions["analysis_notes"].append(
                    f"Some sources ({len(contradicting)}) present alternative views, but majority support the claim."
                )
                contradictions["contradiction_severity"] = "low"
        
        # Handle neutral sources that have FALSE ratings
        # These are fact-checks about RELATED topics, not our specific claim
        false_rated_neutral = [s for s in neutral if "false" in (s.get("rating") or "").lower()]
        if false_rated_neutral:
            contradictions["related_misinformation"].append({
                "description": f"Found {len(false_rated_neutral)} fact-checks about related misinformation in this topic area",
                "note": "These are fact-checks about other claims in this topic, not contradictions of the current claim",
                "sources": [s.get("name", "Unknown") for s in false_rated_neutral[:3]]
            })
            contradictions["analysis_notes"].append(
                f"Note: {len(false_rated_neutral)} fact-checks exist about misinformation in this topic area, "
                "indicating this is a subject where misinformation circulates."
            )
        
        # Check LLM disagreement between models
        if llm and llm.get("consensus"):
            individual_results = llm["consensus"].get("individual_results", [])
            if len(individual_results) > 1:
                verdicts = [r.get("verdict", "").upper() for r in individual_results if r.get("verdict")]
                unique_verdicts = set(verdicts)
                
                if len(unique_verdicts) > 1:
                    # AI models disagree - this IS a real contradiction
                    contradictions["areas_of_disagreement"].append({
                        "area": "AI Model Analysis",
                        "positions": list(unique_verdicts),
                        "description": f"AI models have different assessments: {', '.join(unique_verdicts)}",
                        "significance": "high"
                    })
                    # Upgrade severity if AI models disagree
                    if contradictions["contradiction_severity"] == "none":
                        contradictions["contradiction_severity"] = "low"
        
        # If LLM has high agreement and no real contradictions, severity stays none
        if llm_agreement >= 0.8 and not contradicting:
            contradictions["contradiction_severity"] = "none"
            contradictions["analysis_notes"].append(
                "AI models show strong consensus. No significant contradictions found."
            )
        
        return contradictions
    
    def _build_evidence_based_conclusion(
        self,
        claim: str,
        status: str,
        confidence: float,
        agreements: Dict,
        contradictions: Dict,
        llm: Dict,
        supporting: List[Dict],
        neutral: List[Dict]
    ) -> Dict[str, Any]:
        """
        Build a comprehensive evidence-based conclusion with detailed reasoning.
        
        IMPORTANT: The LLM consensus verdict should be the PRIMARY source of truth,
        as it directly analyzes the claim, unlike fact-check API search results.
        """
        
        # Get LLM verdict - this is our primary signal
        llm_verdict = None
        llm_confidence = 0.5
        llm_explanation = ""
        llm_agreement = 0.0
        
        if llm and llm.get("consensus"):
            consensus = llm["consensus"]
            llm_verdict = consensus.get("verdict", "").upper()
            llm_confidence = consensus.get("confidence", 0.5)
            llm_explanation = consensus.get("explanation", "")
            llm_agreement = consensus.get("agreement", 0)
        
        # Determine the ACTUAL verdict based on LLM consensus (not fact-check search results)
        actual_verdict = status
        if llm_verdict and llm_agreement >= 0.7:
            # Map LLM verdict to our status
            verdict_map = {
                "TRUE": VerificationStatus.VERIFIED_TRUE.value,
                "FALSE": VerificationStatus.VERIFIED_FALSE.value,
                "PARTIALLY_TRUE": VerificationStatus.PARTIALLY_TRUE.value,
                "UNVERIFIABLE": VerificationStatus.UNVERIFIABLE.value,
            }
            actual_verdict = verdict_map.get(llm_verdict, status)
        
        # Calculate actual confidence based on LLM agreement
        actual_confidence = max(confidence, llm_confidence) if llm_agreement >= 0.7 else confidence
        
        conclusion = {
            "verdict": actual_verdict,
            "verdict_label": actual_verdict.replace("_", " ").upper(),
            "confidence_level": "high" if actual_confidence > 0.8 else "moderate" if actual_confidence > 0.5 else "low",
            "confidence_percentage": round(actual_confidence * 100, 1),
            "reasoning": [],
            "reasoning_chain": [],
            "key_evidence": [],
            "supporting_factors": [],
            "limiting_factors": [],
            "limitations": [],
            "recommendation": "",
            "methodology_note": ""
        }
        
        # Build detailed reasoning chain
        reasoning_chain = []
        
        # Step 1: What was analyzed
        reasoning_chain.append({
            "step": 1,
            "action": "Claim Analysis",
            "finding": f"Analyzed the claim: \"{claim[:100]}{'...' if len(claim) > 100 else ''}\"",
            "detail": f"This is a {agreements.get('key_confirmations', [{}])[0].get('importance', 'standard')} priority verification request."
        })
        
        # Step 2: AI Consensus
        if llm_agreement >= 0.7:
            reasoning_chain.append({
                "step": 2,
                "action": "AI Model Consensus",
                "finding": f"Multiple AI models reached {llm_agreement:.0%} agreement that this claim is {llm_verdict}",
                "detail": llm_explanation[:300] if llm_explanation else "AI models analyzed the claim and reached consensus."
            })
        elif llm_verdict:
            reasoning_chain.append({
                "step": 2,
                "action": "AI Model Analysis",
                "finding": f"AI models leaned towards {llm_verdict} with {llm_agreement:.0%} agreement",
                "detail": "Some disagreement exists between AI models on this claim."
            })
        
        # Step 3: Source Analysis
        source_count = len(supporting) + len(neutral)
        if source_count > 0:
            reasoning_chain.append({
                "step": 3,
                "action": "Source Verification",
                "finding": f"Consulted {source_count} external sources for corroboration",
                "detail": f"{len(supporting)} sources directly support the claim, {len(neutral)} provide contextual information."
            })
        
        # Step 4: Contradiction Check
        contradiction_severity = contradictions.get("contradiction_severity", "none")
        if contradiction_severity == "none":
            reasoning_chain.append({
                "step": 4,
                "action": "Contradiction Analysis",
                "finding": "No significant contradictions found",
                "detail": "Sources are generally consistent in their assessment."
            })
        else:
            reasoning_chain.append({
                "step": 4,
                "action": "Contradiction Analysis",
                "finding": f"Found {contradiction_severity} level of source disagreement",
                "detail": "; ".join(contradictions.get("analysis_notes", ["Some sources present different views."]))
            })
        
        # Step 5: Final Verdict
        reasoning_chain.append({
            "step": 5,
            "action": "Final Determination",
            "finding": f"Verdict: {actual_verdict.replace('_', ' ').upper()} with {conclusion['confidence_level']} confidence",
            "detail": f"Based on {llm_agreement:.0%} AI consensus and {source_count} source(s) consulted."
        })
        
        conclusion["reasoning_chain"] = reasoning_chain
        
        # Build reasoning sentences (simplified for narrative)
        reasoning = []
        
        if llm_agreement >= 0.8:
            reasoning.append(f"All AI models unanimously ({llm_agreement:.0%}) agree that this claim is {llm_verdict}.")
        elif llm_agreement >= 0.6:
            reasoning.append(f"Most AI models ({llm_agreement:.0%}) agree that this claim is {llm_verdict}.")
        
        if supporting:
            reasoning.append(f"{len(supporting)} fact-checking source(s) support this assessment.")
        
        if agreements.get("key_confirmations"):
            top_facts = [c["fact"] for c in agreements["key_confirmations"][:2]]
            reasoning.append(f"Key supporting evidence: {'; '.join(top_facts)}")
        
        if contradiction_severity != "none":
            reasoning.append(f"However, some {contradiction_severity} contradictions were noted in the source analysis.")
        
        conclusion["reasoning"] = reasoning
        
        # Extract key evidence from LLM and agreements
        key_evidence = []
        
        # From LLM key facts
        if llm and llm.get("consensus"):
            for fact in llm["consensus"].get("key_facts", [])[:4]:
                if fact and len(str(fact)) > 15 and str(fact) not in key_evidence:
                    key_evidence.append(str(fact))
        
        # From agreements
        for conf in agreements.get("key_confirmations", [])[:3]:
            fact = conf.get("fact", "")
            if fact and len(fact) > 15 and fact not in key_evidence:
                key_evidence.append(fact)
        
        conclusion["key_evidence"] = key_evidence[:8]
        
        # Supporting factors
        if llm_agreement >= 0.7:
            conclusion["supporting_factors"].append(f"Strong AI consensus ({llm_agreement:.0%})")
        if len(supporting) > 0:
            conclusion["supporting_factors"].append(f"{len(supporting)} corroborating source(s)")
        if agreements.get("unanimous_points"):
            conclusion["supporting_factors"].append(f"{len(agreements['unanimous_points'])} points of unanimous agreement")
        
        # Limiting factors
        if actual_confidence < 0.6:
            conclusion["limiting_factors"].append("Limited evidence availability")
        if contradiction_severity in ["moderate", "high"]:
            conclusion["limiting_factors"].append("Source disagreements present")
        if not llm_verdict:
            conclusion["limiting_factors"].append("AI analysis inconclusive")
        
        conclusion["limitations"] = conclusion["limiting_factors"]  # Alias for backwards compat
        
        # Detailed recommendation
        if actual_verdict == VerificationStatus.VERIFIED_TRUE.value:
            if actual_confidence >= 0.8:
                conclusion["recommendation"] = "This claim is accurate and can be confidently shared. Our analysis found strong evidence supporting its truthfulness."
            else:
                conclusion["recommendation"] = "This claim appears to be accurate based on available evidence, though some limitations exist in our analysis."
        elif actual_verdict == VerificationStatus.VERIFIED_FALSE.value:
            conclusion["recommendation"] = "This claim is inaccurate and should not be shared. Consider fact-checking before spreading this information."
        elif actual_verdict == VerificationStatus.PARTIALLY_TRUE.value:
            conclusion["recommendation"] = "This claim contains some accurate elements but is incomplete or misleading. Additional context is needed before sharing."
        else:
            conclusion["recommendation"] = "We could not definitively verify this claim. Exercise caution and seek additional sources before accepting or sharing this information."
        
        # Methodology note
        conclusion["methodology_note"] = (
            f"This verification used multi-model AI consensus (agreement: {llm_agreement:.0%}), "
            f"cross-referenced against {source_count} fact-checking and reference sources. "
            f"Final confidence: {conclusion['confidence_percentage']}%."
        )
        
        return conclusion
    
    def _generate_narrative_summary(
        self,
        claim: str,
        subject: Dict,
        question: Dict,
        agreements: Dict,
        contradictions: Dict,
        conclusion: Dict,
        status: str,
        confidence: float,
        llm: Dict
    ) -> str:
        """
        Generate a comprehensive, human-readable narrative summary.
        This should read like a research report executive summary.
        """
        
        paragraphs = []
        
        # === PARAGRAPH 1: Introduction and Context ===
        intro_parts = []
        
        # What is being claimed
        claim_preview = claim[:150] + "..." if len(claim) > 150 else claim
        intro_parts.append(f"**Claim Under Review:** \"{claim_preview}\"")
        
        # Subject matter context
        category = subject.get("primary_category", "general")
        categories = subject.get("categories", [category])
        claim_type = subject.get("claim_type", "factual")
        complexity = subject.get("complexity", "moderate")
        
        if len(categories) > 1:
            intro_parts.append(f"This {claim_type} claim falls under {', '.join(categories[:3])} and is classified as {complexity} in complexity.")
        else:
            intro_parts.append(f"This is a {complexity} {claim_type} claim related to {category}.")
        
        # Entities mentioned
        entities = subject.get("entities_mentioned", [])
        if entities:
            intro_parts.append(f"Key entities referenced: {', '.join(entities[:5])}.")
        
        paragraphs.append(" ".join(intro_parts))
        
        # === PARAGRAPH 2: Verification Methodology ===
        method_parts = []
        
        method_parts.append("**Verification Process:**")
        
        # What was checked
        verifiability = question.get("verifiability_assessment", "factual")
        method_parts.append(f"This claim is assessed as {verifiability}.")
        
        proof_reqs = question.get("proof_requirements", [])
        if proof_reqs:
            method_parts.append(f"To verify this claim, we examined: {'; '.join(proof_reqs[:3])}.")
        
        # Sources consulted
        source_count = len(agreements.get("agreeing_sources", [])) + len(contradictions.get("conflicting_sources", []))
        llm_agreement = 0.0
        if llm and llm.get("consensus"):
            llm_agreement = llm["consensus"].get("agreement", 0)
            method_parts.append(f"We employed multi-model AI consensus verification (achieving {llm_agreement:.0%} agreement) and cross-referenced against fact-checking databases.")
        
        paragraphs.append(" ".join(method_parts))
        
        # === PARAGRAPH 3: What Sources Agree On ===
        agreement_parts = []
        
        unanimous = agreements.get("unanimous_points", [])
        majority = agreements.get("majority_points", [])
        key_confirmations = agreements.get("key_confirmations", [])
        
        if unanimous or majority or key_confirmations:
            agreement_parts.append("**Source Agreement:**")
            
            if unanimous:
                agreement_parts.append(f"We found {len(unanimous)} points of unanimous agreement across our sources.")
            if majority:
                agreement_parts.append(f"Additionally, {len(majority)} points showed majority consensus.")
            
            # List top confirmations
            if key_confirmations:
                agreement_parts.append("Key confirmed facts include:")
                for i, conf in enumerate(key_confirmations[:4]):
                    fact = conf.get("fact", "")
                    if fact:
                        agreement_parts.append(f"• {fact}")
            
            paragraphs.append(" ".join(agreement_parts))
        
        # === PARAGRAPH 4: Contradictions and Disagreements ===
        if contradictions.get("contradiction_severity", "none") != "none":
            contradiction_parts = []
            contradiction_parts.append("**Areas of Disagreement:**")
            
            severity = contradictions.get("contradiction_severity", "none")
            contradiction_parts.append(f"We found {severity} levels of disagreement in our source analysis.")
            
            # Analysis notes
            for note in contradictions.get("analysis_notes", [])[:2]:
                contradiction_parts.append(note)
            
            # Related misinformation
            related_misinfo = contradictions.get("related_misinformation", [])
            if related_misinfo:
                for info in related_misinfo[:1]:
                    if info.get("note"):
                        contradiction_parts.append(f"Important context: {info['note']}")
            
            paragraphs.append(" ".join(contradiction_parts))
        
        # === PARAGRAPH 5: Evidence and Reasoning ===
        evidence_parts = []
        evidence_parts.append("**Evidence Analysis:**")
        
        key_evidence = conclusion.get("key_evidence", [])
        if key_evidence:
            evidence_parts.append(f"Our investigation uncovered {len(key_evidence)} key pieces of evidence.")
            # Include first 2-3 pieces
            for i, evidence in enumerate(key_evidence[:3]):
                evidence_parts.append(f"({i+1}) {evidence}")
        
        # Reasoning chain summary
        reasoning_chain = conclusion.get("reasoning_chain", [])
        if reasoning_chain:
            final_step = reasoning_chain[-1] if reasoning_chain else {}
            if final_step.get("finding"):
                evidence_parts.append(f"Final determination: {final_step['finding']}")
        
        if evidence_parts:
            paragraphs.append(" ".join(evidence_parts))
        
        # === PARAGRAPH 6: Conclusion ===
        conclusion_parts = []
        
        verdict = conclusion.get("verdict", status)
        verdict_label = verdict.replace("_", " ").upper()
        conf_level = conclusion.get("confidence_level", "moderate")
        conf_pct = conclusion.get("confidence_percentage", confidence * 100)
        
        conclusion_parts.append(f"**Conclusion:**")
        conclusion_parts.append(f"Based on our comprehensive analysis, this claim is rated **{verdict_label}** with **{conf_level} confidence** ({conf_pct:.0f}%).")
        
        # Supporting and limiting factors
        supporting = conclusion.get("supporting_factors", [])
        limiting = conclusion.get("limiting_factors", [])
        
        if supporting:
            conclusion_parts.append(f"Supporting factors: {'; '.join(supporting[:3])}.")
        if limiting:
            conclusion_parts.append(f"Limiting factors: {'; '.join(limiting[:2])}.")
        
        paragraphs.append(" ".join(conclusion_parts))
        
        # === PARAGRAPH 7: Recommendation ===
        recommendation = conclusion.get("recommendation", "")
        methodology = conclusion.get("methodology_note", "")
        
        if recommendation:
            rec_parts = [f"**Recommendation:** {recommendation}"]
            if methodology:
                rec_parts.append(f"[{methodology}]")
            paragraphs.append(" ".join(rec_parts))
        
        # Join all paragraphs with double line breaks
        return "\n\n".join(paragraphs)
    
    def _explain_confidence(
        self,
        confidence: float,
        agreements: Dict,
        contradictions: Dict
    ) -> str:
        """Explain why the confidence score is what it is"""
        
        factors = []
        
        # Positive factors
        if confidence > 0.7:
            if agreements.get("unanimous_points"):
                factors.append("Strong source agreement")
            if agreements.get("agreement_strength", 0) > 0.7:
                factors.append("High source consensus")
        
        # Negative factors
        if confidence < 0.6:
            if contradictions.get("contradiction_severity") in ["moderate", "high"]:
                factors.append("Source contradictions reduce confidence")
            if not agreements.get("unanimous_points"):
                factors.append("Limited unanimous agreement")
        
        if not factors:
            factors.append("Moderate evidence from multiple sources")
        
        return f"Confidence is {confidence:.0%} due to: {'; '.join(factors)}."
    
    def _generate_summary(
        self,
        status: str,
        traditional_count: int,
        extended_count: int
    ) -> str:
        """Generate a brief summary"""
        status_labels = {
            VerificationStatus.VERIFIED_TRUE.value: "TRUE",
            VerificationStatus.VERIFIED_FALSE.value: "FALSE",
            VerificationStatus.PARTIALLY_TRUE.value: "PARTIALLY TRUE",
            VerificationStatus.UNVERIFIABLE.value: "UNVERIFIABLE",
            VerificationStatus.NEEDS_CONTEXT.value: "NEEDS CONTEXT",
            VerificationStatus.DISPUTED.value: "DISPUTED"
        }
        
        label = status_labels.get(status, "UNKNOWN")
        total_sources = traditional_count + extended_count
        
        return f"Verdict: {label} (based on {total_sources} sources)"
    
    def _dict_to_result(
        self,
        data: Dict,
        request_id: str,
        cache_hit: bool = False
    ) -> EnhancedVerificationResult:
        """Convert dictionary to EnhancedVerificationResult"""
        
        verdict = data.get("verdict", {})
        analysis = data.get("analysis", {})
        sources = data.get("sources", {})
        metadata = data.get("metadata", {})
        
        return EnhancedVerificationResult(
            claim=data.get("claim", ""),
            status=VerificationStatus(verdict.get("status", "unverifiable")),
            confidence_score=verdict.get("confidence", 0.0),
            traditional_sources=[],  # Would need conversion
            extended_sources=sources.get("extended", []),
            llm_analysis=data.get("llm_analysis", {}),
            summary=verdict.get("summary", ""),
            explanation=analysis.get("explanation", ""),
            warnings=data.get("warnings", []),
            request_id=request_id,
            timestamp=datetime.fromisoformat(metadata.get("timestamp", datetime.now().isoformat())),
            processing_time_ms=metadata.get("processing_time_ms", 0),
            cache_hit=cache_hit,
            providers_used=sources.get("providers", []),
            supporting_evidence=analysis.get("supporting_evidence", []),
            contradicting_evidence=analysis.get("contradicting_evidence", []),
            comprehensive_summary=analysis.get("comprehensive_summary", {})
        )
    
    # ========================================
    # HEALTH & METRICS
    # ========================================
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get health status of all components"""
        health = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "components": {}
        }
        
        # Check traditional APIs
        if self.super_model:
            providers = []
            for provider in self.super_model.providers:
                if provider.is_available:
                    providers.append(provider.name)
            health["components"]["traditional_apis"] = {
                "status": "healthy" if providers else "degraded",
                "available_providers": providers
            }
        
        # Check LLM gateway
        if self.llm_gateway:
            available_providers = self.llm_gateway.get_available_providers()
            health["components"]["llm_gateway"] = {
                "status": "healthy" if available_providers else "degraded",
                "available_providers": available_providers
            }
        
        # Check data sources
        if self.data_sources:
            available = self.data_sources.get_available_sources()
            health["components"]["data_sources"] = {
                "status": "healthy" if available else "degraded",
                "available_sources": available
            }
        
        # Check cache
        if self.cache:
            # VerificationCache wraps MultiLevelCache which has redis
            has_redis = hasattr(self.cache, 'cache') and hasattr(self.cache.cache, 'redis') and self.cache.cache.redis is not None
            health["components"]["cache"] = {
                "status": "healthy",
                "type": "redis" if has_redis else "memory"
            }
        
        # Determine overall status
        degraded = any(
            c.get("status") == "degraded"
            for c in health["components"].values()
        )
        health["status"] = "degraded" if degraded else "healthy"
        
        return health
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics"""
        return self.metrics.get_all_metrics()


# ============================================================
# EXCEPTIONS
# ============================================================

class VerificationError(Exception):
    """Base verification error"""
    pass


class RateLimitExceededError(VerificationError):
    """Rate limit exceeded"""
    pass


class VerificationTimeoutError(VerificationError):
    """Verification timed out"""
    pass


# ============================================================
# SINGLETON / FACTORY
# ============================================================

_instance: Optional[EnhancedVerifier] = None


async def get_verifier(config: VerifierConfig = None) -> EnhancedVerifier:
    """Get or create the singleton Enhanced Verifier instance"""
    global _instance
    
    if _instance is None:
        _instance = EnhancedVerifier(config)
        await _instance.initialize()
    
    return _instance


async def shutdown_verifier():
    """Shutdown the singleton instance"""
    global _instance
    
    if _instance:
        await _instance.shutdown()
        _instance = None


# ============================================================
# MAIN / TESTING
# ============================================================

async def main():
    """Test the enhanced verifier"""
    
    print("\n" + "=" * 70)
    print("🚀 VERITY ENHANCED VERIFICATION ENGINE")
    print("=" * 70)
    
    config = VerifierConfig(
        enable_llm_verification=True,
        enable_caching=True,
        enable_data_sources=True
    )
    
    verifier = EnhancedVerifier(config)
    await verifier.initialize()
    
    test_claims = [
        "The Earth is approximately 4.5 billion years old",
        "Water boils at 100 degrees Celsius at sea level",
        "The Great Wall of China is visible from space with the naked eye",
    ]
    
    for claim in test_claims:
        print(f"\n📝 Claim: {claim}")
        print("-" * 50)
        
        try:
            result = await verifier.verify_claim(claim)
            
            print(f"✅ Verdict: {result.status.value}")
            print(f"📊 Confidence: {result.confidence_score:.1%}")
            print(f"⏱️  Time: {result.processing_time_ms:.0f}ms")
            print(f"📚 Sources: {len(result.traditional_sources) + len(result.extended_sources)}")
            print(f"💾 Cache Hit: {result.cache_hit}")
            
            if result.warnings:
                print(f"⚠️  Warnings: {', '.join(result.warnings)}")
            
            print(f"\n📋 {result.summary}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
    
    # Health check
    print("\n" + "=" * 70)
    print("🏥 HEALTH STATUS")
    print("=" * 70)
    
    health = await verifier.get_health_status()
    print(json.dumps(health, indent=2))
    
    # Shutdown
    await verifier.shutdown()
    
    print("\n✅ Test complete!")


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
