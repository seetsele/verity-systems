"""
Verity Intelligence Engine - Part 1: Core Architecture
========================================================
The BRAIN of the fact-checking system.

This is our TRADE SECRET - the proprietary algorithm that makes Verity
superior to any other fact-checking system in existence.

ARCHITECTURE OVERVIEW:
┌─────────────────────────────────────────────────────────────────────┐
│                    VERITY INTELLIGENCE ENGINE                       │
├─────────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐             │
│  │   CLAIM     │───▶│   CLAIM     │───▶│  PROVIDER   │             │
│  │   INPUT     │    │ DECOMPOSER  │    │   ROUTER    │             │
│  └─────────────┘    └─────────────┘    └──────┬──────┘             │
│                                               │                     │
│  ┌────────────────────────────────────────────▼────────────────┐   │
│  │                   PARALLEL QUERY ENGINE                      │   │
│  │  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐     │   │
│  │  │Claude│ │GPT-4 │ │Gemini│ │Llama │ │Mistral│ │50+more│    │   │
│  │  └──────┘ └──────┘ └──────┘ └──────┘ └──────┘ └──────┘     │   │
│  └────────────────────────────────────────────┬────────────────┘   │
│                                               │                     │
│  ┌────────────────────────────────────────────▼────────────────┐   │
│  │               EVIDENCE AGGREGATION LAYER                     │   │
│  │  • Source Credibility Scoring                                │   │
│  │  • Evidence Correlation Analysis                             │   │
│  │  • Contradiction Detection                                   │   │
│  └────────────────────────────────────────────┬────────────────┘   │
│                                               │                     │
│  ┌────────────────────────────────────────────▼────────────────┐   │
│  │               CONSENSUS ENGINE (7-Layer)                     │   │
│  │  Layer 1: AI Model Voting                                    │   │
│  │  Layer 2: Source Authority Weighting                         │   │
│  │  Layer 3: Evidence Strength Analysis                         │   │
│  │  Layer 4: Temporal Consistency Check                         │   │
│  │  Layer 5: Cross-Reference Validation                         │   │
│  │  Layer 6: Confidence Calibration                             │   │
│  │  Layer 7: Final Verdict Synthesis                            │   │
│  └────────────────────────────────────────────┬────────────────┘   │
│                                               │                     │
│  ┌────────────────────────────────────────────▼────────────────┐   │
│  │                 OUTPUT GENERATOR                             │   │
│  │  • Verdict + Confidence Score                                │   │
│  │  • Reasoning Chain                                           │   │
│  │  • Evidence Citations                                        │   │
│  │  • Alternative Perspectives                                  │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
"""

import os
import json
import asyncio
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod
import re
from collections import defaultdict
import statistics
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger('VerityIntelligenceEngine')


# ============================================================
# ENUMS AND DATA STRUCTURES
# ============================================================

class Verdict(Enum):
    """Possible verification verdicts"""
    TRUE = "TRUE"
    FALSE = "FALSE"
    PARTIALLY_TRUE = "PARTIALLY_TRUE"
    MISLEADING = "MISLEADING"
    UNVERIFIABLE = "UNVERIFIABLE"
    DISPUTED = "DISPUTED"
    OUTDATED = "OUTDATED"
    NEEDS_CONTEXT = "NEEDS_CONTEXT"


class ClaimType(Enum):
    """Types of claims for specialized routing"""
    SCIENTIFIC = "scientific"
    HISTORICAL = "historical"
    STATISTICAL = "statistical"
    POLITICAL = "political"
    MEDICAL = "medical"
    FINANCIAL = "financial"
    GEOGRAPHIC = "geographic"
    TECHNOLOGICAL = "technological"
    SOCIAL = "social"
    GENERAL = "general"


