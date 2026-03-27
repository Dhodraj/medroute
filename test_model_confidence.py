#!/usr/bin/env python3
"""
Test script to verify that confidence scores are coming from the model
"""
import sys
import os

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "app"))

from app.agents.triage_agent import TriageAgent
from app.schemas import AgentInput, Symptom

def test_model_confidence():
    """Test that confidence scores come from the model"""
    
    print("Testing Model-Based Confidence Scores")
    print("=" * 50)
    
    # Initialize the triage agent
    agent = TriageAgent()
    
    # Test cases with different scenarios
    test_cases = [
        {
            "query": "I have severe chest pain and can't breathe",
            "symptoms": [
                Symptom(name="chest pain", severity="severe", duration="30 minutes"),
                Symptom(name="shortness of breath", severity="severe")
            ],
            "expected_level": "emergency"
        },
        {
            "query": "I have a mild headache for 2 days",
            "symptoms": [
                Symptom(name="headache", severity="mild", duration="2 days")
            ],
            "expected_level": "non_urgent"
        },
        {
            "query": "I have a fever of 102F and body aches",
            "symptoms": [
                Symptom(name="fever", severity="moderate", duration="1 day"),
                Symptom(name="body aches", severity="moderate")
            ],
            "expected_level": "urgent"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest Case {i}: {test_case['query']}")
        print(f"Expected level: {test_case['expected_level']}")
        
        # Create input
        agent_input = AgentInput(
            query=test_case["query"],
            symptoms=test_case["symptoms"],
            metadata={}
        )
        
        # Process with triage agent
        result = agent.process(agent_input)
        
        print(f"Actual level: {result.triage_level.value}")
        print(f"Confidence score: {result.confidence_score:.3f}")
        
        # Check metadata for method used
        triage_metadata = result.metadata.get("triage_agent", {})
        print(f"Method used: {triage_metadata.get('method', 'unknown')}")
        print(f"LLM confidence: {triage_metadata.get('llm_confidence', 'N/A')}")
        print(f"Rule confidence: {triage_metadata.get('rule_based_confidence', 'N/A')}")
        
        # Verify confidence is not a hardcoded value
        common_hardcoded_values = [0.6, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95]
        is_likely_from_model = result.confidence_score not in common_hardcoded_values
        
        print(f"Confidence appears to be from model: {is_likely_from_model}")
        print("-" * 40)
    
    print("\nSummary:")
    print("- All confidence scores should come from the LLM model")
    print("- Non-hardcoded values suggest model-based confidence")
    print("- Check the 'Method used' to see if LLM was consulted")

if __name__ == "__main__":
    test_model_confidence()
