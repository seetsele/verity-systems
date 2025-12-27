"""
Verity Monte Carlo Confidence Engine
====================================
Advanced statistical methods for confidence estimation.

Uses Monte Carlo simulation to:
1. Generate confidence intervals
2. Account for source uncertainty
3. Model disagreement between providers
4. Produce calibrated probability estimates

This is ADVANCED STATISTICS for fact-checking.
"""

import random
import math
import statistics
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional
from enum import Enum


class VerdictCategory(Enum):
    TRUE = "true"
    FALSE = "false"
    MIXED = "mixed"
    UNKNOWN = "unknown"


@dataclass
class SourceEvidence:
    """Evidence from a single source"""
    source_name: str
    verdict: VerdictCategory
    confidence: float  # 0-1, how confident the source is
    credibility: float  # 0-1, how credible the source is
    weight: float = 1.0  # Additional weighting factor


@dataclass
class MonteCarloResult:
    """Result of Monte Carlo simulation"""
    verdict: VerdictCategory
    mean_confidence: float
    confidence_interval: Tuple[float, float]  # 95% CI
    probability_true: float
    probability_false: float
    probability_mixed: float
    simulation_count: int
    convergence_score: float  # How stable the result is


class MonteCarloConfidenceEngine:
    """
    Monte Carlo simulation for verdict confidence.
    
    This addresses the problem: "How confident should we be in our verdict
    when different sources have different levels of reliability?"
    
    Algorithm:
    1. Model each source as a probability distribution
    2. Sample from these distributions thousands of times
    3. Aggregate samples to get final probability distribution
    4. Extract confidence intervals
    """
    
    def __init__(self, simulations: int = 10000, seed: int = None):
        self.simulations = simulations
        if seed:
            random.seed(seed)
    
    def simulate(self, evidence: List[SourceEvidence]) -> MonteCarloResult:
        """
        Run Monte Carlo simulation on evidence
        
        For each simulation:
        1. Sample from each source's confidence distribution
        2. Weight by source credibility
        3. Aggregate to get verdict
        4. Record result
        
        After all simulations:
        - Calculate probability of each verdict
        - Generate confidence intervals
        """
        if not evidence:
            return MonteCarloResult(
                verdict=VerdictCategory.UNKNOWN,
                mean_confidence=0.0,
                confidence_interval=(0.0, 0.0),
                probability_true=0.0,
                probability_false=0.0,
                probability_mixed=0.0,
                simulation_count=0,
                convergence_score=0.0
            )
        
        # Run simulations
        true_scores = []
        false_scores = []
        
        for _ in range(self.simulations):
            sim_true_score = 0.0
            sim_false_score = 0.0
            total_weight = 0.0
            
            for src in evidence:
                # Sample from source's confidence distribution
                # Use Beta distribution for bounded [0,1] confidence
                sampled_confidence = self._sample_beta(src.confidence, 0.15)
                
                # Apply credibility and weight
                effective_weight = src.credibility * src.weight * sampled_confidence
                
                if src.verdict == VerdictCategory.TRUE:
                    sim_true_score += effective_weight
                elif src.verdict == VerdictCategory.FALSE:
                    sim_false_score += effective_weight
                elif src.verdict == VerdictCategory.MIXED:
                    # Mixed verdict contributes to both but less strongly
                    sim_true_score += effective_weight * 0.3
                    sim_false_score += effective_weight * 0.3
                
                total_weight += src.credibility * src.weight
            
            # Normalize
            if total_weight > 0:
                true_scores.append(sim_true_score / total_weight)
                false_scores.append(sim_false_score / total_weight)
            else:
                true_scores.append(0.5)
                false_scores.append(0.5)
        
        # Calculate probabilities
        prob_true = sum(1 for t, f in zip(true_scores, false_scores) if t > f and t > 0.5) / self.simulations
        prob_false = sum(1 for t, f in zip(true_scores, false_scores) if f > t and f > 0.5) / self.simulations
        prob_mixed = 1.0 - prob_true - prob_false
        
        # Determine verdict
        if prob_true > prob_false and prob_true > prob_mixed:
            verdict = VerdictCategory.TRUE
            scores = true_scores
        elif prob_false > prob_true and prob_false > prob_mixed:
            verdict = VerdictCategory.FALSE
            scores = false_scores
        else:
            verdict = VerdictCategory.MIXED
            scores = [(t + f) / 2 for t, f in zip(true_scores, false_scores)]
        
        # Calculate confidence interval (95%)
        scores_sorted = sorted(scores)
        ci_lower = scores_sorted[int(self.simulations * 0.025)]
        ci_upper = scores_sorted[int(self.simulations * 0.975)]
        
        # Mean confidence
        mean_conf = statistics.mean(scores)
        
        # Convergence score (inverse of coefficient of variation)
        if mean_conf > 0:
            std_dev = statistics.stdev(scores)
            cv = std_dev / mean_conf
            convergence = max(0, 1 - cv)
        else:
            convergence = 0.0
        
        return MonteCarloResult(
            verdict=verdict,
            mean_confidence=mean_conf,
            confidence_interval=(ci_lower, ci_upper),
            probability_true=prob_true,
            probability_false=prob_false,
            probability_mixed=prob_mixed,
            simulation_count=self.simulations,
            convergence_score=convergence
        )
    
    def _sample_beta(self, mean: float, spread: float) -> float:
        """
        Sample from a Beta distribution with given mean and spread.
        Beta is ideal for modeling probabilities (bounded 0-1).
        """
        # Clamp mean to valid range
        mean = max(0.01, min(0.99, mean))
        
        # Convert to alpha/beta parameters
        # Higher spread = more variance
        variance = spread * mean * (1 - mean)
        variance = min(variance, mean * (1 - mean) * 0.99)  # Ensure valid
        
        if variance <= 0:
            return mean
        
        # Method of moments
        common = mean * (1 - mean) / variance - 1
        alpha = mean * common
        beta = (1 - mean) * common
        
        # Ensure valid parameters
        alpha = max(0.1, alpha)
        beta = max(0.1, beta)
        
        return random.betavariate(alpha, beta)