class SourceTier(Enum):
    """Source credibility tiers"""
    TIER_1_AUTHORITATIVE = 1  # Peer-reviewed, government, established fact-checkers
    TIER_2_REPUTABLE = 2       # Major news outlets, educational institutions
    TIER_3_GENERAL = 3         # Wikipedia, common resources
    TIER_4_UNCERTAIN = 4       # Social media, blogs, forums


@dataclass
class Evidence:
    """A piece of evidence supporting or refuting a claim"""
    source: str
    source_tier: SourceTier
    content: str
    url: Optional[str]
    supports_claim: bool  # True = supports, False = refutes
    confidence: float  # 0.0 to 1.0
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict = field(default_factory=dict)


@dataclass
class SubClaim:
    """A decomposed sub-claim from the main claim"""
    text: str
    claim_type: ClaimType
    is_verifiable: bool
    requires_sources: List[str]  # Types of sources needed
    priority: int  # 1-5, higher = more important


@dataclass  
class ProviderResult:
    """Result from a single provider"""
    provider_name: str
    verdict: Optional[Verdict]
    confidence: float
    evidence: List[Evidence]
    reasoning: str
    processing_time_ms: float
    raw_response: Dict


@dataclass
class ConsensusResult:
    """Final consensus result from the engine"""
    claim: str
    verdict: Verdict
    confidence_score: float  # 0.0 to 1.0
    sub_claims: List[SubClaim]
    provider_results: List[ProviderResult]
    evidence_for: List[Evidence]
    evidence_against: List[Evidence]
    reasoning_chain: List[str]
    sources_cited: List[Dict]
    warnings: List[str]
    alternative_perspectives: List[str]
    timestamp: datetime = field(default_factory=datetime.now)
    processing_time_ms: float = 0.0
    request_id: str = ""
    
    def to_dict(self) -> Dict:
        return {
            'claim': self.claim,
            'verdict': self.verdict.value,
            'confidence_score': round(self.confidence_score, 4),
            'confidence_percent': f"{self.confidence_score * 100:.1f}%",
            'sub_claims': [
                {
                    'text': sc.text,
                    'type': sc.claim_type.value,
                    'verifiable': sc.is_verifiable
                } for sc in self.sub_claims
            ],
            'provider_results': [
                {
                    'provider': pr.provider_name,
                    'verdict': pr.verdict.value if pr.verdict else None,
                    'confidence': pr.confidence
                } for pr in self.provider_results
            ],
            'evidence': {
                'supporting': [
                    {
                        'source': e.source,
                        'tier': e.source_tier.name,
                        'content': e.content[:500],
                        'url': e.url
                    } for e in self.evidence_for[:10]
                ],
                'refuting': [
                    {
                        'source': e.source,
                        'tier': e.source_tier.name,
                        'content': e.content[:500],
                        'url': e.url
                    } for e in self.evidence_against[:10]
                ]
            },
            'reasoning': self.reasoning_chain,
            'sources': self.sources_cited[:20],
            'warnings': self.warnings,
            'alternative_perspectives': self.alternative_perspectives,
            'metadata': {
                'timestamp': self.timestamp.isoformat(),
                'processing_time_ms': self.processing_time_ms,
                'request_id': self.request_id
            }
        }


# ============================================================
# SOURCE CREDIBILITY DATABASE
# ============================================================

