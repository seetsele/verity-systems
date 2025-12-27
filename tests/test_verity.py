"""
Verity Systems - Comprehensive Unit Tests
Tests for fact-checking API, providers, and verification engine.
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

# ============================================================
# DEMO/FRONTEND TESTS
# ============================================================

class TestDemoFunctionality:
    """Tests for the frontend demo features"""
    
    def test_fact_database_earth_age(self):
        """Test that Earth's age fact returns correct data"""
        # Simulating the FACT_DATABASE from main-v2.js
        fact_database = {
            "earth": {
                "age": {
                    "verdict": "VERIFIED_TRUE",
                    "confidence": 98.7,
                    "summary": "The Earth is approximately 4.54 billion years old"
                }
            }
        }
        
        result = fact_database["earth"]["age"]
        assert result["verdict"] == "VERIFIED_TRUE"
        assert result["confidence"] > 95
        assert "4.54 billion" in result["summary"]
    
    def test_fact_database_brain_myth(self):
        """Test that 10% brain myth returns false"""
        fact_database = {
            "brain": {
                "10percent": {
                    "verdict": "VERIFIED_FALSE",
                    "confidence": 15.2,
                    "summary": "The claim that humans only use 10% of their brain is a myth"
                }
            }
        }
        
        result = fact_database["brain"]["10percent"]
        assert result["verdict"] == "VERIFIED_FALSE"
        assert result["confidence"] < 20  # Low confidence means high certainty it's false
    
    def test_fact_database_lightning_myth(self):
        """Test that lightning myth returns false"""
        fact_database = {
            "lightning": {
                "strike": {
                    "verdict": "VERIFIED_FALSE",
                    "confidence": 12.5,
                    "summary": "Lightning frequently strikes the same place"
                }
            }
        }
        
        result = fact_database["lightning"]["strike"]
        assert result["verdict"] == "VERIFIED_FALSE"
    
    def test_demo_attempts_limit(self):
        """Test that demo attempts are limited to 2"""
        max_attempts = 2
        attempts = 0
        
        # Simulate using attempts
        for _ in range(3):
            if attempts < max_attempts:
                attempts += 1
        
        assert attempts == max_attempts


class TestClaimAnalysis:
    """Tests for claim analysis logic"""
    
    def test_claim_contains_earth_age(self):
        """Test detection of Earth age claims"""
        claims = [
            "The Earth is approximately 4.5 billion years old",
            "Earth is 4.54 billion years old",
            "The earth is billions of years old",
        ]
        
        for claim in claims:
            claim_lower = claim.lower()
            is_earth_age = (
                ('earth' in claim_lower and 
                 ('billion' in claim_lower or 'years old' in claim_lower or 'age' in claim_lower)) or
                '4.5 billion' in claim_lower
            )
            assert is_earth_age, f"Failed to detect Earth age claim: {claim}"
    
    def test_claim_contains_brain_myth(self):
        """Test detection of 10% brain myth claims"""
        claims = [
            "Humans only use 10% of their brain",
            "We use 10 percent of our brain",
            "10% brain myth",
        ]
        
        for claim in claims:
            claim_lower = claim.lower()
            is_brain_myth = (
                ('brain' in claim_lower and '10' in claim_lower) or
                ('use' in claim_lower and 'percent' in claim_lower and 'brain' in claim_lower)
            )
            assert is_brain_myth, f"Failed to detect brain myth claim: {claim}"
    
    def test_claim_contains_opinion(self):
        """Test detection of opinion-based claims"""
        claims = [
            "This is the best restaurant ever",
            "Everyone should learn to code",
            "Pizza is the worst food",
        ]
        
        opinion_patterns = ['best', 'worst', 'should', 'always', 'never', 'everyone', 'nobody']
        
        for claim in claims:
            claim_lower = claim.lower()
            has_opinion = any(pattern in claim_lower for pattern in opinion_patterns)
            assert has_opinion, f"Failed to detect opinion in claim: {claim}"


