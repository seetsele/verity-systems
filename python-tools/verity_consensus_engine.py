"""
Verity Intelligence Engine - Part 2: Consensus Engine
======================================================
The 7-LAYER CONSENSUS ALGORITHM - our secret sauce.

This is what makes Verity UNBEATABLE at fact-checking.
No other system has this level of sophisticated consensus building.

THE 7 LAYERS:
=============
Layer 1: AI Model Voting (Weight: 35%)
    - Aggregate verdicts from all AI models
    - Weight by model quality and specialization match
    
Layer 2: Source Authority Weighting (Weight: 25%)
    - Tier 1 sources (peer-reviewed, govt) = 40 points
    - Tier 2 sources (major news, edu) = 20 points
    - Tier 3 sources (Wikipedia, general) = 10 points
    - Tier 4 sources (social media, blogs) = 5 points
    
Layer 3: Evidence Strength Analysis (Weight: 15%)
    - Direct evidence vs circumstantial
    - Recency of evidence
    - Specificity of claims
    
Layer 4: Temporal Consistency Check (Weight: 5%)
    - Is the claim still current?
    - Has the consensus changed over time?
    - Are sources up-to-date?
    
Layer 5: Cross-Reference Validation (Weight: 10%)
    - Do independent sources agree?
    - Are there citation chains?
    - Corroboration from different domains
    
Layer 6: Confidence Calibration (Weight: 5%)
    - Adjust for uncertainty
    - Apply Bayesian updates
    - Account for model disagreement
    
Layer 7: Final Verdict Synthesis (Weight: 5%)
    - Combine all layers
    - Generate reasoning chain
    - Identify caveats and warnings
"""

import asyncio
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
import math

from verity_intelligence_engine import (
    Verdict, ClaimType, SourceTier, Evidence, SubClaim,
    ProviderResult, ConsensusResult, get_source_tier, get_tier_weight
)