SOURCE_CREDIBILITY = {
    # Tier 1: Authoritative (40 points)
    'peer_reviewed': SourceTier.TIER_1_AUTHORITATIVE,
    'nature.com': SourceTier.TIER_1_AUTHORITATIVE,
    'science.org': SourceTier.TIER_1_AUTHORITATIVE,
    'nejm.org': SourceTier.TIER_1_AUTHORITATIVE,
    'thelancet.com': SourceTier.TIER_1_AUTHORITATIVE,
    'nasa.gov': SourceTier.TIER_1_AUTHORITATIVE,
    'cdc.gov': SourceTier.TIER_1_AUTHORITATIVE,
    'who.int': SourceTier.TIER_1_AUTHORITATIVE,
    'nih.gov': SourceTier.TIER_1_AUTHORITATIVE,
    'usgs.gov': SourceTier.TIER_1_AUTHORITATIVE,
    'noaa.gov': SourceTier.TIER_1_AUTHORITATIVE,
    'semanticscholar.org': SourceTier.TIER_1_AUTHORITATIVE,
    'pubmed.ncbi.nlm.nih.gov': SourceTier.TIER_1_AUTHORITATIVE,
    'arxiv.org': SourceTier.TIER_1_AUTHORITATIVE,
    'snopes.com': SourceTier.TIER_1_AUTHORITATIVE,
    'politifact.com': SourceTier.TIER_1_AUTHORITATIVE,
    'factcheck.org': SourceTier.TIER_1_AUTHORITATIVE,
    'fullfact.org': SourceTier.TIER_1_AUTHORITATIVE,
    'apnews.com': SourceTier.TIER_1_AUTHORITATIVE,
    'reuters.com': SourceTier.TIER_1_AUTHORITATIVE,
    
    # Tier 2: Reputable (20 points)
    'bbc.com': SourceTier.TIER_2_REPUTABLE,
    'nytimes.com': SourceTier.TIER_2_REPUTABLE,
    'washingtonpost.com': SourceTier.TIER_2_REPUTABLE,
    'theguardian.com': SourceTier.TIER_2_REPUTABLE,
    'npr.org': SourceTier.TIER_2_REPUTABLE,
    'pbs.org': SourceTier.TIER_2_REPUTABLE,
    'britannica.com': SourceTier.TIER_2_REPUTABLE,
    'nationalgeographic.com': SourceTier.TIER_2_REPUTABLE,
    'smithsonianmag.com': SourceTier.TIER_2_REPUTABLE,
    'stanford.edu': SourceTier.TIER_2_REPUTABLE,
    'mit.edu': SourceTier.TIER_2_REPUTABLE,
    'harvard.edu': SourceTier.TIER_2_REPUTABLE,
    'oxford.ac.uk': SourceTier.TIER_2_REPUTABLE,
    'cambridge.org': SourceTier.TIER_2_REPUTABLE,
    
    # Tier 3: General (10 points)
    'wikipedia.org': SourceTier.TIER_3_GENERAL,
    'wikidata.org': SourceTier.TIER_3_GENERAL,
    'dbpedia.org': SourceTier.TIER_3_GENERAL,
    'wolframalpha.com': SourceTier.TIER_3_GENERAL,
    'khanacademy.org': SourceTier.TIER_3_GENERAL,
    
    # Tier 4: Uncertain (5 points)
    'twitter.com': SourceTier.TIER_4_UNCERTAIN,
    'facebook.com': SourceTier.TIER_4_UNCERTAIN,
    'reddit.com': SourceTier.TIER_4_UNCERTAIN,
    'quora.com': SourceTier.TIER_4_UNCERTAIN,
}


def get_source_tier(url: str) -> SourceTier:
    """Determine the credibility tier of a source"""
    if not url:
        return SourceTier.TIER_4_UNCERTAIN
    
    url_lower = url.lower()
    for domain, tier in SOURCE_CREDIBILITY.items():
        if domain in url_lower:
            return tier
    
    # Check for academic domains
    if any(domain in url_lower for domain in ['.edu', '.ac.uk', '.gov']):
        return SourceTier.TIER_2_REPUTABLE
    
    return SourceTier.TIER_3_GENERAL


def get_tier_weight(tier: SourceTier) -> float:
    """Get the weight multiplier for a source tier"""
    weights = {
        SourceTier.TIER_1_AUTHORITATIVE: 1.0,
        SourceTier.TIER_2_REPUTABLE: 0.7,
        SourceTier.TIER_3_GENERAL: 0.4,
        SourceTier.TIER_4_UNCERTAIN: 0.15,
    }
    return weights.get(tier, 0.2)


# ============================================================
# CLAIM DECOMPOSER
# ============================================================

