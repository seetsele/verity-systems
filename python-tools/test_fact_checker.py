"""
Verity Systems - Fact-Checker Test Suite
Run this script to test the fact-checking functionality before launch.
"""

import asyncio
import json
import os
import sys
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Test claims with known answers
TEST_CLAIMS = [
    {
        "claim": "The Earth is approximately 4.5 billion years old",
        "expected": "TRUE",
        "category": "Science"
    },
    {
        "claim": "Humans only use 10% of their brain",
        "expected": "FALSE",
        "category": "Myth"
    },
    {
        "claim": "Water boils at 100 degrees Celsius at sea level",
        "expected": "TRUE",
        "category": "Science"
    },
    {
        "claim": "The Great Wall of China is visible from space with the naked eye",
        "expected": "FALSE",
        "category": "Myth"
    },
    {
        "claim": "Lightning never strikes the same place twice",
        "expected": "FALSE",
        "category": "Myth"
    }
]


def print_header(text: str):
    """Print a formatted header"""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)


def print_result(label: str, value: str, color: str = None):
    """Print a formatted result"""
    colors = {
        "green": "\033[92m",
        "red": "\033[91m",
        "yellow": "\033[93m",
        "cyan": "\033[96m",
        "reset": "\033[0m"
    }
    
    if color and color in colors:
        print(f"  {label}: {colors[color]}{value}{colors['reset']}")
    else:
        print(f"  {label}: {value}")


async def test_providers():
    """Test which providers are available"""
    print_header("Testing Provider Availability")
    
    try:
        from verity_supermodel import VeritySuperModel
        model = VeritySuperModel()
        
        available = []
        unavailable = []
        
        for provider in model.providers:
            if provider.is_available:
                available.append(provider.name)
                print_result(provider.name, "✓ Available", "green")
            else:
                unavailable.append(provider.name)
                print_result(provider.name, "✗ Not configured", "yellow")
        
        print(f"\n  Summary: {len(available)}/{len(model.providers)} providers available")
        
        return len(available) > 0, model
        
    except ImportError as e:
        print_result("Error", f"Failed to import: {e}", "red")
        return False, None
    except Exception as e:
        print_result("Error", str(e), "red")
        return False, None


async def test_single_claim(model, claim_data: dict, index: int):
    """Test a single claim"""
    claim = claim_data["claim"]
    expected = claim_data["expected"]
    category = claim_data["category"]
    
    print(f"\n  [{index}] Testing: \"{claim[:50]}...\"")
    print(f"      Category: {category} | Expected: {expected}")
    
    try:
        result = await model.verify_claim(
            claim=claim,
            client_id="test_runner",
            use_cache=False
        )
        
        # Extract verdict
        verdict = result.verdict.value if hasattr(result.verdict, 'value') else str(result.verdict)
        confidence = result.confidence
        
        # Check if matches expected
        verdict_upper = verdict.upper()
        matches = expected in verdict_upper or verdict_upper in expected
        
        color = "green" if matches else "red"
        status = "✓ PASS" if matches else "✗ FAIL"
        
        print(f"      Result: {verdict} ({confidence:.1f}% confidence) {status}")
        print(f"      Sources: {len(result.sources)} | Processing: {result.processing_time:.2f}s")
        
        return {
            "claim": claim,
            "expected": expected,
            "actual": verdict,
            "confidence": confidence,
            "passed": matches,
            "sources": len(result.sources),
            "time": result.processing_time
        }
        
    except Exception as e:
        print(f"      Error: {str(e)[:100]}")
        return {
            "claim": claim,
            "expected": expected,
            "actual": "ERROR",
            "confidence": 0,
            "passed": False,
            "error": str(e)
        }