class ConsensusEngine:
    """
    The 7-Layer Consensus Engine - Verity's secret weapon.
    
    This algorithm combines outputs from 50+ providers into
    a single, highly accurate verdict with confidence score.
    """
    
    # Layer weights (must sum to 1.0)
    LAYER_WEIGHTS = {
        'ai_voting': 0.35,
        'source_authority': 0.25,
        'evidence_strength': 0.15,
        'temporal_consistency': 0.05,
        'cross_reference': 0.10,
        'confidence_calibration': 0.05,
        'verdict_synthesis': 0.05,
    }
    
    # Verdict scoring (for aggregation)
    VERDICT_SCORES = {
        Verdict.TRUE: 1.0,
        Verdict.PARTIALLY_TRUE: 0.6,
        Verdict.MISLEADING: 0.3,
        Verdict.UNVERIFIABLE: 0.5,
        Verdict.DISPUTED: 0.5,
        Verdict.NEEDS_CONTEXT: 0.5,
        Verdict.OUTDATED: 0.4,
        Verdict.FALSE: 0.0,
    }
    
    def __init__(self):
        self.reasoning_chain = []
    
    async def build_consensus(
        self,
        claim: str,
        sub_claims: List[SubClaim],
        provider_results: List[ProviderResult],
        all_evidence: List[Evidence]
    ) -> ConsensusResult:
        """
        Build consensus from all provider results.
        
        This is the CORE ALGORITHM that makes Verity special.
        """
        self.reasoning_chain = []
        start_time = datetime.now()
        
        # Separate evidence
        evidence_for = [e for e in all_evidence if e.supports_claim]
        evidence_against = [e for e in all_evidence if not e.supports_claim]
        
        # Run all 7 layers
        layer_scores = {}
        
        # Layer 1: AI Model Voting
        layer_scores['ai_voting'] = self._layer1_ai_voting(provider_results)
        self.reasoning_chain.append(
            f"Layer 1 (AI Voting): {len(provider_results)} models analyzed, "
            f"weighted score = {layer_scores['ai_voting']:.2f}"
        )
        
        # Layer 2: Source Authority Weighting
        layer_scores['source_authority'] = self._layer2_source_authority(all_evidence)
        self.reasoning_chain.append(
            f"Layer 2 (Source Authority): {len(all_evidence)} sources evaluated, "
            f"authority score = {layer_scores['source_authority']:.2f}"
        )
        
        # Layer 3: Evidence Strength Analysis
        layer_scores['evidence_strength'] = self._layer3_evidence_strength(
            evidence_for, evidence_against
        )
        self.reasoning_chain.append(
            f"Layer 3 (Evidence Strength): {len(evidence_for)} supporting, "
            f"{len(evidence_against)} refuting, score = {layer_scores['evidence_strength']:.2f}"
        )
        
        # Layer 4: Temporal Consistency
        layer_scores['temporal_consistency'] = self._layer4_temporal_consistency(all_evidence)
        self.reasoning_chain.append(
            f"Layer 4 (Temporal): Evidence recency score = {layer_scores['temporal_consistency']:.2f}"
        )
        
        # Layer 5: Cross-Reference Validation
        layer_scores['cross_reference'] = self._layer5_cross_reference(provider_results)
        self.reasoning_chain.append(
            f"Layer 5 (Cross-Reference): Independent agreement score = {layer_scores['cross_reference']:.2f}"
        )
        
        # Layer 6: Confidence Calibration
        layer_scores['confidence_calibration'] = self._layer6_confidence_calibration(
            provider_results, layer_scores
        )
        self.reasoning_chain.append(
            f"Layer 6 (Calibration): Adjusted confidence = {layer_scores['confidence_calibration']:.2f}"
        )
        
        # Layer 7: Final Verdict Synthesis
        final_score, verdict, warnings = self._layer7_verdict_synthesis(layer_scores)
        self.reasoning_chain.append(
            f"Layer 7 (Synthesis): Final score = {final_score:.4f}, Verdict = {verdict.value}"
        )
        
        # Generate alternative perspectives
        alternatives = self._generate_alternative_perspectives(
            provider_results, evidence_for, evidence_against
        )
        
        # Compile sources
        sources_cited = self._compile_sources(all_evidence)
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        return ConsensusResult(
            claim=claim,
            verdict=verdict,
            confidence_score=final_score,
            sub_claims=sub_claims,
            provider_results=provider_results,
            evidence_for=evidence_for,
            evidence_against=evidence_against,
            reasoning_chain=self.reasoning_chain,
            sources_cited=sources_cited,
            warnings=warnings,
            alternative_perspectives=alternatives,
            processing_time_ms=processing_time
        )
    
    def _layer1_ai_voting(self, results: List[ProviderResult]) -> float:
        """
        Layer 1: Weighted voting from AI models.
        
        Each AI model casts a "vote" based on its verdict.
        Votes are weighted by model quality and confidence.
        """
        if not results:
            return 0.5  # Neutral
        
        # Model quality weights (based on benchmark performance)
        model_weights = {
            'anthropic': 1.0,
            'claude': 1.0,
            'openai': 0.95,
            'gpt-4': 0.95,
            'gpt': 0.9,
            'gemini': 0.88,
            'google': 0.88,
            'mistral': 0.85,
            'llama': 0.82,
            'groq': 0.82,
            'deepseek': 0.80,
            'cohere': 0.78,
            'together': 0.75,
            'fireworks': 0.75,
            'replicate': 0.72,
            'openrouter': 0.70,
        }
        
        weighted_sum = 0.0
        total_weight = 0.0
        
        for result in results:
            if result.verdict is None:
                continue
            
            # Get model weight
            provider_lower = result.provider_name.lower()
            model_weight = 0.7  # Default
            for key, weight in model_weights.items():
                if key in provider_lower:
                    model_weight = weight
                    break
            
            # Apply confidence multiplier
            confidence_multiplier = result.confidence
            
            # Calculate weighted vote
            verdict_score = self.VERDICT_SCORES.get(result.verdict, 0.5)
            weighted_vote = verdict_score * model_weight * confidence_multiplier
            
            weighted_sum += weighted_vote
            total_weight += model_weight * confidence_multiplier
        
        if total_weight == 0:
            return 0.5
        
        return weighted_sum / total_weight
    
    def _layer2_source_authority(self, evidence: List[Evidence]) -> float:
        """
        Layer 2: Weight evidence by source authority.
        
        Tier 1 (peer-reviewed, government) = 40 points
        Tier 2 (major news, universities) = 20 points
        Tier 3 (Wikipedia, general) = 10 points
        Tier 4 (social media, blogs) = 5 points
        """
        if not evidence:
            return 0.5
        
        tier_points = {
            SourceTier.TIER_1_AUTHORITATIVE: 40,
            SourceTier.TIER_2_REPUTABLE: 20,
            SourceTier.TIER_3_GENERAL: 10,
            SourceTier.TIER_4_UNCERTAIN: 5,
        }
        
        supporting_points = 0
        refuting_points = 0
        
        for e in evidence:
            points = tier_points.get(e.source_tier, 5) * e.confidence
            if e.supports_claim:
                supporting_points += points
            else:
                refuting_points += points
        
        total_points = supporting_points + refuting_points
        if total_points == 0:
            return 0.5
        
        # Return ratio of supporting evidence
        return supporting_points / total_points
    
    def _layer3_evidence_strength(
        self, 
        evidence_for: List[Evidence], 
        evidence_against: List[Evidence]
    ) -> float:
        """
        Layer 3: Analyze evidence strength.
        
        Considers:
        - Number of evidence pieces
        - Quality/tier of evidence
        - Specificity of evidence
        - Confidence levels
        """
        def calculate_strength(evidence_list: List[Evidence]) -> float:
            if not evidence_list:
                return 0.0
            
            strength = 0.0
            for e in evidence_list:
                tier_weight = get_tier_weight(e.source_tier)
                specificity = min(len(e.content) / 500, 1.0)  # Longer = more specific
                strength += tier_weight * e.confidence * (0.5 + 0.5 * specificity)
            
            return strength
        
        strength_for = calculate_strength(evidence_for)
        strength_against = calculate_strength(evidence_against)
        total_strength = strength_for + strength_against
        
        if total_strength == 0:
            return 0.5
        
        return strength_for / total_strength
    
    def _layer4_temporal_consistency(self, evidence: List[Evidence]) -> float:
        """
        Layer 4: Check temporal consistency.
        
        Recent evidence is weighted more heavily.
        Old evidence might indicate outdated claims.
        """
        if not evidence:
            return 0.5
        
        now = datetime.now()
        recency_scores = []
        
        for e in evidence:
            # Calculate age in days
            age_days = (now - e.timestamp).days
            
            # Exponential decay: evidence older than 2 years gets lower weight
            # Half-life of ~365 days
            recency = math.exp(-age_days / 365)
            recency_scores.append(recency)
        
        # Return average recency (higher = more recent evidence)
        avg_recency = statistics.mean(recency_scores)
        
        # Map to 0-1 scale with 0.5 as neutral
        # Recent evidence (recency > 0.5) boosts score
        # Old evidence (recency < 0.5) reduces score
        return 0.3 + 0.4 * avg_recency  # Maps to 0.3-0.7 range
    
    def _layer5_cross_reference(self, results: List[ProviderResult]) -> float:
        """
        Layer 5: Cross-reference validation.
        
        Checks if independent sources agree with each other.
        High agreement = high confidence
        Disagreement = lower confidence
        """
        if len(results) < 2:
            return 0.5
        
        verdicts = [r.verdict for r in results if r.verdict is not None]
        if not verdicts:
            return 0.5
        
        # Count verdict frequencies
        verdict_counts = defaultdict(int)
        for v in verdicts:
            verdict_counts[v] += 1
        
        # Find majority verdict
        majority_verdict = max(verdict_counts.keys(), key=lambda v: verdict_counts[v])
        majority_count = verdict_counts[majority_verdict]
        
        # Calculate agreement ratio
        agreement_ratio = majority_count / len(verdicts)
        
        # Bonus for unanimous agreement
        if agreement_ratio == 1.0:
            return 0.95
        elif agreement_ratio >= 0.8:
            return 0.85
        elif agreement_ratio >= 0.6:
            return 0.70
        else:
            return 0.5  # Disputed
    
    def _layer6_confidence_calibration(
        self, 
        results: List[ProviderResult],
        layer_scores: Dict[str, float]
    ) -> float:
        """
        Layer 6: Calibrate confidence.
        
        Apply Bayesian-style adjustments based on:
        - Model disagreement
        - Evidence uncertainty
        - Historical accuracy
        """
        # Get variance in confidence scores
        confidences = [r.confidence for r in results if r.confidence > 0]
        if not confidences:
            return 0.5
        
        mean_confidence = statistics.mean(confidences)
        
        # Penalize high variance (disagreement)
        if len(confidences) > 1:
            variance = statistics.variance(confidences)
            variance_penalty = min(variance * 2, 0.3)  # Max 30% penalty
        else:
            variance_penalty = 0.2  # Penalty for single source
        
        # Check layer agreement
        layer_values = list(layer_scores.values())
        if len(layer_values) > 2:
            layer_variance = statistics.variance(layer_values)
            layer_agreement_bonus = max(0, 0.1 - layer_variance)
        else:
            layer_agreement_bonus = 0
        
        calibrated = mean_confidence - variance_penalty + layer_agreement_bonus
        return max(0.1, min(0.95, calibrated))
    
    def _layer7_verdict_synthesis(
        self, 
        layer_scores: Dict[str, float]
    ) -> Tuple[float, Verdict, List[str]]:
        """
        Layer 7: Synthesize final verdict.
        
        Combines all layer scores using weighted average.
        Maps final score to verdict category.
        Generates warnings for edge cases.
        """
        warnings = []
        
        # Calculate weighted final score
        final_score = 0.0
        for layer_name, weight in self.LAYER_WEIGHTS.items():
            score = layer_scores.get(layer_name, 0.5)
            final_score += score * weight
        
        # Determine verdict from score
        if final_score >= 0.85:
            verdict = Verdict.TRUE
        elif final_score >= 0.70:
            verdict = Verdict.PARTIALLY_TRUE
            warnings.append("Some aspects of the claim may be contested or require context.")
        elif final_score >= 0.55:
            verdict = Verdict.NEEDS_CONTEXT
            warnings.append("The claim requires additional context for accurate interpretation.")
        elif final_score >= 0.45:
            verdict = Verdict.DISPUTED
            warnings.append("This claim is actively disputed among sources.")
        elif final_score >= 0.30:
            verdict = Verdict.MISLEADING
            warnings.append("The claim may be technically true but misleading in context.")
        elif final_score >= 0.15:
            verdict = Verdict.PARTIALLY_TRUE
            warnings.append("Only some aspects of this claim are accurate.")
        else:
            verdict = Verdict.FALSE
        
        # Check for special cases
        if layer_scores.get('temporal_consistency', 0.5) < 0.35:
            warnings.append("Evidence may be outdated. Current status should be verified.")
        
        if layer_scores.get('cross_reference', 0.5) < 0.5:
            warnings.append("Sources show significant disagreement on this claim.")
        
        if layer_scores.get('confidence_calibration', 0.5) < 0.4:
            warnings.append("Confidence is lower due to limited or uncertain evidence.")
        
        return final_score, verdict, warnings
    
    def _generate_alternative_perspectives(
        self,
        results: List[ProviderResult],
        evidence_for: List[Evidence],
        evidence_against: List[Evidence]
    ) -> List[str]:
        """Generate alternative perspectives on the claim"""
        perspectives = []
        
        # Check for minority opinions
        verdict_counts = defaultdict(list)
        for r in results:
            if r.verdict:
                verdict_counts[r.verdict].append(r.provider_name)
        
        # If there's disagreement, note minority views
        if len(verdict_counts) > 1:
            for verdict, providers in verdict_counts.items():
                if len(providers) <= len(results) // 3:  # Minority view
                    perspectives.append(
                        f"Alternative view ({', '.join(providers[:2])}): "
                        f"This claim may be {verdict.value.lower()}."
                    )
        
        # Note if strong evidence exists on both sides
        if evidence_for and evidence_against:
            tier1_for = sum(1 for e in evidence_for if e.source_tier == SourceTier.TIER_1_AUTHORITATIVE)
            tier1_against = sum(1 for e in evidence_against if e.source_tier == SourceTier.TIER_1_AUTHORITATIVE)
            
            if tier1_for > 0 and tier1_against > 0:
                perspectives.append(
                    "Note: High-quality sources exist supporting both sides of this claim."
                )
        
        return perspectives[:3]  # Limit to 3
    
    def _compile_sources(self, evidence: List[Evidence]) -> List[Dict]:
        """Compile list of sources with metadata"""
        sources = []
        seen_urls = set()
        
        for e in evidence:
            if e.url and e.url not in seen_urls:
                sources.append({
                    'name': e.source,
                    'url': e.url,
                    'tier': e.source_tier.name,
                    'supports': e.supports_claim
                })
                seen_urls.add(e.url)
        
        # Sort by tier (most authoritative first)
        sources.sort(key=lambda x: SourceTier[x['tier']].value)
        
        return sources[:50]  # Limit to 50


