#!/usr/bin/env python3
"""
Integration Tests for Authentication with Existing Endpoints
Tests that protected and public endpoints work correctly with the auth system
"""

import requests
import json

BASE_URL = "https://lab-connect-3.preview.emergentagent.com/api"
HEADERS = {"Content-Type": "application/json"}

def get_auth_token():
    """Get a valid authentication token"""
    test_data = {
        "email": "integration_test@hackster.ai",
        "username": "integration_tester",
        "password": "IntegrationTest123!",
        "role": "member"
    }
    
    # Try to register (might fail if user exists, that's ok)
    requests.post(f"{BASE_URL}/auth/register", json=test_data, headers=HEADERS)
    
    # Login to get token
    login_data = {
        "email": test_data["email"],
        "password": test_data["password"]
    }
    
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data, headers=HEADERS, timeout=10)
    if response.status_code == 200:
        return response.json()["access_token"]
    return None

def test_public_endpoints():
    """Test that public endpoints work without authentication"""
    print("🌐 Testing Public Endpoints (No Auth Required)...")
    
    public_endpoints = [
        ("/supplements", "Supplements"),
        ("/health-tests", "Health Tests"),
        ("/coaches", "Coaches"),
        ("/biohacks", "Biohacking Tips"),
        ("/supplements/priority", "Priority Supplements")
    ]
    
    all_passed = True
    
    for endpoint, name in public_endpoints:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", headers=HEADERS, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list) and len(data) > 0:
                    print(f"✅ {name}: {len(data)} items returned")
                else:
                    print(f"⚠️ {name}: Empty response (might be expected)")
            else:
                print(f"❌ {name}: Status {response.status_code}")
                all_passed = False
        except Exception as e:
            print(f"❌ {name}: Error - {e}")
            all_passed = False
    
    return all_passed

def test_protected_endpoints_without_auth():
    """Test that protected endpoints reject requests without authentication"""
    print("\n🔒 Testing Protected Endpoints (Should Require Auth)...")
    
    protected_endpoints = [
        ("POST", "/users", {"email": "test@test.com", "age": 25}),
        ("GET", "/users/test-id", None),
        ("POST", "/assessments", {"user_id": "test", "responses": {}}),
        ("GET", "/assessments/test-id", None)
    ]
    
    all_passed = True
    
    for method, endpoint, data in protected_endpoints:
        try:
            if method == "GET":
                response = requests.get(f"{BASE_URL}{endpoint}", headers=HEADERS, timeout=10)
            else:
                response = requests.post(f"{BASE_URL}{endpoint}", json=data, headers=HEADERS, timeout=10)
            
            if response.status_code in [401, 403]:
                print(f"✅ {method} {endpoint}: Correctly rejected (Status: {response.status_code})")
            else:
                print(f"❌ {method} {endpoint}: Should require auth (Status: {response.status_code})")
                all_passed = False
        except Exception as e:
            print(f"❌ {method} {endpoint}: Error - {e}")
            all_passed = False
    
    return all_passed

def test_protected_endpoints_with_auth():
    """Test that protected endpoints work with valid authentication"""
    print("\n🔓 Testing Protected Endpoints (With Valid Auth)...")
    
    token = get_auth_token()
    if not token:
        print("❌ Could not get authentication token")
        return False
    
    auth_headers = HEADERS.copy()
    auth_headers["Authorization"] = f"Bearer {token}"
    
    # Test user profile update
    try:
        user_data = {
            "email": "integration_test@hackster.ai",
            "age": 28,
            "goals": ["fitness", "health"]
        }
        
        response = requests.post(f"{BASE_URL}/users", json=user_data, headers=auth_headers, timeout=10)
        if response.status_code == 200:
            print("✅ POST /users: Successfully updated user profile")
        else:
            print(f"❌ POST /users: Status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ POST /users: Error - {e}")
        return False
    
    # Test health assessment creation
    try:
        assessment_data = {
            "user_id": "will-be-overridden",  # Should be set to current user
            "responses": {
                "age": 28,
                "activity_level": "moderate",
                "goals": ["weight_loss", "energy"]
            }
        }
        
        response = requests.post(f"{BASE_URL}/assessments", json=assessment_data, headers=auth_headers, timeout=10)
        if response.status_code == 200:
            assessment = response.json()
            print("✅ POST /assessments: Successfully created health assessment")
            print(f"   Recommended tests: {len(assessment.get('recommended_tests', []))}")
            print(f"   Recommended supplements: {len(assessment.get('recommended_supplements', []))}")
        else:
            print(f"❌ POST /assessments: Status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ POST /assessments: Error - {e}")
        return False
    
    return True

def test_cors_and_headers():
    """Test CORS and header handling"""
    print("\n🌍 Testing CORS and Headers...")
    
    try:
        # Test with different origins (basic test)
        custom_headers = HEADERS.copy()
        custom_headers["Origin"] = "https://example.com"
        
        response = requests.get(f"{BASE_URL}/supplements", headers=custom_headers, timeout=10)
        
        # Check if CORS headers are present
        cors_headers = [
            "Access-Control-Allow-Origin",
            "Access-Control-Allow-Methods",
            "Access-Control-Allow-Headers"
        ]
        
        found_cors_headers = []
        for header in cors_headers:
            if header in response.headers:
                found_cors_headers.append(header)
        
        if found_cors_headers:
            print(f"✅ CORS headers found: {found_cors_headers}")
        else:
            print("⚠️ No CORS headers found (might be configured at proxy level)")
        
        return True
    except Exception as e:
        print(f"❌ CORS test error: {e}")
        return False

def test_api_response_formats():
    """Test that API responses have consistent formats"""
    print("\n📋 Testing API Response Formats...")
    
    try:
        # Test supplements endpoint
        response = requests.get(f"{BASE_URL}/supplements", headers=HEADERS, timeout=10)
        if response.status_code == 200:
            supplements = response.json()
            if supplements and isinstance(supplements, list):
                supplement = supplements[0]
                required_fields = ["id", "name", "brand", "category", "priority"]
                missing_fields = [field for field in required_fields if field not in supplement]
                
                if not missing_fields:
                    print("✅ Supplements: Correct response format")
                else:
                    print(f"❌ Supplements: Missing fields - {missing_fields}")
                    return False
        
        # Test health tests endpoint
        response = requests.get(f"{BASE_URL}/health-tests", headers=HEADERS, timeout=10)
        if response.status_code == 200:
            tests = response.json()
            if tests and isinstance(tests, list):
                test = tests[0]
                required_fields = ["id", "name", "provider", "description"]
                missing_fields = [field for field in required_fields if field not in test]
                
                if not missing_fields:
                    print("✅ Health Tests: Correct response format")
                else:
                    print(f"❌ Health Tests: Missing fields - {missing_fields}")
                    return False
        
        return True
    except Exception as e:
        print(f"❌ Response format test error: {e}")
        return False

def main():
    """Run all integration tests"""
    print("🔗 Authentication Integration Tests")
    print("=" * 50)
    
    results = []
    
    results.append(test_public_endpoints())
    results.append(test_protected_endpoints_without_auth())
    results.append(test_protected_endpoints_with_auth())
    results.append(test_cors_and_headers())
    results.append(test_api_response_formats())
    
    print("\n📊 Integration Test Summary")
    print("-" * 30)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All integration tests passed!")
        return True
    else:
        print("⚠️ Some integration tests failed.")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)