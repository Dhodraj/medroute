#!/usr/bin/env python3
"""
Comprehensive test to verify model-based confidence scores
"""
import sys
import os

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "app"))

from app.agents.triage_agent import TriageAgent
from app.schemas import AgentInput, Symptom

def test_varied_confidence():
    """Test that we get varied confidence scores from the model"""
    
    print("Testing Model-Based Confidence Score Variation")
    print("=" * 55)
    
    agent = TriageAgent()
    
    # Test cases designed to get different confidence levels
    test_cases = [
        {
            "query": "I have severe crushing chest pain and shortness of breath",
            "symptoms": [
                Symptom(name="chest pain", severity="severe", duration="10 minutes"),
                Symptom(name="shortness of breath", severity="severe")
            ],
            "description": "Very clear emergency case"
        },
        {
            "query": "I feel unwell",
            "symptoms": [Symptom(name="general malaise", severity="mild")],
            "description": "Vague symptoms, low confidence expected"
        },
        {
            "query": "I have a broken arm",
            "symptoms": [Symptom(name="arm pain", severity="moderate", location="left arm")],
            "description": "Clear but non-emergency case"
        },
        {
            "query": "I might have food poisoning",
            "symptoms": [
                Symptom(name="nausea", severity="moderate"),
                Symptom(name="stomach pain", severity="moderate")
            ],
            "description": "Moderately clear case"
        },
        {
            "query": "I have some discomfort",
            "symptoms": [Symptom(name="discomfort", severity="mild")],
            "description": "Very vague, should have low confidence"
        }
    ]
    
    confidence_scores = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest Case {i}: {test_case['description']}")
        print(f"Query: {test_case['query']}")
        
        agent_input = AgentInput(
            query=test_case["query"],
            symptoms=test_case["symptoms"],
            metadata={}
        )
        
        result = agent.process(agent_input)
        confidence = result.confidence_score
        confidence_scores.append(confidence)
        
        print(f"Triage Level: {result.triage_level.value}")
        print(f"Confidence: {confidence:.3f}")
        
        metadata = result.metadata.get("triage_agent", {})
        print(f"Method: {metadata.get('method', 'unknown')}")
        print(f"LLM Confidence: {metadata.get('llm_confidence', 'N/A')}")
        print("-" * 40)
    
    # Analyze confidence variation
    print(f"\nConfidence Score Analysis:")
    print(f"Scores: {[f'{c:.3f}' for c in confidence_scores]}")
    print(f"Min: {min(confidence_scores):.3f}")
    print(f"Max: {max(confidence_scores):.3f}")
    print(f"Range: {max(confidence_scores) - min(confidence_scores):.3f}")
    
    # Check if we have variation (not all the same)
    unique_scores = len(set(confidence_scores))
    print(f"Unique confidence scores: {unique_scores}")
    
    if unique_scores > 1:
        print("✅ SUCCESS: Model is providing varied confidence scores!")
    else:
        print("⚠️  WARNING: All confidence scores are the same - may be using fallback values")
    
    # Check if scores make logical sense
    print(f"\nLogical Assessment:")
    print("- Emergency cases should have higher confidence than vague cases")
    print("- Clear symptoms should have higher confidence than unclear ones")

if __name__ == "__main__":
    test_varied_confidence()