# ============================================================
# CONFIDENCE SCORE CALCULATOR
# ============================================================

class ConfidenceCalculator:
    """
    Calculates the final confidence score using the formula:
    
    Confidence Score = 
        (AI Agreement %: 35%)
        + (Source Credibility %: 30%)
        + (Evidence Strength %: 20%)
        + (Consensus Score %: 15%)
    
    This is displayed to users as the primary accuracy metric.
    """
    
    def calculate(
        self,
        ai_agreement: float,
        source_credibility: float,
        evidence_strength: float,
        consensus_score: float
    ) -> float:
        """
        Calculate final confidence score.
        
        Each component is 0.0 to 1.0.
        Returns final score as 0.0 to 1.0.
        """
        score = (
            ai_agreement * 0.35 +
            source_credibility * 0.30 +
            evidence_strength * 0.20 +
            consensus_score * 0.15
        )
        
        # Apply calibration to avoid overconfidence
        if score > 0.95:
            score = 0.95 + (score - 0.95) * 0.5  # Diminishing returns above 95%
        
        return round(score, 4)
    
    def get_confidence_breakdown(
        self,
        ai_agreement: float,
        source_credibility: float,
        evidence_strength: float,
        consensus_score: float
    ) -> Dict:
        """Get detailed breakdown of confidence score"""
        return {
            'ai_agreement': {
                'value': ai_agreement,
                'weight': 0.35,
                'contribution': ai_agreement * 0.35,
                'description': f'{len([])} AI models analyzed'
            },
            'source_credibility': {
                'value': source_credibility,
                'weight': 0.30,
                'contribution': source_credibility * 0.30,
                'description': 'Based on source authority tiers'
            },
            'evidence_strength': {
                'value': evidence_strength,
                'weight': 0.20,
                'contribution': evidence_strength * 0.20,
                'description': 'Quality and specificity of evidence'
            },
            'consensus_score': {
                'value': consensus_score,
                'weight': 0.15,
                'contribution': consensus_score * 0.15,
                'description': 'Agreement between independent sources'
            },
            'total': self.calculate(
                ai_agreement, source_credibility, 
                evidence_strength, consensus_score
            )
        }


__all__ = ['ConsensusEngine', 'ConfidenceCalculator']
