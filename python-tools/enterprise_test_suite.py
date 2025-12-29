#!/usr/bin/env python3
"""
Verity Enterprise API Test Suite
Comprehensive testing for achieving 90%+ accuracy
"""

import asyncio
import httpx
import json
import time
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from datetime import datetime

# Configuration
API_BASE = "http://localhost:8081"
TIMEOUT = 60.0

@dataclass
class TestCase:
    """A single test case"""
    claim: str
    expected_verdict: str  # true, false, mixed, unverified
    category: str
    difficulty: str  # easy, medium, hard
    notes: str = ""

@dataclass
class TestResult:
    """Result of a single test"""
    test_case: TestCase
    actual_verdict: str
    confidence: float
    passed: bool
    response_time_ms: float
    error: Optional[str] = None
    raw_response: Optional[Dict] = None

# =============================================================
# TEST CASES - Organized by category
# =============================================================

FACTUAL_CLAIMS = [
    TestCase("The Eiffel Tower is a landmark in Paris, France", "true", "geography", "easy"),
    TestCase("Water has a boiling point of 100 degrees Celsius at standard atmospheric pressure", "true", "science", "easy"),
    TestCase("The Great Wall of China can be seen from space with the naked eye", "false", "science", "medium"),
    TestCase("Mount Everest is the highest mountain peak on Earth", "true", "geography", "easy"),
    TestCase("The Amazon River is longer than the Nile River", "false", "geography", "medium", "Nile is longer"),
    TestCase("Japan is divided into 47 prefectures", "true", "geography", "medium"),
    TestCase("Australia is both a country and a continent", "true", "geography", "easy"),
    TestCase("An adult human skeleton has 206 bones", "true", "science", "easy"),
    TestCase("Lightning cannot strike the same location twice", "false", "science", "easy"),
    TestCase("Goldfish only have a memory span of 3 seconds", "false", "science", "medium"),
]

HISTORICAL_CLAIMS = [
    TestCase("World War II ended in 1945", "true", "history", "easy"),
    TestCase("The Berlin Wall fell in 1989", "true", "history", "easy"),
    TestCase("Napoleon Bonaparte was born in France", "false", "history", "medium", "Born in Corsica, Italian at the time"),
    TestCase("The first moon landing was in 1969", "true", "history", "easy"),
    TestCase("Abraham Lincoln was the first US President", "false", "history", "easy"),
    TestCase("The Titanic sank in 1912", "true", "history", "easy"),
    TestCase("Columbus arrived in the Americas in 1492", "true", "history", "medium"),
    TestCase("The Western Roman Empire fell in 476 AD", "true", "history", "medium"),
]

SCIENTIFIC_CLAIMS = [
    TestCase("The Earth orbits the Sun", "true", "science", "easy"),
    TestCase("Humans share about 98% of their DNA with chimpanzees", "true", "science", "medium"),
    TestCase("Antibiotics are effective against viruses", "false", "science", "easy"),
    TestCase("The speed of light is exactly 299,792 kilometers per second", "true", "science", "medium"),
    TestCase("Diamonds are made of carbon", "true", "science", "easy"),
    TestCase("Vaccines cause autism", "false", "science", "easy"),
    TestCase("The human brain uses only 10% of its capacity", "false", "science", "medium"),
    TestCase("Plants release oxygen during photosynthesis", "true", "science", "easy"),
]

STATISTICAL_CLAIMS = [
    TestCase("The world population exceeded 8 billion in 2022", "true", "statistics", "medium"),
    TestCase("India has the largest population in the world as of 2024", "true", "statistics", "medium"),
    TestCase("The United States has 50 states", "true", "statistics", "easy"),
    TestCase("The United Nations has 193 member states", "true", "statistics", "medium"),
    TestCase("Mandarin Chinese is the most spoken native language in the world", "true", "statistics", "medium"),
]

FALSE_CLAIMS = [
    TestCase("The Earth is flat", "false", "science", "easy"),
    TestCase("5G networks cause COVID-19", "false", "misinformation", "easy"),
    TestCase("Drinking bleach cures diseases", "false", "health", "easy"),
    TestCase("Birds are not real", "false", "conspiracy", "easy"),
    TestCase("The moon landing was faked", "false", "conspiracy", "easy"),
    TestCase("Eating carrots can cure blindness", "false", "health", "medium"),
]

def get_all_test_cases() -> List[TestCase]:
    """Get all test cases"""
    return (
        FACTUAL_CLAIMS + 
        HISTORICAL_CLAIMS + 
        SCIENTIFIC_CLAIMS + 
        STATISTICAL_CLAIMS + 
        FALSE_CLAIMS
    )

