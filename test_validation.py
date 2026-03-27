#!/usr/bin/env python3
"""
Manual testing script for the healthcare triage backend
"""

import asyncio
import json
import time
from typing import List, Dict, Any

from app.schemas import TriageRequest
from app.orchestrator import TriageOrchestrator


class TriageValidator:
    """Validates triage system with test cases"""
    
    def __init__(self):
        self.orchestrator = TriageOrchestrator()
        
        # Test cases with expected triage levels
        self.test_cases = [
            # Emergency cases
            {
                "query": "I have severe chest pain for 2 hours",
                "expected_level": "emergency",
                "description": "Chest pain emergency"
            },
            {
                "query": "I can't breathe and having chest pressure",
                "expected_level": "emergency", 
                "description": "Breathing difficulty emergency"
            },
            {
                "query": "I think I'm having a heart attack",
                "expected_level": "emergency",
                "description": "Heart attack emergency"
            },
            
            # Urgent cases
            {
                "query": "High fever of 103F with severe headache",
                "expected_level": "urgent",
                "description": "High fever urgent"
            },
            {
                "query": "Severe abdominal pain for 6 hours",
                "expected_level": "urgent",
                "description": "Severe pain urgent"
            },
            
            # Semi-urgent cases
            {
                "query": "Mild fever and sore throat for 2 days",
                "expected_level": "semi_urgent",
                "description": "Cold symptoms semi-urgent"
            },
            {
                "query": "Small cut on finger, minor bleeding",
                "expected_level": "semi_urgent",
                "description": "Minor injury semi-urgent"
            },
            
            # Non-urgent cases
            {
                "query": "Mild headache, feeling tired",
                "expected_level": "non_urgent",
                "description": "Mild symptoms non-urgent"
            },
            {
                "query": "Need routine checkup, feeling fine",
                "expected_level": "non_urgent",
                "description": "Routine care non-urgent"
            }
        ]
    
    async def run_validation(self) -> Dict[str, Any]:
        """Run all validation tests"""
        print("🏥 Healthcare Triage Backend Validation")
        print("=" * 50)
        
        results = {
            "total_tests": len(self.test_cases),
            "passed": 0,
            "failed": 0,
            "test_results": [],
            "performance": {
                "total_time": 0,
                "average_time": 0,
                "max_time": 0,
                "min_time": float('inf')
            }
        }
        
        start_time = time.time()
        
        for i, test_case in enumerate(self.test_cases, 1):
            print(f"\n🧪 Test {i}/{len(self.test_cases)}: {test_case['description']}")
            print(f"Query: \"{test_case['query']}\"")
            
            test_start = time.time()
            
            try:
                # Run triage
                request = TriageRequest(query=test_case['query'])
                print(f"  Processing with orchestrator...")
                response = await self.orchestrator.process_triage(request)
                
                test_time = time.time() - test_start
                print(f"  Response received in {test_time:.2f}s")
                
                # Check result
                passed = response.triage_level.value == test_case['expected_level']
                
                # Update performance metrics
                results["performance"]["max_time"] = max(results["performance"]["max_time"], test_time)
                results["performance"]["min_time"] = min(results["performance"]["min_time"], test_time)
                
                # Store result
                test_result = {
                    "test_id": i,
                    "description": test_case['description'],
                    "query": test_case['query'],
                    "expected_level": test_case['expected_level'],
                    "actual_level": response.triage_level.value,
                    "symptoms_count": len(response.symptoms),
                    "confidence": response.confidence_score,
                    "processing_time_ms": response.processing_time_ms,
                    "passed": passed
                }
                
                results["test_results"].append(test_result)
                
                if passed:
                    results["passed"] += 1
                    print(f"✅ PASS - Triage: {response.triage_level.value}")
                else:
                    results["failed"] += 1
                    print(f"❌ FAIL - Expected: {test_case['expected_level']}, Got: {response.triage_level.value}")
                
                print(f"   Symptoms: {len(response.symptoms)}")
                print(f"   Confidence: {response.confidence_score:.2f}")
                print(f"   Time: {test_time:.2f}s")
                
            except Exception as e:
                test_time = time.time() - test_start
                results["failed"] += 1
                print(f"❌ ERROR: {str(e)}")
                print(f"   Error type: {type(e).__name__}")
                import traceback
                print(f"   Traceback: {traceback.format_exc()}")
                
                test_result = {
                    "test_id": i,
                    "description": test_case['description'],
                    "query": test_case['query'],
                    "expected_level": test_case['expected_level'],
                    "error": str(e),
                    "passed": False,
                    "time": test_time
                }
                results["test_results"].append(test_result)
        
        # Calculate final metrics
        total_time = time.time() - start_time
        results["performance"]["total_time"] = total_time
        results["performance"]["average_time"] = total_time / len(self.test_cases)
        
        if results["performance"]["min_time"] == float('inf'):
            results["performance"]["min_time"] = 0
        
        # Print summary
        self._print_summary(results)
        
        return results
    
    def _print_summary(self, results: Dict[str, Any]):
        """Print validation summary"""
        print("\n" + "=" * 50)
        print("📊 VALIDATION SUMMARY")
        print("=" * 50)
        
        total = results["total_tests"]
        passed = results["passed"]
        failed = results["failed"]
        
        success_rate = (passed / total) * 100 if total > 0 else 0
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        perf = results["performance"]
        print(f"\nPerformance:")
        print(f"  Total Time: {perf['total_time']:.2f}s")
        print(f"  Average Time: {perf['average_time']:.2f}s")
        print(f"  Min Time: {perf['min_time']:.2f}s")
        print(f"  Max Time: {perf['max_time']:.2f}s")
        
        if success_rate >= 70:
            print(f"\n🎉 VALIDATION PASSED - Success rate {success_rate:.1f}% meets 70% threshold")
        else:
            print(f"\n⚠️  VALIDATION WARNING - Success rate {success_rate:.1f}% below 70% threshold")
    
    async def test_system_health(self):
        """Test system health and availability"""
        print("\n🔍 SYSTEM HEALTH CHECK")
        print("-" * 30)
        
        try:
            health = self.orchestrator.get_health_status()
            print(f"Status: {health['status']}")
            print(f"Model Available: {health['model']['available']}")
            
            if health['status'] == 'healthy':
                print("✅ System is healthy")
            else:
                print("⚠️  System has issues")
                
        except Exception as e:
            print(f"❌ Health check failed: {e}")


async def main():
    """Main validation function"""
    validator = TriageValidator()
    
    # Test system health first
    await validator.test_system_health()
    
    # Run validation tests
    results = await validator.run_validation()
    
    # Save results to file
    with open("validation_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n💾 Results saved to validation_results.json")


if __name__ == "__main__":
    asyncio.run(main())