class ClaimDecomposer:
    """
    Breaks down complex claims into verifiable sub-claims.
    
    This is CRITICAL for accuracy - complex claims often contain
    multiple assertions that need individual verification.
    
    Example:
    "The Earth is 4.5 billion years old and orbits the Sun at 67,000 mph"
    
    Decomposes to:
    1. "The Earth is approximately 4.5 billion years old" (scientific)
    2. "The Earth orbits the Sun" (scientific)
    3. "The Earth's orbital speed is approximately 67,000 mph" (scientific/statistical)
    """
    
    # Claim type indicators
    CLAIM_TYPE_PATTERNS = {
        ClaimType.SCIENTIFIC: [
            r'\b(study|research|scientist|experiment|data|evidence|theory)\b',
            r'\b(biology|physics|chemistry|astronomy|geology)\b',
            r'\b(evolution|climate|species|atom|molecule)\b',
        ],
        ClaimType.MEDICAL: [
            r'\b(health|disease|treatment|vaccine|medicine|drug|doctor)\b',
            r'\b(symptom|diagnosis|cure|therapy|hospital|patient)\b',
            r'\b(cancer|diabetes|heart|brain|virus|bacteria)\b',
        ],
        ClaimType.HISTORICAL: [
            r'\b(history|historical|century|decade|year|era|period)\b',
            r'\b(war|battle|revolution|empire|kingdom|civilization)\b',
            r'\b(ancient|medieval|modern|founded|discovered|invented)\b',
        ],
        ClaimType.STATISTICAL: [
            r'\b(\d+%|\d+ percent|percentage|rate|ratio|average)\b',
            r'\b(million|billion|trillion|thousand)\b',
            r'\b(statistic|survey|poll|census|data)\b',
        ],
        ClaimType.POLITICAL: [
            r'\b(government|president|congress|senate|law|policy)\b',
            r'\b(democrat|republican|election|vote|campaign)\b',
            r'\b(political|politician|legislation|bill|act)\b',
        ],
        ClaimType.FINANCIAL: [
            r'\b(money|dollar|price|cost|economy|market|stock)\b',
            r'\b(tax|revenue|profit|loss|investment|budget)\b',
            r'\b(gdp|inflation|unemployment|interest rate)\b',
        ],
        ClaimType.GEOGRAPHIC: [
            r'\b(country|city|state|continent|ocean|mountain|river)\b',
            r'\b(population|capital|border|territory|region)\b',
            r'\b(north|south|east|west|latitude|longitude)\b',
        ],
    }
    
    # Connectors that often separate sub-claims
    CLAIM_SEPARATORS = [
        r'\band\b',
        r'\bwhile\b',
        r'\bwhereas\b',
        r'\bbut\b',
        r'\bhowever\b',
        r'\balthough\b',
        r'\b,\s*which\b',
        r'\b,\s*and\b',
    ]
    
    def decompose(self, claim: str) -> List[SubClaim]:
        """Decompose a claim into verifiable sub-claims"""
        sub_claims = []
        
        # Try to split on natural separators
        parts = self._split_claim(claim)
        
        for part in parts:
            part = part.strip()
            if len(part) < 10:  # Too short to be meaningful
                continue
            
            claim_type = self._identify_claim_type(part)
            is_verifiable = self._is_verifiable(part)
            required_sources = self._identify_required_sources(part, claim_type)
            priority = self._calculate_priority(part)
            
            sub_claims.append(SubClaim(
                text=part,
                claim_type=claim_type,
                is_verifiable=is_verifiable,
                requires_sources=required_sources,
                priority=priority
            ))
        
        # If no decomposition happened, treat the whole claim as one
        if not sub_claims:
            claim_type = self._identify_claim_type(claim)
            sub_claims.append(SubClaim(
                text=claim,
                claim_type=claim_type,
                is_verifiable=self._is_verifiable(claim),
                requires_sources=self._identify_required_sources(claim, claim_type),
                priority=5
            ))
        
        return sorted(sub_claims, key=lambda x: -x.priority)
    
    def _split_claim(self, claim: str) -> List[str]:
        """Split claim on natural language separators"""
        parts = [claim]
        
        for separator in self.CLAIM_SEPARATORS:
            new_parts = []
            for part in parts:
                split_parts = re.split(separator, part, flags=re.IGNORECASE)
                new_parts.extend(split_parts)
            parts = new_parts
        
        return [p.strip() for p in parts if p.strip()]
    
    def _identify_claim_type(self, claim: str) -> ClaimType:
        """Identify the type of claim"""
        claim_lower = claim.lower()
        type_scores = defaultdict(int)
        
        for claim_type, patterns in self.CLAIM_TYPE_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, claim_lower):
                    type_scores[claim_type] += 1
        
        if type_scores:
            return max(type_scores.keys(), key=lambda x: type_scores[x])
        return ClaimType.GENERAL
    
    def _is_verifiable(self, claim: str) -> bool:
        """Check if a claim is verifiable"""
        # Opinions and subjective statements are not verifiable
        opinion_indicators = [
            r'\b(i think|i believe|in my opinion|probably|maybe|might)\b',
            r'\b(best|worst|most beautiful|ugliest|greatest)\b',
            r'\b(should|ought to|must|need to)\b',
        ]
        
        claim_lower = claim.lower()
        for pattern in opinion_indicators:
            if re.search(pattern, claim_lower):
                return False
        
        # Check for factual indicators
        factual_indicators = [
            r'\b(is|are|was|were|has|have|had)\b',
            r'\b\d+\b',  # Contains numbers
            r'\b(percent|rate|million|billion)\b',
        ]
        
        for pattern in factual_indicators:
            if re.search(pattern, claim_lower):
                return True
        
        return True  # Default to verifiable
    
    def _identify_required_sources(self, claim: str, claim_type: ClaimType) -> List[str]:
        """Identify what types of sources are needed to verify this claim"""
        sources = []
        
        type_to_sources = {
            ClaimType.SCIENTIFIC: ['academic', 'ai_models', 'wikipedia'],
            ClaimType.MEDICAL: ['pubmed', 'medical_ai', 'fact_checkers'],
            ClaimType.HISTORICAL: ['wikipedia', 'academic', 'encyclopedias'],
            ClaimType.STATISTICAL: ['government', 'research', 'fact_checkers'],
            ClaimType.POLITICAL: ['fact_checkers', 'news', 'government'],
            ClaimType.FINANCIAL: ['financial_data', 'news', 'government'],
            ClaimType.GEOGRAPHIC: ['geographic', 'wikipedia', 'encyclopedias'],
            ClaimType.GENERAL: ['ai_models', 'search', 'wikipedia'],
        }
        
        return type_to_sources.get(claim_type, ['ai_models', 'search'])
    
    def _calculate_priority(self, claim: str) -> int:
        """Calculate verification priority (1-5)"""
        priority = 3  # Default
        
        # Higher priority for specific/quantifiable claims
        if re.search(r'\b\d+\b', claim):
            priority += 1
        
        # Higher priority for claims with strong assertions
        if re.search(r'\b(always|never|all|none|every|no one)\b', claim.lower()):
            priority += 1
        
        # Lower priority for vague claims
        if re.search(r'\b(some|many|often|sometimes|usually)\b', claim.lower()):
            priority -= 1
        
        return max(1, min(5, priority))