async def run_single_test(client: httpx.AsyncClient, test_case: TestCase) -> TestResult:
    """Run a single test case"""
    start_time = time.time()
    
    try:
        response = await client.post(
            f"{API_BASE}/api/v4/verify",
            json={"claim": test_case.claim},
            headers={
                "X-API-Key": "test-enterprise-api-key-12345",  # API key for enterprise tier
                "X-User-Tier": "enterprise"
            },
            timeout=TIMEOUT
        )
        
        response_time = (time.time() - start_time) * 1000
        
        if response.status_code != 200:
            return TestResult(
                test_case=test_case,
                actual_verdict="error",
                confidence=0,
                passed=False,
                response_time_ms=response_time,
                error=f"HTTP {response.status_code}: {response.text[:200]}"
            )
        
        data = response.json()
        actual_verdict = data.get("verdict", "unknown").lower()
        confidence = data.get("confidence", 0)
        
        # Normalize verdicts for comparison
        verdict_map = {
            "verified_true": "true",
            "verified_false": "false",
            "partially_true": "mixed",
            "mixed": "mixed",
            "unverified": "unverified",
            "true": "true",
            "false": "false"
        }
        
        normalized_verdict = verdict_map.get(actual_verdict, actual_verdict)
        expected = test_case.expected_verdict.lower()
        
        # Check if passed
        passed = normalized_verdict == expected
        
        return TestResult(
            test_case=test_case,
            actual_verdict=normalized_verdict,
            confidence=confidence,
            passed=passed,
            response_time_ms=response_time,
            raw_response=data
        )
        
    except Exception as e:
        response_time = (time.time() - start_time) * 1000
        return TestResult(
            test_case=test_case,
            actual_verdict="error",
            confidence=0,
            passed=False,
            response_time_ms=response_time,
            error=str(e)
        )

async def run_test_suite(test_cases: List[TestCase] = None) -> Dict[str, Any]:
    """Run the full test suite"""
    if test_cases is None:
        test_cases = get_all_test_cases()
    
    print(f"\n{'='*60}")
    print(f"  VERITY ENTERPRISE API TEST SUITE")
    print(f"  Testing {len(test_cases)} claims")
    print(f"{'='*60}\n")
    
    results: List[TestResult] = []
    
    async with httpx.AsyncClient() as client:
        # First check API health
        try:
            health = await client.get(f"{API_BASE}/health", timeout=5)
            if health.status_code != 200:
                print("❌ API is not healthy!")
                return {"error": "API not available"}
            print("✅ API is healthy\n")
        except Exception as e:
            print(f"❌ Cannot connect to API: {e}")
            return {"error": str(e)}
        
        # Run tests
        for i, test_case in enumerate(test_cases, 1):
            print(f"[{i}/{len(test_cases)}] Testing: {test_case.claim[:50]}...")
            
            result = await run_single_test(client, test_case)
            results.append(result)
            
            status = "✅ PASS" if result.passed else "❌ FAIL"
            print(f"  {status} | Expected: {test_case.expected_verdict} | Got: {result.actual_verdict} | Conf: {result.confidence:.2%}")
            
            if result.error:
                print(f"  ⚠️  Error: {result.error}")
            
            # Small delay to avoid rate limiting
            await asyncio.sleep(0.5)
    
    # Calculate statistics
    passed = sum(1 for r in results if r.passed)
    failed = len(results) - passed
    accuracy = passed / len(results) * 100 if results else 0
    
    avg_response_time = sum(r.response_time_ms for r in results) / len(results) if results else 0
    avg_confidence = sum(r.confidence for r in results) / len(results) if results else 0
    
    # Group by category
    by_category = {}
    for r in results:
        cat = r.test_case.category
        if cat not in by_category:
            by_category[cat] = {"passed": 0, "total": 0}
        by_category[cat]["total"] += 1
        if r.passed:
            by_category[cat]["passed"] += 1
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"  TEST RESULTS SUMMARY")
    print(f"{'='*60}")
    print(f"  Total Tests:     {len(results)}")
    print(f"  Passed:          {passed}")
    print(f"  Failed:          {failed}")
    print(f"  Accuracy:        {accuracy:.1f}%")
    print(f"  Avg Response:    {avg_response_time:.0f}ms")
    print(f"  Avg Confidence:  {avg_confidence:.1%}")
    print(f"\n  By Category:")
    for cat, stats in sorted(by_category.items()):
        cat_acc = stats["passed"] / stats["total"] * 100
        print(f"    {cat:15} {stats['passed']}/{stats['total']} ({cat_acc:.0f}%)")
    
    # List failures
    failures = [r for r in results if not r.passed]
    if failures:
        print(f"\n  FAILURES:")
        for r in failures:
            print(f"    • {r.test_case.claim[:40]}...")
            print(f"      Expected: {r.test_case.expected_verdict}, Got: {r.actual_verdict}")
            if r.test_case.notes:
                print(f"      Note: {r.test_case.notes}")
    
    target_met = accuracy >= 90
    print(f"\n{'='*60}")
    if target_met:
        print(f"  ✅ TARGET MET: {accuracy:.1f}% >= 90%")
    else:
        print(f"  ❌ TARGET NOT MET: {accuracy:.1f}% < 90%")
    print(f"{'='*60}\n")
    
    return {
        "total": len(results),
        "passed": passed,
        "failed": failed,
        "accuracy": accuracy,
        "avg_response_time_ms": avg_response_time,
        "avg_confidence": avg_confidence,
        "by_category": by_category,
        "failures": [
            {
                "claim": r.test_case.claim,
                "expected": r.test_case.expected_verdict,
                "actual": r.actual_verdict,
                "category": r.test_case.category,
                "notes": r.test_case.notes
            }
            for r in failures
        ],
        "target_met": target_met,
        "timestamp": datetime.now().isoformat()
    }

async def quick_test(n: int = 5) -> Dict:
    """Run a quick subset of tests"""
    all_cases = get_all_test_cases()
    # Pick diverse sample
    sample = all_cases[:n]
    return await run_test_suite(sample)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "quick":
        n = int(sys.argv[2]) if len(sys.argv) > 2 else 5
        result = asyncio.run(quick_test(n))
    else:
        result = asyncio.run(run_test_suite())
    
    # Save results
    with open("test_results.json", "w") as f:
        json.dump(result, f, indent=2)
    
    print(f"Results saved to test_results.json")
