"""
Verity Master Orchestrator - The Brain
======================================
This is the MASTER CONTROLLER that brings everything together.

It orchestrates:
1. Claim decomposition
2. Provider routing
3. Parallel evidence gathering  
4. Evidence graph building
5. 7-layer consensus
6. Adaptive learning
7. Response formatting

THE COMPLETE FLOW:
=================
User Claim
    ↓
Claim Decomposer → Break into sub-claims
    ↓
Provider Router → Select best providers for each sub-claim
    ↓
Parallel Execution → Query 50+ providers simultaneously
    ↓
Evidence Graph → Build knowledge graph of evidence
    ↓
Consensus Engine → 7-layer analysis
    ↓
Adaptive Learning → Update weights, cache verdict
    ↓
Final Response → Verdict + Confidence + Sources

THIS IS THE SECRET SAUCE. 🔥
"""

import asyncio
import aiohttp
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict, List, Optional, Any
import json

# Core engine components
from verity_intelligence_engine import (
    Verdict, ClaimType, SourceTier, Evidence, SubClaim,
    ProviderResult, ConsensusResult, ClaimDecomposer, ProviderRouter,
    get_source_tier
)
from verity_consensus_engine import ConsensusEngine, ConfidenceCalculator
from verity_evidence_graph import EvidenceGraphBuilder, TrustNetworkAnalyzer
from verity_adaptive_learning import AdaptiveLearningSystem

# Provider imports
from enhanced_providers import (
    GeminiProvider, MistralProvider, TogetherAIProvider, CohereProvider,
    DeepSeekProvider, TavilyProvider, ExaProvider, BraveSearchProvider,
    YouComProvider, SemanticScholarProvider, CrossRefProvider,
    PubMedProvider, FullFactProvider, AFPFactCheckProvider
)

from ultimate_providers import (
    FireworksAIProvider, ReplicateProvider, CerebrasProvider, OpenRouterProvider,
    WolframAlphaProvider, GeoNamesProvider, MediaStackProvider, JinaAIProvider,
    ArXivProvider, DBpediaProvider, YAGOProvider, GoogleScholarProvider,
    ModalProvider, HyperbolicProvider
)


@dataclass
class VerityResponse:
    """The final response returned to users"""
    claim: str
    verdict: str
    verdict_emoji: str
    confidence_score: float
    confidence_display: str
    summary: str
    evidence_for: List[Dict]
    evidence_against: List[Dict]
    sources: List[Dict]
    warnings: List[str]
    alternative_perspectives: List[str]
    processing_time_ms: float
    providers_consulted: int
    sub_claims_analyzed: int
    reasoning_chain: List[str]
    
    # Detailed breakdown (optional)
    detailed_breakdown: Optional[Dict] = None