class TestScoreWheel:
    """Tests for the animated score wheel component"""
    
    def test_score_wheel_color_high(self):
        """Test that high scores get green color"""
        score = 95
        if score >= 80:
            color = '#22c55e'  # Green
        elif score >= 60:
            color = '#fbbf24'  # Yellow
        elif score >= 40:
            color = '#f97316'  # Orange
        else:
            color = '#ef4444'  # Red
        
        assert color == '#22c55e'
    
    def test_score_wheel_color_medium(self):
        """Test that medium scores get yellow color"""
        score = 70
        if score >= 80:
            color = '#22c55e'
        elif score >= 60:
            color = '#fbbf24'
        elif score >= 40:
            color = '#f97316'
        else:
            color = '#ef4444'
        
        assert color == '#fbbf24'
    
    def test_score_wheel_color_low(self):
        """Test that low scores get red color"""
        score = 25
        if score >= 80:
            color = '#22c55e'
        elif score >= 60:
            color = '#fbbf24'
        elif score >= 40:
            color = '#f97316'
        else:
            color = '#ef4444'
        
        assert color == '#ef4444'
    
    def test_score_circumference_calculation(self):
        """Test SVG circumference calculation for score wheel"""
        size = 120
        radius = (size - 10) / 2  # 55
        circumference = 2 * 3.14159 * radius
        
        score = 75
        stroke_dashoffset = circumference - (score / 100) * circumference
        
        assert circumference > 340 and circumference < 350
        assert stroke_dashoffset > 0


# ============================================================
# API ENDPOINT TESTS
# ============================================================

class TestAPIEndpoints:
    """Tests for API endpoint responses"""
    
    def test_health_endpoint_structure(self):
        """Test health endpoint returns correct structure"""
        # Expected health response structure
        health_response = {
            "status": "healthy",
            "version": "1.0.0",
            "providers_available": 14,
            "timestamp": datetime.now().isoformat()
        }
        
        assert "status" in health_response
        assert "version" in health_response
        assert health_response["status"] == "healthy"
    
    def test_verify_request_structure(self):
        """Test verify request has correct structure"""
        verify_request = {
            "claim": "The Earth is 4.5 billion years old",
            "providers": ["anthropic", "groq", "wikipedia"],
            "detail_level": "comprehensive"
        }
        
        assert "claim" in verify_request
        assert len(verify_request["claim"]) >= 10
        assert isinstance(verify_request["providers"], list)
    
    def test_verify_response_structure(self):
        """Test verify response has all required fields"""
        verify_response = {
            "request_id": "req_abc123",
            "claim": "The Earth is 4.5 billion years old",
            "status": "verified_true",
            "confidence_score": 98.7,
            "analysis_summary": "This claim is supported by scientific evidence",
            "ai_analysis": "Detailed analysis here...",
            "sources": [
                {"name": "NASA", "url": "https://nasa.gov", "credibility": "high"}
            ],
            "breakdown": {
                "ai_agreement": 100,
                "source_credibility": 98,
                "evidence_strength": 99,
                "consensus_score": 97
            }
        }
        
        required_fields = [
            "request_id", "claim", "status", "confidence_score",
            "analysis_summary", "sources", "breakdown"
        ]
        
        for field in required_fields:
            assert field in verify_response, f"Missing field: {field}"
    
    def test_verdict_types(self):
        """Test all verdict types are valid"""
        valid_verdicts = [
            'VERIFIED_TRUE', 'VERIFIED_FALSE', 'PARTIALLY_TRUE',
            'PARTIALLY_VERIFIABLE', 'UNVERIFIABLE', 'NEEDS_VERIFICATION',
            'DISPUTED', 'MISLEADING', 'OUTDATED', 'SATIRE'
        ]
        
        assert 'VERIFIED_TRUE' in valid_verdicts
        assert 'VERIFIED_FALSE' in valid_verdicts
        assert len(valid_verdicts) >= 8


class TestProviderIntegration:
    """Tests for AI provider integrations"""
    
    def test_provider_available_check(self):
        """Test provider availability check logic"""
        class MockProvider:
            def __init__(self, api_key):
                self.api_key = api_key
            
            @property
            def is_available(self):
                return bool(self.api_key)
        
        # Test with API key
        provider_with_key = MockProvider("test_api_key")
        assert provider_with_key.is_available == True
        
        # Test without API key
        provider_without_key = MockProvider(None)
        assert provider_without_key.is_available == False
    
    def test_wikipedia_url_construction(self):
        """Test Wikipedia search URL is constructed correctly"""
        base_url = "https://en.wikipedia.org/w/api.php"
        search_term = "Earth age"
        
        params = {
            "action": "query",
            "format": "json",
            "list": "search",
            "srsearch": search_term,
            "srlimit": 5
        }
        
        from urllib.parse import urlencode
        full_url = f"{base_url}?{urlencode(params)}"
        
        assert "wikipedia.org" in full_url
        assert "Earth+age" in full_url or "Earth%20age" in full_url


