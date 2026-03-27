#!/usr/bin/env python3
"""
Test script to query the triage endpoint and verify functionality
"""
import requests
import json
import time

def test_triage_endpoint():
    """Test the triage endpoint with various scenarios"""
    
    base_url = "http://localhost:8000"
    
    print("Testing Triage Endpoint")
    print("=" * 40)
    
    # First check if the server is running
    try:
        health_response = requests.get(f"{base_url}/health", timeout=5)
        print(f"✅ Server health check: {health_response.status_code}")
        print(f"Health response: {health_response.json()}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Server not responding: {e}")
        print("Please start the server with: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
        return
    
    print("\n" + "=" * 40)
    print("Testing Triage Cases")
    print("=" * 40)
    
    # Test cases with different scenarios
    test_cases = [
        {
            "name": "Emergency Case - Chest Pain",
            "data": {
                "query": "I have severe crushing chest pain and can't breathe properly",
                "symptoms": [
                    {
                        "name": "chest pain",
                        "severity": "severe",
                        "duration": "15 minutes",
                        "location": "center chest"
                    },
                    {
                        "name": "shortness of breath",
                        "severity": "severe",
                        "duration": "15 minutes"
                    }
                ]
            },
            "expected_level": "emergency"
        },
        {
            "name": "Urgent Case - High Fever",
            "data": {
                "query": "I have a very high fever and severe headache",
                "symptoms": [
                    {
                        "name": "fever",
                        "severity": "severe",
                        "duration": "6 hours",
                        "additional_info": "temperature 103°F"
                    },
                    {
                        "name": "headache",
                        "severity": "severe",
                        "duration": "6 hours"
                    }
                ]
            },
            "expected_level": "urgent"
        },
        {
            "name": "Semi-Urgent Case - Broken Arm",
            "data": {
                "query": "I fell and think I broke my arm",
                "symptoms": [
                    {
                        "name": "arm pain",
                        "severity": "moderate",
                        "duration": "1 hour",
                        "location": "left forearm"
                    },
                    {
                        "name": "swelling",
                        "severity": "moderate",
                        "location": "left forearm"
                    }
                ]
            },
            "expected_level": "semi_urgent"
        },
        {
            "name": "Non-Urgent Case - Mild Headache",
            "data": {
                "query": "I have a mild headache that started this morning",
                "symptoms": [
                    {
                        "name": "headache",
                        "severity": "mild",
                        "duration": "4 hours"
                    }
                ]
            },
            "expected_level": "non_urgent"
        },
        {
            "name": "Vague Case - General Discomfort",
            "data": {
                "query": "I don't feel well today",
                "symptoms": [
                    {
                        "name": "general malaise",
                        "severity": "mild",
                        "duration": "today"
                    }
                ]
            },
            "expected_level": "non_urgent"
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test_case['name']}")
        print(f"Query: {test_case['data']['query']}")
        print(f"Expected: {test_case['expected_level']}")
        
        try:
            # Send request to triage endpoint
            start_time = time.time()
            response = requests.post(
                f"{base_url}/triage",
                json=test_case["data"],
                headers={"Content-Type": "application/json"},
                timeout=60  # Increased timeout for model processing
            )
            end_time = time.time()
            
            if response.status_code == 200:
                result = response.json()
                
                print(f"✅ Status: {response.status_code}")
                print(f"📊 Triage Level: {result['triage_level']}")
                print(f"🎯 Confidence: {result['confidence_score']:.3f}")
                print(f"⏱️  Response Time: {end_time - start_time:.2f}s")
                
                # Check if recommendation exists
                if result.get('recommendation'):
                    print(f"💡 Recommendation: {result['recommendation'][:100]}...")
                
                # Check metadata for model info
                metadata = result.get('metadata', {})
                triage_meta = metadata.get('triage_agent', {})
                if triage_meta:
                    print(f"🔧 Method: {triage_meta.get('method', 'unknown')}")
                    print(f"🤖 LLM Confidence: {triage_meta.get('llm_confidence', 'N/A')}")
                
                # Verify if result matches expectation
                actual_level = result['triage_level']
                expected_level = test_case['expected_level']
                match = "✅" if actual_level == expected_level else "⚠️"
                print(f"{match} Match: {actual_level == expected_level}")
                
                results.append({
                    "test": test_case['name'],
                    "expected": expected_level,
                    "actual": actual_level,
                    "confidence": result['confidence_score'],
                    "response_time": end_time - start_time,
                    "match": actual_level == expected_level
                })
                
            else:
                print(f"❌ Error: {response.status_code}")
                print(f"Response: {response.text}")
                
        except requests.exceptions.Timeout:
            print("❌ Request timed out (model may be slow)")
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {e}")
        
        print("-" * 50)
    
    # Summary
    print("\n" + "=" * 40)
    print("SUMMARY")
    print("=" * 40)
    
    if results:
        total_tests = len(results)
        successful_matches = sum(1 for r in results if r['match'])
        accuracy = (successful_matches / total_tests) * 100
        
        print(f"📈 Total Tests: {total_tests}")
        print(f"✅ Correct Classifications: {successful_matches}")
        print(f"📊 Accuracy: {accuracy:.1f}%")
        
        confidence_scores = [r['confidence'] for r in results]
        print(f"🎯 Confidence Range: {min(confidence_scores):.3f} - {max(confidence_scores):.3f}")
        
        avg_response_time = sum(r['response_time'] for r in results) / len(results)
        print(f"⏱️  Average Response Time: {avg_response_time:.2f}s")
        
        print("\nDetailed Results:")
        for result in results:
            status = "✅" if result['match'] else "❌"
            print(f"{status} {result['test']}: {result['actual']} (conf: {result['confidence']:.3f})")
        
        print(f"\n🎉 Model-based confidence working: {'YES' if len(set(confidence_scores)) > 1 else 'NO'}")
    else:
        print("❌ No successful tests completed")

if __name__ == "__main__":
    test_triage_endpoint()