class VerityMasterOrchestrator:
    """
    The Master Orchestrator - Verity's Brain.
    
    This class coordinates ALL components to produce
    the most accurate fact-check possible.
    """
    
    VERDICT_EMOJIS = {
        Verdict.TRUE: "✅",
        Verdict.FALSE: "❌",
        Verdict.PARTIALLY_TRUE: "⚠️",
        Verdict.MISLEADING: "🔶",
        Verdict.UNVERIFIABLE: "❓",
        Verdict.DISPUTED: "⚔️",
        Verdict.NEEDS_CONTEXT: "📋",
        Verdict.OUTDATED: "📅",
    }
    
    def __init__(self, api_keys: Dict[str, str] = None):
        self.api_keys = api_keys or {}
        
        # Initialize core components
        self.decomposer = ClaimDecomposer()
        self.router = ProviderRouter()
        self.consensus_engine = ConsensusEngine()
        self.confidence_calculator = ConfidenceCalculator()
        self.learning_system = AdaptiveLearningSystem()
        
        # Initialize providers
        self._init_providers()
    
    def _init_providers(self):
        """Initialize all provider instances"""
        # AI Providers
        self.ai_providers = {}
        
        if 'GOOGLE_AI_KEY' in self.api_keys:
            self.ai_providers['gemini'] = GeminiProvider(self.api_keys['GOOGLE_AI_KEY'])
        
        if 'MISTRAL_API_KEY' in self.api_keys:
            self.ai_providers['mistral'] = MistralProvider(self.api_keys['MISTRAL_API_KEY'])
        
        if 'TOGETHER_AI_KEY' in self.api_keys:
            self.ai_providers['together'] = TogetherAIProvider(self.api_keys['TOGETHER_AI_KEY'])
        
        if 'COHERE_API_KEY' in self.api_keys:
            self.ai_providers['cohere'] = CohereProvider(self.api_keys['COHERE_API_KEY'])
        
        if 'DEEPSEEK_API_KEY' in self.api_keys:
            self.ai_providers['deepseek'] = DeepSeekProvider(self.api_keys['DEEPSEEK_API_KEY'])
        
        if 'FIREWORKS_API_KEY' in self.api_keys:
            self.ai_providers['fireworks'] = FireworksAIProvider(self.api_keys['FIREWORKS_API_KEY'])
        
        if 'REPLICATE_API_KEY' in self.api_keys:
            self.ai_providers['replicate'] = ReplicateProvider(self.api_keys['REPLICATE_API_KEY'])
        
        if 'CEREBRAS_API_KEY' in self.api_keys:
            self.ai_providers['cerebras'] = CerebrasProvider(self.api_keys['CEREBRAS_API_KEY'])
        
        if 'OPENROUTER_API_KEY' in self.api_keys:
            self.ai_providers['openrouter'] = OpenRouterProvider(self.api_keys['OPENROUTER_API_KEY'])
        
        if 'HYPERBOLIC_API_KEY' in self.api_keys:
            self.ai_providers['hyperbolic'] = HyperbolicProvider(self.api_keys['HYPERBOLIC_API_KEY'])
        
        # Search Providers
        self.search_providers = {}
        
        if 'TAVILY_API_KEY' in self.api_keys:
            self.search_providers['tavily'] = TavilyProvider(self.api_keys['TAVILY_API_KEY'])
        
        if 'EXA_API_KEY' in self.api_keys:
            self.search_providers['exa'] = ExaProvider(self.api_keys['EXA_API_KEY'])
        
        if 'BRAVE_API_KEY' in self.api_keys:
            self.search_providers['brave'] = BraveSearchProvider(self.api_keys['BRAVE_API_KEY'])
        
        if 'YDC_API_KEY' in self.api_keys:
            self.search_providers['you'] = YouComProvider(self.api_keys['YDC_API_KEY'])
        
        if 'JINA_API_KEY' in self.api_keys:
            self.search_providers['jina'] = JinaAIProvider(self.api_keys['JINA_API_KEY'])
        
        if 'MEDIASTACK_API_KEY' in self.api_keys:
            self.search_providers['mediastack'] = MediaStackProvider(self.api_keys['MEDIASTACK_API_KEY'])
        
        # Knowledge Providers (many are FREE!)
        self.knowledge_providers = {
            'semantic_scholar': SemanticScholarProvider(),  # FREE
            'crossref': CrossRefProvider(),  # FREE
            'pubmed': PubMedProvider(),  # FREE
            'arxiv': ArXivProvider(),  # FREE
            'dbpedia': DBpediaProvider(),  # FREE
            'yago': YAGOProvider(),  # FREE
        }
        
        if 'WOLFRAM_APP_ID' in self.api_keys:
            self.knowledge_providers['wolfram'] = WolframAlphaProvider(self.api_keys['WOLFRAM_APP_ID'])
        
        if 'GEONAMES_USERNAME' in self.api_keys:
            self.knowledge_providers['geonames'] = GeoNamesProvider(self.api_keys['GEONAMES_USERNAME'])
        
        # Fact-Check Providers
        self.factcheck_providers = {
            'fullfact': FullFactProvider(),  # FREE
            'afp': AFPFactCheckProvider(),  # FREE
        }
    
    async def check_claim(
        self,
        claim: str,
        strategy: str = 'balanced',
        include_detailed_breakdown: bool = False,
        max_providers: int = 20
    ) -> VerityResponse:
        """
        The main entry point - check a claim.
        
        strategy: 'speed', 'accuracy', 'balanced', 'comprehensive'
        """
        start_time = datetime.now()
        
        # Check cache first
        cached = self.learning_system.get_cached_verdict(claim)
        if cached and not include_detailed_breakdown:
            return self._format_cached_response(cached, start_time)
        
        # Step 1: Decompose the claim
        sub_claims = self.decomposer.decompose(claim)
        
        # Step 2: Route to providers
        primary_type = sub_claims[0].claim_type if sub_claims else ClaimType.GENERAL
        provider_plan = self.router.route(claim, primary_type, strategy)
        
        # Apply learning-based adjustments
        learned_weights = self.learning_system.get_provider_weights(primary_type)
        if learned_weights:
            self._apply_learned_weights(provider_plan, learned_weights)
        
        # Step 3: Query providers in parallel
        all_results, all_evidence = await self._query_all_providers(
            claim, sub_claims, provider_plan, max_providers
        )
        
        # Step 4: Build evidence graph
        graph = EvidenceGraphBuilder()
        claim_id = graph.add_claim(claim, sub_claims)
        for evidence in all_evidence:
            graph.add_evidence(evidence, claim_id)
        
        network_strength = graph.calculate_evidence_network_strength(claim_id)
        
        # Step 5: Run consensus engine
        consensus = await self.consensus_engine.build_consensus(
            claim, sub_claims, all_results, all_evidence
        )
        
        # Step 6: Calculate final confidence
        final_confidence = self.confidence_calculator.calculate(
            ai_agreement=self._calculate_ai_agreement(all_results),
            source_credibility=self._calculate_source_credibility(all_evidence),
            evidence_strength=network_strength.get('network_confidence', 0.5),
            consensus_score=consensus.confidence_score
        )
        
        # Apply calibration from learning
        calibrated_confidence = self.learning_system.get_calibration_adjustment(
            final_confidence
        )
        
        # Step 7: Cache the result
        self.learning_system.cache_verdict(
            claim,
            consensus.verdict,
            calibrated_confidence,
            len(all_evidence)
        )
        
        # Step 8: Format response
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        response = VerityResponse(
            claim=claim,
            verdict=consensus.verdict.value,
            verdict_emoji=self.VERDICT_EMOJIS.get(consensus.verdict, "❓"),
            confidence_score=calibrated_confidence,
            confidence_display=self._format_confidence(calibrated_confidence),
            summary=self._generate_summary(consensus, all_evidence),
            evidence_for=[self._format_evidence(e) for e in consensus.evidence_for[:10]],
            evidence_against=[self._format_evidence(e) for e in consensus.evidence_against[:10]],
            sources=consensus.sources_cited[:20],
            warnings=consensus.warnings,
            alternative_perspectives=consensus.alternative_perspectives,
            processing_time_ms=processing_time,
            providers_consulted=len(all_results),
            sub_claims_analyzed=len(sub_claims),
            reasoning_chain=consensus.reasoning_chain
        )
        
        if include_detailed_breakdown:
            response.detailed_breakdown = {
                'sub_claims': [asdict(sc) for sc in sub_claims],
                'provider_results': [
                    {'provider': r.provider_name, 'verdict': r.verdict.value if r.verdict else None}
                    for r in all_results
                ],
                'evidence_graph': graph.export_graph(),
                'network_strength': network_strength,
                'confidence_breakdown': self.confidence_calculator.get_confidence_breakdown(
                    self._calculate_ai_agreement(all_results),
                    self._calculate_source_credibility(all_evidence),
                    network_strength.get('network_confidence', 0.5),
                    consensus.confidence_score
                ),
                'learning_summary': self.learning_system.get_learning_summary()
            }
        
        return response
    
    async def _query_all_providers(
        self,
        claim: str,
        sub_claims: List[SubClaim],
        provider_plan: Dict,
        max_providers: int
    ) -> tuple[List[ProviderResult], List[Evidence]]:
        """Query all providers in parallel"""
        tasks = []
        all_results = []
        all_evidence = []
        
        async with aiohttp.ClientSession() as session:
            # Query AI providers
            ai_providers_to_use = list(self.ai_providers.items())[:max_providers // 3]
            for name, provider in ai_providers_to_use:
                tasks.append(self._query_ai_provider(name, provider, claim, session))
            
            # Query search providers
            search_providers_to_use = list(self.search_providers.items())[:max_providers // 3]
            for name, provider in search_providers_to_use:
                tasks.append(self._query_search_provider(name, provider, claim, session))
            
            # Query knowledge providers
            knowledge_providers_to_use = list(self.knowledge_providers.items())[:max_providers // 3]
            for name, provider in knowledge_providers_to_use:
                tasks.append(self._query_knowledge_provider(name, provider, claim, session))
            
            # Query fact-check providers
            for name, provider in self.factcheck_providers.items():
                tasks.append(self._query_factcheck_provider(name, provider, claim, session))
            
            # Execute all in parallel with timeout
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, Exception):
                    continue
                if isinstance(result, ProviderResult):
                    all_results.append(result)
                elif isinstance(result, list):
                    for item in result:
                        if isinstance(item, Evidence):
                            all_evidence.append(item)
                        elif isinstance(item, ProviderResult):
                            all_results.append(item)
        
        return all_results, all_evidence
    
    async def _query_ai_provider(
        self, name: str, provider, claim: str, session: aiohttp.ClientSession
    ) -> ProviderResult:
        """Query an AI provider"""
        start = datetime.now()
        try:
            result = await provider.verify_claim(claim, session)
            response_time = (datetime.now() - start).total_seconds() * 1000
            
            verdict = self._parse_verdict(result.get('verdict', ''))
            confidence = result.get('confidence', 0.5)
            
            return ProviderResult(
                provider_name=name,
                verdict=verdict,
                confidence=confidence,
                reasoning=result.get('reasoning', ''),
                evidence=[],
                response_time_ms=response_time,
                raw_response=result
            )
        except Exception as e:
            return ProviderResult(
                provider_name=name,
                verdict=None,
                confidence=0.0,
                reasoning=f"Error: {str(e)}",
                evidence=[],
                response_time_ms=(datetime.now() - start).total_seconds() * 1000,
                raw_response={'error': str(e)}
            )
    
    async def _query_search_provider(
        self, name: str, provider, claim: str, session: aiohttp.ClientSession
    ) -> List[Evidence]:
        """Query a search provider"""
        try:
            results = await provider.search(claim, session)
            evidence_list = []
            
            for r in results[:5]:
                source = r.get('source', r.get('url', 'Unknown'))
                evidence_list.append(Evidence(
                    source=source,
                    content=r.get('content', r.get('snippet', '')),
                    url=r.get('url', ''),
                    timestamp=datetime.now(),
                    confidence=r.get('relevance', 0.6),
                    source_tier=get_source_tier(source),
                    supports_claim=True  # Search results are neutral
                ))
            
            return evidence_list
        except Exception:
            return []
    
    async def _query_knowledge_provider(
        self, name: str, provider, claim: str, session: aiohttp.ClientSession
    ) -> List[Evidence]:
        """Query a knowledge provider"""
        try:
            results = await provider.query(claim, session)
            evidence_list = []
            
            for r in results[:3]:
                evidence_list.append(Evidence(
                    source=r.get('source', name),
                    content=r.get('abstract', r.get('content', '')),
                    url=r.get('url', ''),
                    timestamp=datetime.now(),
                    confidence=0.8,  # Academic sources are high confidence
                    source_tier=SourceTier.TIER_1_AUTHORITATIVE,
                    supports_claim=True
                ))
            
            return evidence_list
        except Exception:
            return []
    
    async def _query_factcheck_provider(
        self, name: str, provider, claim: str, session: aiohttp.ClientSession
    ) -> List[ProviderResult]:
        """Query a fact-check provider"""
        try:
            results = await provider.check(claim, session)
            provider_results = []
            
            for r in results[:2]:
                verdict = self._parse_verdict(r.get('rating', ''))
                provider_results.append(ProviderResult(
                    provider_name=f"{name}_{r.get('source', 'check')}",
                    verdict=verdict,
                    confidence=0.85,  # Fact-check orgs are reliable
                    reasoning=r.get('title', ''),
                    evidence=[],
                    response_time_ms=0,
                    raw_response=r
                ))
            
            return provider_results
        except Exception:
            return []
    
    def _parse_verdict(self, verdict_str: str) -> Optional[Verdict]:
        """Parse verdict from string"""
        verdict_lower = verdict_str.lower()
        
        if any(w in verdict_lower for w in ['true', 'correct', 'accurate', 'verified']):
            return Verdict.TRUE
        elif any(w in verdict_lower for w in ['false', 'incorrect', 'wrong', 'fake']):
            return Verdict.FALSE
        elif any(w in verdict_lower for w in ['partial', 'mostly', 'half']):
            return Verdict.PARTIALLY_TRUE
        elif any(w in verdict_lower for w in ['misleading', 'deceiving', 'out of context']):
            return Verdict.MISLEADING
        elif any(w in verdict_lower for w in ['unverified', 'unverifiable', 'cannot']):
            return Verdict.UNVERIFIABLE
        elif any(w in verdict_lower for w in ['disputed', 'contested', 'debate']):
            return Verdict.DISPUTED
        elif any(w in verdict_lower for w in ['context', 'nuance', 'depends']):
            return Verdict.NEEDS_CONTEXT
        elif any(w in verdict_lower for w in ['outdated', 'old', 'was true']):
            return Verdict.OUTDATED
        
        return None
    
    def _calculate_ai_agreement(self, results: List[ProviderResult]) -> float:
        """Calculate agreement between AI providers"""
        verdicts = [r.verdict for r in results if r.verdict is not None]
        if not verdicts:
            return 0.5
        
        # Count TRUE-ish vs FALSE-ish
        true_count = sum(1 for v in verdicts if v in [Verdict.TRUE, Verdict.PARTIALLY_TRUE])
        false_count = sum(1 for v in verdicts if v in [Verdict.FALSE, Verdict.MISLEADING])
        
        total = true_count + false_count
        if total == 0:
            return 0.5
        
        return max(true_count, false_count) / total
    
    def _calculate_source_credibility(self, evidence: List[Evidence]) -> float:
        """Calculate average source credibility"""
        if not evidence:
            return 0.5
        
        tier_scores = {
            SourceTier.TIER_1_AUTHORITATIVE: 1.0,
            SourceTier.TIER_2_REPUTABLE: 0.75,
            SourceTier.TIER_3_GENERAL: 0.5,
            SourceTier.TIER_4_UNCERTAIN: 0.25,
        }
        
        scores = [tier_scores.get(e.source_tier, 0.5) for e in evidence]
        return sum(scores) / len(scores)
    
    def _apply_learned_weights(self, provider_plan: Dict, learned_weights: Dict):
        """Apply learned weights to provider plan"""
        for category in ['ai', 'search', 'knowledge', 'factcheck']:
            if category in provider_plan:
                for provider in provider_plan[category]:
                    if provider in learned_weights:
                        provider_plan[category][provider] = learned_weights[provider]
    
    def _format_confidence(self, score: float) -> str:
        """Format confidence score for display"""
        percentage = round(score * 100)
        
        if percentage >= 90:
            return f"{percentage}% (Very High Confidence)"
        elif percentage >= 75:
            return f"{percentage}% (High Confidence)"
        elif percentage >= 60:
            return f"{percentage}% (Moderate Confidence)"
        elif percentage >= 40:
            return f"{percentage}% (Low Confidence)"
        else:
            return f"{percentage}% (Very Low Confidence)"
    
    def _generate_summary(self, consensus: ConsensusResult, evidence: List[Evidence]) -> str:
        """Generate human-readable summary"""
        verdict_descriptions = {
            Verdict.TRUE: "Our analysis indicates this claim is TRUE",
            Verdict.FALSE: "Our analysis indicates this claim is FALSE",
            Verdict.PARTIALLY_TRUE: "This claim is PARTIALLY TRUE",
            Verdict.MISLEADING: "This claim is MISLEADING",
            Verdict.UNVERIFIABLE: "This claim cannot be verified",
            Verdict.DISPUTED: "This claim is actively DISPUTED",
            Verdict.NEEDS_CONTEXT: "This claim NEEDS CONTEXT for accuracy",
            Verdict.OUTDATED: "This claim may be OUTDATED",
        }
        
        base = verdict_descriptions.get(
            consensus.verdict, 
            "Our analysis is inconclusive"
        )
        
        evidence_count = len(consensus.evidence_for) + len(consensus.evidence_against)
        base += f". Based on {evidence_count} pieces of evidence"
        base += f" from {len(consensus.sources_cited)} sources."
        
        return base
    
    def _format_evidence(self, evidence: Evidence) -> Dict:
        """Format evidence for response"""
        return {
            'source': evidence.source,
            'content': evidence.content[:300],
            'url': evidence.url,
            'tier': evidence.source_tier.name,
            'confidence': evidence.confidence
        }
    
    def _format_cached_response(
        self, cached, start_time: datetime
    ) -> VerityResponse:
        """Format a cached response"""
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        verdict = cached.verdict
        return VerityResponse(
            claim=cached.original_claim,
            verdict=verdict.value,
            verdict_emoji=self.VERDICT_EMOJIS.get(verdict, "❓"),
            confidence_score=cached.confidence,
            confidence_display=self._format_confidence(cached.confidence),
            summary=f"Cached result from {cached.timestamp.strftime('%Y-%m-%d')}",
            evidence_for=[],
            evidence_against=[],
            sources=[],
            warnings=["This is a cached result. Request fresh analysis for updated information."],
            alternative_perspectives=[],
            processing_time_ms=processing_time,
            providers_consulted=0,
            sub_claims_analyzed=0,
            reasoning_chain=["Returned from cache"]
        )
    
    async def provide_feedback(
        self,
        claim: str,
        user_verdict: Verdict,
        notes: str = ""
    ):
        """Allow users to provide feedback on verdicts"""
        cached = self.learning_system.get_cached_verdict(claim)
        if cached:
            self.learning_system.record_feedback(
                claim,
                cached.verdict,
                user_verdict,
                cached.confidence,
                notes
            )
    
    def get_system_stats(self) -> Dict:
        """Get system statistics"""
        return {
            'active_ai_providers': len(self.ai_providers),
            'active_search_providers': len(self.search_providers),
            'active_knowledge_providers': len(self.knowledge_providers),
            'active_factcheck_providers': len(self.factcheck_providers),
            'total_providers': (
                len(self.ai_providers) + len(self.search_providers) +
                len(self.knowledge_providers) + len(self.factcheck_providers)
            ),
            'learning_summary': self.learning_system.get_learning_summary()
        }


# Convenience function for quick checking
async def verify_claim(claim: str, api_keys: Dict[str, str] = None) -> VerityResponse:
    """Quick claim verification"""
    orchestrator = VerityMasterOrchestrator(api_keys or {})
    return await orchestrator.check_claim(claim)


__all__ = ['VerityMasterOrchestrator', 'VerityResponse', 'verify_claim']