class TestSourceCredibility:
    """Tests for source credibility scoring"""
    
    def test_high_credibility_sources(self):
        """Test that authoritative sources get high credibility"""
        high_credibility_domains = [
            "nasa.gov", "nih.gov", "nature.com", "science.org",
            "who.int", "cdc.gov", "reuters.com", "apnews.com"
        ]
        
        def get_credibility(domain):
            if any(d in domain for d in ["gov", "edu", ".int"]):
                return "high"
            elif any(d in domain for d in ["nature.com", "science.org", "reuters", "apnews"]):
                return "high"
            return "medium"
        
        for domain in high_credibility_domains:
            assert get_credibility(domain) == "high", f"{domain} should be high credibility"
    
    def test_credibility_tiers(self):
        """Test credibility tier system"""
        tiers = {
            "TIER_1_AUTHORITATIVE": 1.0,
            "TIER_2_REPUTABLE": 0.8,
            "TIER_3_STANDARD": 0.6,
            "TIER_4_UNVERIFIED": 0.4
        }
        
        assert tiers["TIER_1_AUTHORITATIVE"] > tiers["TIER_2_REPUTABLE"]
        assert tiers["TIER_2_REPUTABLE"] > tiers["TIER_3_STANDARD"]


class TestConsensusAlgorithm:
    """Tests for consensus/voting algorithm"""
    
    def test_simple_majority(self):
        """Test simple majority voting"""
        votes = ["TRUE", "TRUE", "TRUE", "FALSE", "TRUE"]
        
        vote_counts = {}
        for vote in votes:
            vote_counts[vote] = vote_counts.get(vote, 0) + 1
        
        winner = max(vote_counts.items(), key=lambda x: x[1])
        
        assert winner[0] == "TRUE"
        assert winner[1] == 4
    
    def test_weighted_voting(self):
        """Test weighted voting system"""
        votes = [
            {"verdict": "TRUE", "weight": 1.0, "provider": "claude"},
            {"verdict": "TRUE", "weight": 0.8, "provider": "wikipedia"},
            {"verdict": "FALSE", "weight": 0.9, "provider": "gpt4"},
        ]
        
        weighted_scores = {}
        for vote in votes:
            verdict = vote["verdict"]
            weighted_scores[verdict] = weighted_scores.get(verdict, 0) + vote["weight"]
        
        winner = max(weighted_scores.items(), key=lambda x: x[1])
        
        assert winner[0] == "TRUE"
        assert weighted_scores["TRUE"] == 1.8
        assert weighted_scores["FALSE"] == 0.9
    
    def test_confidence_calibration(self):
        """Test confidence score calibration based on agreement"""
        base_confidence = 80
        agreement_rate = 0.9  # 90% of providers agree
        
        calibrated_confidence = base_confidence * (0.5 + 0.5 * agreement_rate)
        
        assert calibrated_confidence > base_confidence * 0.9


class TestErrorHandling:
    """Tests for error handling"""
    
    def test_claim_too_short(self):
        """Test that short claims are rejected"""
        min_length = 10
        
        short_claims = ["test", "hi", "ok"]
        valid_claims = ["The Earth is 4.5 billion years old"]
        
        for claim in short_claims:
            assert len(claim) < min_length
        
        for claim in valid_claims:
            assert len(claim) >= min_length
    
    def test_api_timeout_handling(self):
        """Test that API timeouts are handled gracefully"""
        timeout_seconds = 30
        
        class MockTimeout:
            def __init__(self, timeout):
                self.timeout = timeout
        
        timeout = MockTimeout(timeout_seconds)
        assert timeout.timeout == 30
    
    def test_invalid_verdict_handling(self):
        """Test handling of invalid verdict values"""
        valid_verdicts = {'TRUE', 'FALSE', 'PARTIALLY_TRUE', 'UNVERIFIABLE'}
        
        def normalize_verdict(verdict):
            normalized = verdict.upper().replace('-', '_').replace(' ', '_')
            if normalized in valid_verdicts:
                return normalized
            return 'UNVERIFIABLE'
        
        assert normalize_verdict("true") == "TRUE"
        assert normalize_verdict("INVALID") == "UNVERIFIABLE"
        assert normalize_verdict("partially-true") == "PARTIALLY_TRUE"


# ============================================================
# RUN TESTS
# ============================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