class BayesianConfidenceUpdater:
    """
    Bayesian updating for confidence scores.
    
    As new evidence comes in, update our belief about the claim.
    Uses Bayes' theorem: P(H|E) = P(E|H) * P(H) / P(E)
    """
    
    def __init__(self, prior_true: float = 0.5):
        """
        Initialize with prior probability.
        Default 0.5 = no initial bias toward true or false.
        """
        self.prior_true = prior_true
        self.prior_false = 1 - prior_true
        self.evidence_history = []
    
    def update(self, evidence: SourceEvidence) -> Tuple[float, float]:
        """
        Update beliefs based on new evidence.
        
        Returns (P(true|evidence), P(false|evidence))
        """
        # Likelihood: P(evidence | hypothesis)
        # If source says TRUE:
        #   - If claim is actually true: high likelihood (based on credibility)
        #   - If claim is actually false: low likelihood
        
        if evidence.verdict == VerdictCategory.TRUE:
            # Likelihood of seeing "true" evidence if claim is actually true
            likelihood_true = evidence.credibility * evidence.confidence
            # Likelihood of seeing "true" evidence if claim is actually false (error)
            likelihood_false = (1 - evidence.credibility) * (1 - evidence.confidence)
        elif evidence.verdict == VerdictCategory.FALSE:
            likelihood_true = (1 - evidence.credibility) * (1 - evidence.confidence)
            likelihood_false = evidence.credibility * evidence.confidence
        else:  # MIXED or UNKNOWN
            likelihood_true = 0.5
            likelihood_false = 0.5
        
        # Ensure minimum likelihoods to avoid zeros
        likelihood_true = max(0.01, likelihood_true)
        likelihood_false = max(0.01, likelihood_false)
        
        # Bayes' theorem
        # P(true|E) = P(E|true) * P(true) / P(E)
        # P(E) = P(E|true)*P(true) + P(E|false)*P(false)
        
        p_evidence = (likelihood_true * self.prior_true + 
                     likelihood_false * self.prior_false)
        
        posterior_true = (likelihood_true * self.prior_true) / p_evidence
        posterior_false = (likelihood_false * self.prior_false) / p_evidence
        
        # Normalize
        total = posterior_true + posterior_false
        posterior_true /= total
        posterior_false /= total
        
        # Update priors for next iteration
        self.prior_true = posterior_true
        self.prior_false = posterior_false
        
        # Record history
        self.evidence_history.append({
            "source": evidence.source_name,
            "verdict": evidence.verdict.value,
            "posterior_true": posterior_true,
            "posterior_false": posterior_false
        })
        
        return posterior_true, posterior_false
    
    def get_final_verdict(self) -> Dict:
        """Get final verdict after all evidence"""
        if self.prior_true > 0.7:
            verdict = "TRUE"
        elif self.prior_false > 0.7:
            verdict = "FALSE"
        elif self.prior_true > self.prior_false:
            verdict = "LIKELY TRUE"
        elif self.prior_false > self.prior_true:
            verdict = "LIKELY FALSE"
        else:
            verdict = "UNCERTAIN"
        
        return {
            "verdict": verdict,
            "probability_true": self.prior_true,
            "probability_false": self.prior_false,
            "evidence_count": len(self.evidence_history),
            "history": self.evidence_history
        }
    
    def reset(self, prior_true: float = 0.5):
        """Reset for new claim"""
        self.prior_true = prior_true
        self.prior_false = 1 - prior_true
        self.evidence_history = []


