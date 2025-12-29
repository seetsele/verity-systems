#!/usr/bin/env python3
"""Debug script to trace verification flow"""

import asyncio
import os
import sys

# Add path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

async def debug_verification():
    from verity_enhanced_orchestrator import EnhancedVerifier, VerifierConfig
    
    config = VerifierConfig(
        max_concurrent_requests=5,
        request_timeout_seconds=60,
        enable_caching=False  # Disable cache for debugging
    )
    
    verifier = EnhancedVerifier(config)
    await verifier.initialize()
    
    claim = "The Eiffel Tower is located in Paris, France"
    
    print(f"\n{'='*60}")
    print(f"Testing claim: {claim}")
    print(f"{'='*60}")
    
    # Run individual components manually
    print("\n1. Traditional verification:")
    try:
        traditional = await verifier._run_traditional_verification(claim)
        print(f"   Status: {traditional.status.value}")
        print(f"   Confidence: {traditional.confidence_score:.2%}")
        print(f"   Sources: {len(traditional.sources)}")
    except Exception as e:
        print(f"   ERROR: {e}")
        traditional = None
    
    print("\n2. Extended sources:")
    try:
        extended = await verifier._run_extended_sources(claim)
        print(f"   Evidence count: {extended.get('evidence_count', 0)}")
        print(f"   Evidence strength: {extended.get('evidence_strength', 0):.2%}")
    except Exception as e:
        print(f"   ERROR: {e}")
        extended = None
    
    print("\n3. LLM verification:")
    try:
        llm = await verifier._run_llm_verification(claim)
        consensus = llm.get("consensus", {})
        print(f"   Verdict: {consensus.get('verdict', 'N/A')}")
        print(f"   Confidence: {consensus.get('confidence', 0):.2%}")
        print(f"   Agreement: {consensus.get('agreement', 0):.2%}")
    except Exception as e:
        print(f"   ERROR: {e}")
        llm = None
    
    print("\n4. Combine results (manual):")
    if traditional or extended or llm:
        verdicts = []
        
        if traditional:
            verdicts.append((traditional.status.value, traditional.confidence_score, 0.4))
            print(f"   Traditional verdict: ({traditional.status.value}, {traditional.confidence_score:.2f}, 0.4)")
        
        if llm and llm.get("consensus"):
            llm_consensus = llm["consensus"]
            from verity_enhanced_orchestrator import VerificationStatus
            status_map = {
                "TRUE": VerificationStatus.VERIFIED_TRUE.value,
                "FALSE": VerificationStatus.VERIFIED_FALSE.value,
                "PARTIALLY_TRUE": VerificationStatus.PARTIALLY_TRUE.value,
                "UNVERIFIABLE": VerificationStatus.UNVERIFIABLE.value,
            }
            llm_verdict = llm_consensus.get("verdict", "").upper()
            llm_confidence = llm_consensus.get("confidence", 0.5)
            mapped_status = status_map.get(llm_verdict, VerificationStatus.NEEDS_CONTEXT.value)
            verdicts.append((mapped_status, llm_confidence, 0.35))
            print(f"   LLM verdict: ({mapped_status}, {llm_confidence:.2f}, 0.35)")
        
        print(f"\n   All verdicts: {verdicts}")
        
        # Calculate weighted consensus manually
        status_scores = {}
        total_weight = 0
        
        for status, confidence, weight in verdicts:
            weighted_score = confidence * weight
            if status not in status_scores:
                status_scores[status] = 0
            status_scores[status] += weighted_score
            total_weight += weight
            print(f"   Adding: {status} += {confidence:.2f} * {weight:.2f} = {weighted_score:.4f}")
        
        print(f"\n   Total weight: {total_weight}")
        print(f"   Raw scores: {status_scores}")
        
        # Normalize
        for status in status_scores:
            status_scores[status] /= total_weight
        
        print(f"   Normalized: {status_scores}")
        
        best_status = max(status_scores.items(), key=lambda x: x[1])
        print(f"\n   FINAL: {best_status[0]} @ {best_status[1]:.2%}")
    
    print("\n5. Full verification result:")
    result = await verifier.verify_claim(claim, "debug_user")
    print(f"   Status: {result.status.value}")
    print(f"   Confidence: {result.confidence_score:.2%}")
    print(f"   Summary: {result.summary}")
    
    await verifier.shutdown()

if __name__ == "__main__":
    asyncio.run(debug_verification())
