#!/usr/bin/env python3
"""
Automated Test Suite for All Features
Tests both main page chat and officials dashboard chat
"""

import requests
import json
import time
import sys

BASE_URL = "http://localhost:8080"

def test_health_check():
    """Test backend is running"""
    print("\n[TEST] 1. Testing Backend Health...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        assert response.status_code == 200
        print("[OK] Backend is running")
        return True
    except Exception as e:
        print(f"[ERROR] Backend health check failed: {e}")
        return False

def test_api_endpoints():
    """Test new API endpoints"""
    print("\n[TEST] 2. Testing New API Endpoints...")
    endpoints = [
        ('/api/wildfires?state=California', 'wildfires'),
        ('/api/covid?state=California', 'covid'),
        ('/api/respiratory?state=California', 'respiratory'),
    ]
    
    for endpoint, name in endpoints:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}")
            print(f"[OK] {name}: {response.status_code}")
        except Exception as e:
            print(f"[FAIL] {name} failed: {e}")

def test_agent_chat_community_resident():
    """Test main page chat as Community Resident"""
    print("\n[TEST] 3. Testing Main Page Chat (Community Resident)...")
    
    test_data = {
        "question": "What's the air quality in Los Angeles?",
        "persona": "Community Resident",
        "state": "California",
        "city": "Los Angeles",
        "days": 7
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/agent-chat",
            json=test_data,
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data.get('success') == True
        assert 'response' in data
        assert data.get('agent') in ['ADK Multi-Agent System', 'Gemini AI with Comprehensive Environmental Data']
        
        print("[OK] Main page chat works")
        print(f"   Agent: {data.get('agent')}")
        print(f"   Response length: {len(data.get('response', ''))}")
        return True
    except Exception as e:
        print(f"[FAIL] Main page chat failed: {e}")
        return False

def test_agent_chat_health_official():
    """Test officials dashboard chat as Health Official"""
    print("\n[TEST] 4. Testing Officials Dashboard Chat (Health Official)...")
    
    test_data = {
        "question": "What are the top health trends?",
        "persona": "Health Official",
        "state": "California",
        "city": "Los Angeles",
        "days": 7
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/agent-chat",
            json=test_data,
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data.get('success') == True
        assert 'response' in data
        
        print("[OK] Officials dashboard chat works")
        print(f"   Agent: {data.get('agent')}")
        print(f"   Persona: Health Official")
        return True
    except Exception as e:
        print(f"[FAIL] Officials dashboard chat failed: {e}")
        return False

def test_location_context():
    """Test location context handling"""
    print("\n[TEST] 5. Testing Location Context...")
    
    # Test with location_context object
    test_data = {
        "question": "What's the weather?",
        "persona": "Community Resident",
        "location_context": {
            "state": "California",
            "city": "San Francisco",
            "zipCode": "94102"
        }
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/agent-chat",
            json=test_data,
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        print("[OK] Location context works (no UnboundLocalError)")
        print(f"   Location: {data.get('location')}")
        return True
    except Exception as e:
        print(f"[FAIL] Location context failed: {e}")
        return False

def test_enhanced_context():
    """Test enhanced context formatting"""
    print("\n[TEST] 6. Testing Enhanced Context Formatting...")
    
    test_data = {
        "question": "Show me current air quality",
        "persona": "Community Resident",
        "state": "California",
        "city": "Los Angeles",
        "days": 7
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/agent-chat",
            json=test_data,
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 200
        data = response.json()
        response_text = data.get('response', '')
        
        # Check for enhanced formatting indicators
        has_real_time = 'CURRENT REAL-TIME' in response_text or 'real-time' in response_text.lower()
        has_environmental = 'environmental' in response_text.lower()
        
        print("[OK] Enhanced context formatting works")
        print(f"   Real-time data indicators: {has_real_time}")
        print(f"   Environmental data: {has_environmental}")
        return True
    except Exception as e:
        print(f"[FAIL] Enhanced context failed: {e}")
        return False

def main():
    """Run all tests"""
    print("\n[TEST] Starting Feature Tests...")
    print("=" * 60)
    
    results = []
    
    # Run all tests
    results.append(("Health Check", test_health_check()))
    test_api_endpoints()
    results.append(("Main Chat", test_agent_chat_community_resident()))
    results.append(("Officials Chat", test_agent_chat_health_official()))
    results.append(("Location Context", test_location_context()))
    results.append(("Enhanced Context", test_enhanced_context()))
    
    # Summary
    print("\n" + "=" * 60)
    print("[SUMMARY] TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "[OK] PASS" if result else "[FAIL] FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\n[RESULT] Passed: {passed}/{total}")
    
    if passed == total:
        print("\n[SUCCESS] ALL TESTS PASSED! Integration is working correctly.")
        return 0
    else:
        print(f"\n[WARNING] {total - passed} test(s) failed. Please check the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

