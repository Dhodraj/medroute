#!/usr/bin/env python3
"""
Quick test script to verify the triage backend is working
"""

import asyncio
import httpx
import json
from typing import Dict, Any


async def test_api_endpoints():
    """Test all API endpoints"""
    base_url = "http://localhost:8000"
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        print("🧪 Testing Healthcare Triage API")
        print("=" * 40)
        
        # Test 1: Root endpoint
        print("\n1. Testing root endpoint...")
        try:
            response = await client.get(f"{base_url}/")
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                print("   ✅ Root endpoint working")
            else:
                print("   ❌ Root endpoint failed")
        except Exception as e:
            print(f"   ❌ Root endpoint error: {e}")
        
        # Test 2: Health check
        print("\n2. Testing health endpoint...")
        try:
            response = await client.get(f"{base_url}/health")
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                health_data = response.json()
                print(f"   Status: {health_data.get('status', 'unknown')}")
                print("   ✅ Health endpoint working")
            else:
                print("   ❌ Health endpoint failed")
        except Exception as e:
            print(f"   ❌ Health endpoint error: {e}")
        
        # Test 3: Triage endpoint
        print("\n3. Testing triage endpoint...")
        test_cases = [
            "I have chest pain for 2 hours",
            "Mild headache and feeling tired",
            "High fever with severe headache"
        ]
        
        for i, query in enumerate(test_cases, 1):
            print(f"\n   Test 3.{i}: \"{query}\"")
            try:
                payload = {"query": query}
                response = await client.post(
                    f"{base_url}/triage",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                
                print(f"   Status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"   Triage Level: {data.get('triage_level', 'unknown')}")
                    print(f"   Symptoms: {len(data.get('symptoms', []))}")
                    print(f"   Processing Time: {data.get('processing_time_ms', 0)}ms")
                    print("   ✅ Triage successful")
                else:
                    print(f"   ❌ Triage failed: {response.text}")
                    
            except Exception as e:
                print(f"   ❌ Triage error: {e}")
        
        # Test 4: Stats endpoint
        print("\n4. Testing stats endpoint...")
        try:
            response = await client.get(f"{base_url}/stats")
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                stats = response.json()
                total_logs = stats.get('database', {}).get('total_logs', 0)
                print(f"   Total logs: {total_logs}")
                print("   ✅ Stats endpoint working")
            else:
                print("   ❌ Stats endpoint failed")
        except Exception as e:
            print(f"   ❌ Stats endpoint error: {e}")


def test_direct_import():
    """Test importing the application directly"""
    print("\n🔍 Testing direct imports...")
    
    try:
        from app.main import app
        print("   ✅ FastAPI app import successful")
    except Exception as e:
        print(f"   ❌ FastAPI app import failed: {e}")
    
    try:
        from app.orchestrator import TriageOrchestrator
        orch = TriageOrchestrator()
        print("   ✅ Orchestrator import successful")
    except Exception as e:
        print(f"   ❌ Orchestrator import failed: {e}")
    
    try:
        from app.config import get_settings
        settings = get_settings()
        print(f"   ✅ Config import successful - Model: {settings.ollama_model}")
    except Exception as e:
        print(f"   ❌ Config import failed: {e}")


async def main():
    """Main test function"""
    print("🏥 Healthcare Triage Backend Quick Test")
    print("=" * 50)
    
    # Test direct imports first
    test_direct_import()
    
    # Test API endpoints (requires running server)
    print("\n📡 Testing API endpoints (requires running server)...")
    print("   Start server with: uvicorn app.main:app --reload")
    
    try:
        await test_api_endpoints()
    except Exception as e:
        print(f"\n⚠️  API tests skipped - server not running: {e}")
        print("   To test API endpoints:")
        print("   1. Start server: uvicorn app.main:app --reload")
        print("   2. Run this script again")
    
    print("\n" + "=" * 50)
    print("🏁 Quick test completed!")
    print("\nNext steps:")
    print("1. Install dependencies: pip install -r requirements.txt")
    print("2. Install Ollama: curl -fsSL https://ollama.ai/install.sh | sh")
    print("3. Pull model: python3 manage_model.py pull <model_name>")
    print("   Example: python3 manage_model.py pull medllama2:7b")
    print("4. Start server: uvicorn app.main:app --reload")
    print("5. Test API: python test_validation.py")


if __name__ == "__main__":
    asyncio.run(main())