# ============================================================
# PROVIDER ROUTER
# ============================================================

class ProviderRouter:
    """
    Intelligently routes claims to the most appropriate providers
    based on claim type, provider specialization, and availability.
    
    This is a KEY COMPETITIVE ADVANTAGE - we don't just query all
    providers blindly, we strategically select the best ones for
    each claim type.
    """
    
    # Provider specializations
    PROVIDER_SPECIALIZATIONS = {
        # AI Models - which are best for what
        'anthropic': {
            'strengths': [ClaimType.SCIENTIFIC, ClaimType.GENERAL, ClaimType.POLITICAL],
            'reasoning_quality': 0.95,
            'speed': 'medium',
            'cost': 'medium'
        },
        'openai': {
            'strengths': [ClaimType.GENERAL, ClaimType.TECHNOLOGICAL, ClaimType.HISTORICAL],
            'reasoning_quality': 0.93,
            'speed': 'medium',
            'cost': 'high'
        },
        'gemini': {
            'strengths': [ClaimType.SCIENTIFIC, ClaimType.STATISTICAL, ClaimType.GENERAL],
            'reasoning_quality': 0.90,
            'speed': 'fast',
            'cost': 'free'
        },
        'groq': {
            'strengths': [ClaimType.GENERAL, ClaimType.TECHNOLOGICAL],
            'reasoning_quality': 0.85,
            'speed': 'ultra_fast',
            'cost': 'free'
        },
        'mistral': {
            'strengths': [ClaimType.SCIENTIFIC, ClaimType.GENERAL],
            'reasoning_quality': 0.88,
            'speed': 'fast',
            'cost': 'free'
        },
        'deepseek': {
            'strengths': [ClaimType.SCIENTIFIC, ClaimType.TECHNOLOGICAL],
            'reasoning_quality': 0.86,
            'speed': 'medium',
            'cost': 'free'
        },
        'cohere': {
            'strengths': [ClaimType.GENERAL],
            'reasoning_quality': 0.82,
            'speed': 'fast',
            'cost': 'free'
        },
        'together_ai': {
            'strengths': [ClaimType.GENERAL, ClaimType.SCIENTIFIC],
            'reasoning_quality': 0.84,
            'speed': 'medium',
            'cost': 'cheap'
        },
        'fireworks': {
            'strengths': [ClaimType.GENERAL],
            'reasoning_quality': 0.83,
            'speed': 'ultra_fast',
            'cost': 'cheap'
        },
        
        # Search Providers
        'tavily': {
            'strengths': [ClaimType.GENERAL, ClaimType.POLITICAL],
            'reasoning_quality': 0.70,
            'speed': 'fast',
            'cost': 'free'
        },
        'exa': {
            'strengths': [ClaimType.GENERAL, ClaimType.SCIENTIFIC],
            'reasoning_quality': 0.72,
            'speed': 'fast',
            'cost': 'free'
        },
        'brave': {
            'strengths': [ClaimType.GENERAL],
            'reasoning_quality': 0.68,
            'speed': 'fast',
            'cost': 'free'
        },
        
        # Academic Sources
        'semantic_scholar': {
            'strengths': [ClaimType.SCIENTIFIC, ClaimType.MEDICAL],
            'reasoning_quality': 0.90,
            'speed': 'medium',
            'cost': 'free'
        },
        'pubmed': {
            'strengths': [ClaimType.MEDICAL],
            'reasoning_quality': 0.95,
            'speed': 'medium',
            'cost': 'free'
        },
        'arxiv': {
            'strengths': [ClaimType.SCIENTIFIC, ClaimType.TECHNOLOGICAL],
            'reasoning_quality': 0.88,
            'speed': 'medium',
            'cost': 'free'
        },
        'crossref': {
            'strengths': [ClaimType.SCIENTIFIC],
            'reasoning_quality': 0.85,
            'speed': 'medium',
            'cost': 'free'
        },
        
        # Knowledge Bases
        'wikipedia': {
            'strengths': [ClaimType.HISTORICAL, ClaimType.GEOGRAPHIC, ClaimType.GENERAL],
            'reasoning_quality': 0.75,
            'speed': 'fast',
            'cost': 'free'
        },
        'wikidata': {
            'strengths': [ClaimType.GENERAL, ClaimType.STATISTICAL],
            'reasoning_quality': 0.80,
            'speed': 'fast',
            'cost': 'free'
        },
        'wolfram': {
            'strengths': [ClaimType.SCIENTIFIC, ClaimType.STATISTICAL],
            'reasoning_quality': 0.98,
            'speed': 'medium',
            'cost': 'cheap'
        },
        'dbpedia': {
            'strengths': [ClaimType.GENERAL, ClaimType.HISTORICAL],
            'reasoning_quality': 0.78,
            'speed': 'fast',
            'cost': 'free'
        },
        
        # Fact-Checkers
        'google_factcheck': {
            'strengths': [ClaimType.POLITICAL, ClaimType.GENERAL],
            'reasoning_quality': 0.92,
            'speed': 'fast',
            'cost': 'free'
        },
        'claimbuster': {
            'strengths': [ClaimType.POLITICAL],
            'reasoning_quality': 0.85,
            'speed': 'medium',
            'cost': 'free'
        },
        
        # Geographic
        'geonames': {
            'strengths': [ClaimType.GEOGRAPHIC],
            'reasoning_quality': 0.90,
            'speed': 'fast',
            'cost': 'free'
        },
        
        # Financial
        'polygon': {
            'strengths': [ClaimType.FINANCIAL],
            'reasoning_quality': 0.92,
            'speed': 'fast',
            'cost': 'free'
        },
    }
    
    def route(
        self, 
        sub_claims: List[SubClaim],
        available_providers: List[str],
        strategy: str = 'balanced'  # 'speed', 'accuracy', 'balanced', 'comprehensive'
    ) -> Dict[str, List[str]]:
        """
        Route sub-claims to appropriate providers.
        
        Returns: Dict mapping provider names to list of sub-claim texts
        """
        routing = defaultdict(list)
        
        for sub_claim in sub_claims:
            # Get best providers for this claim type
            ranked_providers = self._rank_providers_for_claim(
                sub_claim, 
                available_providers,
                strategy
            )
            
            # Select top N providers based on strategy
            if strategy == 'speed':
                num_providers = 3
            elif strategy == 'accuracy':
                num_providers = 8
            elif strategy == 'comprehensive':
                num_providers = 15
            else:  # balanced
                num_providers = 5
            
            for provider in ranked_providers[:num_providers]:
                routing[provider].append(sub_claim.text)
        
        return dict(routing)
    
    def _rank_providers_for_claim(
        self, 
        sub_claim: SubClaim, 
        available: List[str],
        strategy: str
    ) -> List[str]:
        """Rank providers for a specific sub-claim"""
        scores = {}
        
        for provider in available:
            if provider not in self.PROVIDER_SPECIALIZATIONS:
                scores[provider] = 0.5  # Default score
                continue
            
            spec = self.PROVIDER_SPECIALIZATIONS[provider]
            score = 0.0
            
            # Base score from reasoning quality
            score += spec['reasoning_quality'] * 0.4
            
            # Bonus for specialization match
            if sub_claim.claim_type in spec['strengths']:
                score += 0.3
            
            # Strategy modifiers
            if strategy == 'speed':
                speed_bonus = {'ultra_fast': 0.3, 'fast': 0.2, 'medium': 0.1}
                score += speed_bonus.get(spec['speed'], 0)
            elif strategy == 'accuracy':
                score += spec['reasoning_quality'] * 0.2
            
            # Cost consideration (free/cheap providers get slight boost)
            cost_bonus = {'free': 0.1, 'cheap': 0.05}
            score += cost_bonus.get(spec['cost'], 0)
            
            scores[provider] = score
        
        # Sort by score
        return sorted(scores.keys(), key=lambda x: -scores[x])


# Export for use in other modules
__all__ = [
    'Verdict',
    'ClaimType', 
    'SourceTier',
    'Evidence',
    'SubClaim',
    'ProviderResult',
    'ConsensusResult',
    'ClaimDecomposer',
    'ProviderRouter',
    'get_source_tier',
    'get_tier_weight',
    'SOURCE_CREDIBILITY',
]