class EnsembleConfidenceCalculator:
    """
    Ensemble method combining multiple confidence calculation approaches.
    
    Combines:
    1. Weighted average (simple)
    2. Monte Carlo simulation (robust)
    3. Bayesian updating (sequential)
    
    The ensemble provides the most reliable confidence estimate.
    """
    
    def __init__(self, mc_simulations: int = 5000):
        self.monte_carlo = MonteCarloConfidenceEngine(simulations=mc_simulations)
    
    def calculate(self, evidence: List[SourceEvidence]) -> Dict:
        """
        Calculate ensemble confidence from all methods
        """
        if not evidence:
            return {
                "verdict": "UNKNOWN",
                "confidence": 0.0,
                "confidence_interval": (0.0, 0.0),
                "methods": {}
            }
        
        # Method 1: Weighted Average
        weighted_result = self._weighted_average(evidence)
        
        # Method 2: Monte Carlo
        mc_result = self.monte_carlo.simulate(evidence)
        
        # Method 3: Bayesian
        bayesian_result = self._bayesian_sequential(evidence)
        
        # Ensemble combination
        # Weight Monte Carlo highest (most robust), then Bayesian, then weighted avg
        ensemble_true = (
            weighted_result["probability_true"] * 0.2 +
            mc_result.probability_true * 0.5 +
            bayesian_result["probability_true"] * 0.3
        )
        
        ensemble_false = (
            weighted_result["probability_false"] * 0.2 +
            mc_result.probability_false * 0.5 +
            bayesian_result["probability_false"] * 0.3
        )
        
        # Normalize
        total = ensemble_true + ensemble_false
        if total > 0:
            ensemble_true /= total
            ensemble_false /= total
        
        # Determine verdict
        if ensemble_true > 0.7:
            verdict = "TRUE"
        elif ensemble_false > 0.7:
            verdict = "FALSE"
        elif ensemble_true > ensemble_false:
            verdict = "LIKELY TRUE"
        elif ensemble_false > ensemble_true:
            verdict = "LIKELY FALSE"
        else:
            verdict = "UNCERTAIN"
        
        # Final confidence
        confidence = max(ensemble_true, ensemble_false)
        
        # Use Monte Carlo CI as it's most statistically rigorous
        confidence_interval = mc_result.confidence_interval
        
        return {
            "verdict": verdict,
            "confidence": confidence,
            "probability_true": ensemble_true,
            "probability_false": ensemble_false,
            "confidence_interval": confidence_interval,
            "methods": {
                "weighted_average": weighted_result,
                "monte_carlo": {
                    "verdict": mc_result.verdict.value,
                    "confidence": mc_result.mean_confidence,
                    "probability_true": mc_result.probability_true,
                    "probability_false": mc_result.probability_false,
                    "convergence": mc_result.convergence_score
                },
                "bayesian": bayesian_result
            },
            "evidence_count": len(evidence),
            "source_agreement": self._calculate_agreement(evidence)
        }
    
    def _weighted_average(self, evidence: List[SourceEvidence]) -> Dict:
        """Simple weighted average calculation"""
        true_weight = 0.0
        false_weight = 0.0
        total_weight = 0.0
        
        for e in evidence:
            weight = e.credibility * e.confidence * e.weight
            
            if e.verdict == VerdictCategory.TRUE:
                true_weight += weight
            elif e.verdict == VerdictCategory.FALSE:
                false_weight += weight
            elif e.verdict == VerdictCategory.MIXED:
                true_weight += weight * 0.3
                false_weight += weight * 0.3
            
            total_weight += weight
        
        if total_weight > 0:
            prob_true = true_weight / total_weight
            prob_false = false_weight / total_weight
        else:
            prob_true = 0.5
            prob_false = 0.5
        
        return {
            "probability_true": prob_true,
            "probability_false": prob_false,
            "total_weight": total_weight
        }
    
    def _bayesian_sequential(self, evidence: List[SourceEvidence]) -> Dict:
        """Bayesian sequential updating"""
        updater = BayesianConfidenceUpdater(prior_true=0.5)
        
        for e in evidence:
            updater.update(e)
        
        return updater.get_final_verdict()
    
    def _calculate_agreement(self, evidence: List[SourceEvidence]) -> float:
        """Calculate agreement between sources"""
        if len(evidence) < 2:
            return 1.0
        
        true_count = sum(1 for e in evidence if e.verdict == VerdictCategory.TRUE)
        false_count = sum(1 for e in evidence if e.verdict == VerdictCategory.FALSE)
        
        majority = max(true_count, false_count)
        return majority / len(evidence)