async def test_free_providers_only():
    """Test with only free providers (no API key required)"""
    print_header("Testing Free Providers (No API Key)")
    
    try:
        from verity_supermodel import (
            WikipediaProvider, 
            DuckDuckGoProvider, 
            WikidataProvider
        )
        
        providers = [
            WikipediaProvider(),
            DuckDuckGoProvider(),
            WikidataProvider()
        ]
        
        test_claim = "Albert Einstein developed the theory of relativity"
        
        for provider in providers:
            print(f"\n  Testing {provider.name}...")
            try:
                results = await provider.check_claim(test_claim)
                if results:
                    print_result("  Status", f"✓ Working - Got {len(results)} results", "green")
                    if results[0].get('title') or results[0].get('text'):
                        preview = results[0].get('title') or results[0].get('text', '')[:50]
                        print(f"      Preview: {preview}...")
                else:
                    print_result("  Status", "⚠ No results returned", "yellow")
            except Exception as e:
                print_result("  Status", f"✗ Error: {e}", "red")
        
        return True
        
    except Exception as e:
        print_result("Error", str(e), "red")
        return False


async def run_full_test():
    """Run the complete test suite"""
    print("\n")
    print("╔══════════════════════════════════════════════════════════╗")
    print("║         VERITY SYSTEMS - FACT-CHECKER TEST SUITE         ║")
    print("║                                                          ║")
    print("║  Testing 14 AI providers for fact-checking accuracy      ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print(f"\n  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test 1: Free providers (always available)
    await test_free_providers_only()
    
    # Test 2: Check all providers
    providers_ok, model = await test_providers()
    
    if not providers_ok:
        print_header("⚠ No providers available")
        print("  Please configure at least one API key in .env file")
        print("  Free providers (Wikipedia, DuckDuckGo, Wikidata) should work without keys")
        return
    
    # Test 3: Run claim verification tests
    print_header("Running Claim Verification Tests")
    
    results = []
    for i, claim_data in enumerate(TEST_CLAIMS, 1):
        result = await test_single_claim(model, claim_data, i)
        results.append(result)
    
    # Summary
    print_header("Test Summary")
    
    passed = sum(1 for r in results if r.get("passed", False))
    failed = len(results) - passed
    avg_confidence = sum(r.get("confidence", 0) for r in results) / len(results)
    avg_time = sum(r.get("time", 0) for r in results) / len(results)
    
    print_result("Total Tests", str(len(results)))
    print_result("Passed", str(passed), "green" if passed > 0 else "red")
    print_result("Failed", str(failed), "red" if failed > 0 else "green")
    print_result("Average Confidence", f"{avg_confidence:.1f}%")
    print_result("Average Response Time", f"{avg_time:.2f}s")
    
    # Final status
    if passed == len(results):
        print("\n  ✓ All tests passed! Ready for launch.")
    elif passed > len(results) / 2:
        print("\n  ⚠ Most tests passed. Review failed tests before launch.")
    else:
        print("\n  ✗ Multiple tests failed. Please review configuration.")
    
    print(f"\n  Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n")


async def quick_test():
    """Quick test with a single claim"""
    print_header("Quick Test - Single Claim")
    
    try:
        from verity_supermodel import VeritySuperModel
        
        model = VeritySuperModel()
        
        claim = "The speed of light is approximately 300,000 kilometers per second"
        print(f"\n  Claim: \"{claim}\"")
        print("  Verifying...\n")
        
        result = await model.verify_claim(claim, client_id="quick_test")
        
        verdict = result.verdict.value if hasattr(result.verdict, 'value') else str(result.verdict)
        
        print_result("Verdict", verdict, "green" if "TRUE" in verdict.upper() else "yellow")
        print_result("Confidence", f"{result.confidence:.1f}%")
        print_result("Sources Found", str(len(result.sources)))
        print_result("Processing Time", f"{result.processing_time:.2f}s")
        
        if result.sources:
            print("\n  Top Sources:")
            for source in result.sources[:3]:
                print(f"    - {source.name}: {source.url or 'N/A'}")
        
        return True
        
    except Exception as e:
        print_result("Error", str(e), "red")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Verity Systems Fact-Checker")
    parser.add_argument("--quick", action="store_true", help="Run quick single-claim test")
    parser.add_argument("--full", action="store_true", help="Run full test suite")
    parser.add_argument("--providers", action="store_true", help="Test provider availability only")
    
    args = parser.parse_args()
    
    if args.quick:
        asyncio.run(quick_test())
    elif args.providers:
        asyncio.run(test_providers())
    else:
        # Default: run full test
        asyncio.run(run_full_test())


if __name__ == "__main__":
    main()
