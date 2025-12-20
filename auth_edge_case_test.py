#!/usr/bin/env python3
"""
Additional Edge Case Tests for Authentication System
Tests JWT token expiration, email validation, and other edge cases
"""

import requests
import json
import time
from jose import jwt, JWTError
import base64

BASE_URL = "https://lab-connect-3.preview.emergentagent.com/api"
HEADERS = {"Content-Type": "application/json"}

def test_email_validation():
    """Test email validation with invalid email formats"""
    print("🧪 Testing Email Validation...")
    
    invalid_emails = [
        "invalid-email",
        "test@",
        "@domain.com",
        "test..test@domain.com",
        "test@domain",
        ""
    ]
    
    for email in invalid_emails:
        test_data = {
            "email": email,
            "username": f"user_{email.replace('@', '_').replace('.', '_')}",
            "password": "ValidPass123!",
            "role": "member"
        }
        
        try:
            response = requests.post(f"{BASE_URL}/auth/register", json=test_data, headers=HEADERS, timeout=10)
            if response.status_code == 422:  # Validation error
                print(f"✅ Correctly rejected invalid email: {email}")
            else:
                print(f"❌ Should reject invalid email: {email} (Status: {response.status_code})")
        except Exception as e:
            print(f"❌ Error testing email {email}: {e}")

def test_password_requirements():
    """Test password strength requirements"""
    print("\n🔒 Testing Password Requirements...")
    
    weak_passwords = [
        "123",
        "password",
        "abc",
        "",
        "a"
    ]
    
    for password in weak_passwords:
        test_data = {
            "email": f"test_{len(password)}@hackster.ai",
            "username": f"user_{len(password)}",
            "password": password,
            "role": "member"
        }
        
        try:
            response = requests.post(f"{BASE_URL}/auth/register", json=test_data, headers=HEADERS, timeout=10)
            # Note: The current implementation doesn't enforce password strength, 
            # but we're testing to see current behavior
            print(f"Password '{password}': Status {response.status_code}")
        except Exception as e:
            print(f"❌ Error testing password: {e}")

def test_jwt_token_structure():
    """Test JWT token structure and claims"""
    print("\n🎫 Testing JWT Token Structure...")
    
    # Register a user to get a token
    test_data = {
        "email": "jwt_test@hackster.ai",
        "username": "jwt_test_user",
        "password": "JWTTest123!",
        "role": "member"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/register", json=test_data, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            token = response.json()["access_token"]
            
            # Decode JWT token (without verification for inspection)
            try:
                # Split token and decode payload
                parts = token.split('.')
                if len(parts) == 3:
                    # Add padding if needed
                    payload = parts[1]
                    payload += '=' * (4 - len(payload) % 4)
                    decoded_payload = base64.urlsafe_b64decode(payload)
                    claims = json.loads(decoded_payload)
                    
                    print(f"✅ JWT Token decoded successfully")
                    print(f"   Subject (sub): {claims.get('sub', 'Not found')}")
                    print(f"   Expiration (exp): {claims.get('exp', 'Not found')}")
                    
                    # Check if expiration is set (should be 30 minutes from now)
                    if 'exp' in claims:
                        exp_time = claims['exp']
                        current_time = time.time()
                        time_diff = exp_time - current_time
                        print(f"   Time until expiration: {time_diff/60:.1f} minutes")
                        
                        if 25 <= time_diff/60 <= 35:  # Should be around 30 minutes
                            print("✅ Token expiration time is correct (~30 minutes)")
                        else:
                            print(f"❌ Token expiration time seems incorrect: {time_diff/60:.1f} minutes")
                    else:
                        print("❌ No expiration claim found in token")
                else:
                    print("❌ Invalid JWT token format")
                    
            except Exception as e:
                print(f"❌ Error decoding JWT token: {e}")
        else:
            print(f"❌ Failed to register user for JWT testing: {response.status_code}")
    except Exception as e:
        print(f"❌ Error in JWT token test: {e}")

def test_role_validation():
    """Test user role validation"""
    print("\n👥 Testing Role Validation...")
    
    # Test valid roles
    valid_roles = ["member", "coach"]
    for role in valid_roles:
        test_data = {
            "email": f"role_test_{role}@hackster.ai",
            "username": f"role_test_{role}",
            "password": "RoleTest123!",
            "role": role
        }
        
        try:
            response = requests.post(f"{BASE_URL}/auth/register", json=test_data, headers=HEADERS, timeout=10)
            if response.status_code == 200:
                user_role = response.json()["user"]["role"]
                if user_role == role:
                    print(f"✅ Role '{role}' correctly assigned")
                else:
                    print(f"❌ Role mismatch: expected '{role}', got '{user_role}'")
            else:
                print(f"❌ Failed to register user with role '{role}': {response.status_code}")
        except Exception as e:
            print(f"❌ Error testing role '{role}': {e}")
    
    # Test invalid role
    test_data = {
        "email": "invalid_role@hackster.ai",
        "username": "invalid_role_user",
        "password": "InvalidRole123!",
        "role": "invalid_role"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/register", json=test_data, headers=HEADERS, timeout=10)
        if response.status_code == 422:  # Validation error expected
            print("✅ Correctly rejected invalid role")
        else:
            print(f"❌ Should reject invalid role (Status: {response.status_code})")
    except Exception as e:
        print(f"❌ Error testing invalid role: {e}")

def test_concurrent_registrations():
    """Test handling of concurrent registrations with same email"""
    print("\n⚡ Testing Concurrent Registration Handling...")
    
    # This is a basic test - in production you'd want proper concurrency testing
    test_data = {
        "email": "concurrent_test@hackster.ai",
        "username": "concurrent_user",
        "password": "ConcurrentTest123!",
        "role": "member"
    }
    
    try:
        # First registration
        response1 = requests.post(f"{BASE_URL}/auth/register", json=test_data, headers=HEADERS, timeout=10)
        
        # Second registration with same email but different username
        test_data["username"] = "concurrent_user2"
        response2 = requests.post(f"{BASE_URL}/auth/register", json=test_data, headers=HEADERS, timeout=10)
        
        if response1.status_code == 200 and response2.status_code == 400:
            print("✅ Correctly handled concurrent registration attempt")
        else:
            print(f"❌ Concurrent registration handling issue: {response1.status_code}, {response2.status_code}")
            
    except Exception as e:
        print(f"❌ Error in concurrent registration test: {e}")

def main():
    """Run all edge case tests"""
    print("🧪 Authentication Edge Case Tests")
    print("=" * 50)
    
    test_email_validation()
    test_password_requirements()
    test_jwt_token_structure()
    test_role_validation()
    test_concurrent_registrations()
    
    print("\n✅ Edge case testing completed!")

if __name__ == "__main__":
    main()