class ConfidenceCalibrator:
    """
    Calibrates confidence scores based on historical accuracy.
    
    If we historically say "90% confident" but are only right 75% of the time,
    we need to adjust our confidence down.
    """
    
    def __init__(self):
        # Buckets for calibration data
        # Key: confidence bucket (0.0-0.1, 0.1-0.2, etc.)
        # Value: list of (predicted, actual) pairs
        self.calibration_data: Dict[float, List[Tuple[float, bool]]] = {}
        for i in range(10):
            bucket = i / 10
            self.calibration_data[bucket] = []
    
    def record_outcome(self, predicted_confidence: float, was_correct: bool):
        """Record a prediction outcome for calibration"""
        bucket = math.floor(predicted_confidence * 10) / 10
        bucket = min(bucket, 0.9)  # Cap at 0.9 bucket
        self.calibration_data[bucket].append((predicted_confidence, was_correct))
    
    def calibrate(self, raw_confidence: float) -> float:
        """
        Calibrate a raw confidence score based on historical accuracy.
        """
        bucket = math.floor(raw_confidence * 10) / 10
        bucket = min(bucket, 0.9)
        
        history = self.calibration_data.get(bucket, [])
        
        if len(history) < 10:
            # Not enough data for calibration
            return raw_confidence
        
        # Calculate actual accuracy in this bucket
        actual_accuracy = sum(1 for _, correct in history if correct) / len(history)
        
        # Adjust confidence toward actual accuracy
        # Weighted average: 70% raw, 30% historical
        calibrated = raw_confidence * 0.7 + actual_accuracy * 0.3
        
        return calibrated
    
    def get_calibration_report(self) -> Dict:
        """Get report on calibration status"""
        report = {}
        
        for bucket, history in self.calibration_data.items():
            if len(history) >= 5:
                predicted_avg = sum(p for p, _ in history) / len(history)
                actual_accuracy = sum(1 for _, c in history if c) / len(history)
                
                report[f"{bucket:.1f}-{bucket+0.1:.1f}"] = {
                    "sample_size": len(history),
                    "predicted_avg": predicted_avg,
                    "actual_accuracy": actual_accuracy,
                    "calibration_error": abs(predicted_avg - actual_accuracy)
                }
        
        return report


__all__ = [
    'MonteCarloConfidenceEngine', 'MonteCarloResult',
    'BayesianConfidenceUpdater', 'EnsembleConfidenceCalculator',
    'ConfidenceCalibrator', 'SourceEvidence', 'VerdictCategory'
]
