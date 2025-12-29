#!/usr/bin/env python3
"""Test the comprehensive summary functionality"""
import requests
import json

def test_comprehensive_summary():
    response = requests.post(
        'http://localhost:8081/api/v4/verify/detailed',
        json={'claim': 'The Eiffel Tower is located in Paris, France'},
        timeout=120
    )
    
    data = response.json()
    
    print("=" * 60)
    print("COMPREHENSIVE SUMMARY TEST")
    print("=" * 60)
    
    comp = data.get('analysis', {}).get('comprehensive_summary', {})
    
    if not comp:
        print("\nERROR: comprehensive_summary is empty!")
        print("\nFull response keys:", list(data.keys()))
        print("Analysis keys:", list(data.get('analysis', {}).keys()))
        return
    
    print("\n=== SUBJECT MATTER ===")
    subject = comp.get('subject_matter', {})
    print(f"Categories: {subject.get('categories', [])}")
    print(f"Claim Type: {subject.get('claim_type', 'N/A')}")
    print(f"Complexity: {subject.get('complexity', 'N/A')}")
    print(f"Entities: {subject.get('entities_mentioned', [])}")
    
    print("\n=== QUESTION ANALYSIS ===")
    question = comp.get('question_analysis', {})
    print(f"Type: {question.get('question_type', 'N/A')}")
    print(f"Verifiability: {question.get('verifiability_assessment', 'N/A')}")
    
    print("\n=== CONCLUSION ===")
    conclusion = comp.get('conclusion', {})
    print(f"Verdict: {conclusion.get('verdict', 'N/A')}")
    print(f"Confidence: {conclusion.get('confidence_percentage', 'N/A')}%")
    print(f"Confidence Level: {conclusion.get('confidence_level', 'N/A')}")
    
    print("\n=== KEY EVIDENCE ===")
    for i, ev in enumerate(conclusion.get('key_evidence', [])[:3], 1):
        print(f"  {i}. {ev[:100]}...")
    
    print("\n=== RECOMMENDATION ===")
    print(conclusion.get('recommendation', 'N/A'))
    
    print("\n=== NARRATIVE SUMMARY ===")
    narrative = comp.get('narrative_summary', 'N/A')
    print(narrative[:1000] if narrative != 'N/A' else 'N/A')
    
    print("\n" + "=" * 60)

if __name__ == '__main__':
    test_comprehensive_summary()
