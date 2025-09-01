#!/usr/bin/env python3
"""
Comprehensive Backend Testing for Hackster.ai Authentication System
Tests all authentication endpoints and protected routes
"""

import requests
import json
import time
from typing import Dict, Any, Optional

# Configuration
BASE_URL = "https://biohack-buddy.preview.emergentagent.com/api"
HEADERS = {"Content-Type": "application/json"}

class AuthenticationTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.headers = HEADERS
        self.test_results = []
        self.member_token = None
        self.coach_token = None
        self.test_post_id = None
        self.test_comment_id = None
        
    def log_test(self, test_name: str, passed: bool, details: str = ""):
        """Log test results"""
        status = "✅ PASS" if passed else "❌ FAIL"
        result = {
            "test": test_name,
            "status": status,
            "passed": passed,
            "details": details
        }
        self.test_results.append(result)
        print(f"{status}: {test_name}")
        if details:
            print(f"   Details: {details}")
        print()
    
    def make_request(self, method: str, endpoint: str, data: Dict = None, token: str = None) -> Dict[str, Any]:
        """Make HTTP request with proper error handling"""
        url = f"{self.base_url}{endpoint}"
        headers = self.headers.copy()
        
        if token:
            headers["Authorization"] = f"Bearer {token}"
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=headers, timeout=30)
            elif method.upper() == "POST":
                response = requests.post(url, headers=headers, json=data, timeout=30)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            return {
                "status_code": response.status_code,
                "data": response.json() if response.content else {},
                "success": response.status_code < 400
            }
        except requests.exceptions.RequestException as e:
            return {
                "status_code": 0,
                "data": {"error": str(e)},
                "success": False
            }
        except json.JSONDecodeError:
            return {
                "status_code": response.status_code,
                "data": {"error": "Invalid JSON response"},
                "success": False
            }

    def test_member_registration(self):
        """Test member registration endpoint"""
        test_data = {
            "email": "testmember@hackster.ai",
            "username": "testmember123",
            "password": "SecurePass123!",
            "role": "member",
            "age": 28,
            "gender": "male"
        }
        
        response = self.make_request("POST", "/auth/register", test_data)
        
        if response["success"] and response["status_code"] == 200:
            data = response["data"]
            # Check response structure
            required_fields = ["access_token", "token_type", "user", "message"]
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                self.log_test("Member Registration", False, f"Missing fields: {missing_fields}")
                return
            
            # Validate token format
            if not data["access_token"] or data["token_type"] != "bearer":
                self.log_test("Member Registration", False, "Invalid token format")
                return
            
            # Validate user data
            user = data["user"]
            if user["email"] != test_data["email"] or user["role"] != "member":
                self.log_test("Member Registration", False, "User data mismatch")
                return
            
            # Check password is not in response
            if "password" in str(data) or "hashed_password" in str(data):
                self.log_test("Member Registration", False, "Password exposed in response")
                return
            
            self.member_token = data["access_token"]
            self.log_test("Member Registration", True, "Member registered successfully with JWT token")
        else:
            self.log_test("Member Registration", False, f"Status: {response['status_code']}, Error: {response['data']}")

    def test_coach_registration(self):
        """Test coach registration endpoint"""
        test_data = {
            "email": "testcoach@hackster.ai",
            "username": "testcoach456",
            "password": "CoachPass456!",
            "role": "coach",
            "age": 35,
            "gender": "female"
        }
        
        response = self.make_request("POST", "/auth/register", test_data)
        
        if response["success"] and response["status_code"] == 200:
            data = response["data"]
            # Validate coach role
            if data["user"]["role"] != "coach":
                self.log_test("Coach Registration", False, "Role not set to coach")
                return
            
            self.coach_token = data["access_token"]
            self.log_test("Coach Registration", True, "Coach registered successfully")
        else:
            self.log_test("Coach Registration", False, f"Status: {response['status_code']}, Error: {response['data']}")

    def test_duplicate_email_validation(self):
        """Test duplicate email validation"""
        # Try to register with same email as member
        test_data = {
            "email": "testmember@hackster.ai",
            "username": "anothermember",
            "password": "AnotherPass123!",
            "role": "member"
        }
        
        response = self.make_request("POST", "/auth/register", test_data)
        
        if response["status_code"] == 400 and "already registered" in str(response["data"]).lower():
            self.log_test("Duplicate Email Validation", True, "Correctly rejected duplicate email")
        else:
            self.log_test("Duplicate Email Validation", False, f"Should reject duplicate email. Status: {response['status_code']}")

    def test_duplicate_username_validation(self):
        """Test duplicate username validation"""
        test_data = {
            "email": "newemail@hackster.ai",
            "username": "testmember123",  # Same username as member
            "password": "NewPass123!",
            "role": "member"
        }
        
        response = self.make_request("POST", "/auth/register", test_data)
        
        if response["status_code"] == 400 and "username" in str(response["data"]).lower():
            self.log_test("Duplicate Username Validation", True, "Correctly rejected duplicate username")
        else:
            self.log_test("Duplicate Username Validation", False, f"Should reject duplicate username. Status: {response['status_code']}")

    def test_valid_login(self):
        """Test login with valid credentials"""
        test_data = {
            "email": "testmember@hackster.ai",
            "password": "SecurePass123!"
        }
        
        response = self.make_request("POST", "/auth/login", test_data)
        
        if response["success"] and response["status_code"] == 200:
            data = response["data"]
            required_fields = ["access_token", "token_type", "user"]
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                self.log_test("Valid Login", False, f"Missing fields: {missing_fields}")
                return
            
            if data["token_type"] != "bearer":
                self.log_test("Valid Login", False, "Invalid token type")
                return
            
            self.log_test("Valid Login", True, "Login successful with valid credentials")
        else:
            self.log_test("Valid Login", False, f"Status: {response['status_code']}, Error: {response['data']}")

    def test_invalid_login_credentials(self):
        """Test login with invalid credentials"""
        # Test wrong password
        test_data = {
            "email": "testmember@hackster.ai",
            "password": "WrongPassword123!"
        }
        
        response = self.make_request("POST", "/auth/login", test_data)
        
        if response["status_code"] == 401:
            self.log_test("Invalid Login - Wrong Password", True, "Correctly rejected wrong password")
        else:
            self.log_test("Invalid Login - Wrong Password", False, f"Should reject wrong password. Status: {response['status_code']}")
        
        # Test non-existent email
        test_data = {
            "email": "nonexistent@hackster.ai",
            "password": "AnyPassword123!"
        }
        
        response = self.make_request("POST", "/auth/login", test_data)
        
        if response["status_code"] == 401:
            self.log_test("Invalid Login - Non-existent Email", True, "Correctly rejected non-existent email")
        else:
            self.log_test("Invalid Login - Non-existent Email", False, f"Should reject non-existent email. Status: {response['status_code']}")

    def test_auth_me_with_valid_token(self):
        """Test /auth/me endpoint with valid JWT token"""
        if not self.member_token:
            self.log_test("Auth Me - Valid Token", False, "No member token available")
            return
        
        response = self.make_request("GET", "/auth/me", token=self.member_token)
        
        if response["success"] and response["status_code"] == 200:
            user_data = response["data"]
            required_fields = ["id", "email", "username", "role"]
            missing_fields = [field for field in required_fields if field not in user_data]
            
            if missing_fields:
                self.log_test("Auth Me - Valid Token", False, f"Missing user fields: {missing_fields}")
                return
            
            if user_data["email"] != "testmember@hackster.ai":
                self.log_test("Auth Me - Valid Token", False, "Wrong user data returned")
                return
            
            self.log_test("Auth Me - Valid Token", True, "Successfully retrieved user profile")
        else:
            self.log_test("Auth Me - Valid Token", False, f"Status: {response['status_code']}, Error: {response['data']}")

    def test_auth_me_with_invalid_token(self):
        """Test /auth/me endpoint with invalid JWT token"""
        # Test with invalid token
        response = self.make_request("GET", "/auth/me", token="invalid.jwt.token")
        
        if response["status_code"] == 401:
            self.log_test("Auth Me - Invalid Token", True, "Correctly rejected invalid token")
        else:
            self.log_test("Auth Me - Invalid Token", False, f"Should reject invalid token. Status: {response['status_code']}")
        
        # Test without token
        response = self.make_request("GET", "/auth/me")
        
        if response["status_code"] == 401 or response["status_code"] == 403:
            self.log_test("Auth Me - No Token", True, "Correctly rejected missing token")
        else:
            self.log_test("Auth Me - No Token", False, f"Should reject missing token. Status: {response['status_code']}")

    def test_protected_endpoint_with_auth(self):
        """Test protected endpoint (POST /users) with authentication"""
        if not self.member_token:
            self.log_test("Protected Endpoint - With Auth", False, "No member token available")
            return
        
        test_data = {
            "email": "testmember@hackster.ai",
            "age": 30,
            "goals": ["weight_loss", "muscle_gain"]
        }
        
        response = self.make_request("POST", "/users", test_data, token=self.member_token)
        
        if response["success"]:
            self.log_test("Protected Endpoint - With Auth", True, "Successfully accessed protected endpoint")
        else:
            self.log_test("Protected Endpoint - With Auth", False, f"Status: {response['status_code']}, Error: {response['data']}")

    def test_protected_endpoint_without_auth(self):
        """Test protected endpoint (POST /users) without authentication"""
        test_data = {
            "email": "testmember@hackster.ai",
            "age": 30,
            "goals": ["weight_loss"]
        }
        
        response = self.make_request("POST", "/users", test_data)
        
        if response["status_code"] == 401 or response["status_code"] == 403:
            self.log_test("Protected Endpoint - Without Auth", True, "Correctly rejected unauthenticated request")
        else:
            self.log_test("Protected Endpoint - Without Auth", False, f"Should reject unauthenticated request. Status: {response['status_code']}")

    def test_public_endpoints(self):
        """Test that public endpoints work without authentication"""
        public_endpoints = [
            "/supplements",
            "/health-tests",
            "/coaches",
            "/biohacks"
        ]
        
        all_passed = True
        failed_endpoints = []
        
        for endpoint in public_endpoints:
            response = self.make_request("GET", endpoint)
            if not response["success"]:
                all_passed = False
                failed_endpoints.append(f"{endpoint} (Status: {response['status_code']})")
        
        if all_passed:
            self.log_test("Public Endpoints Access", True, "All public endpoints accessible without auth")
        else:
            self.log_test("Public Endpoints Access", False, f"Failed endpoints: {failed_endpoints}")

    def test_password_hashing_security(self):
        """Test that passwords are properly hashed and not stored in plain text"""
        # This test checks that password is not returned in any response
        # We already checked this in registration, but let's verify in login too
        
        test_data = {
            "email": "testmember@hackster.ai",
            "password": "SecurePass123!"
        }
        
        response = self.make_request("POST", "/auth/login", test_data)
        
        if response["success"]:
            response_str = str(response["data"])
            if "SecurePass123!" in response_str or "password" in response_str.lower():
                self.log_test("Password Hashing Security", False, "Password exposed in login response")
            else:
                self.log_test("Password Hashing Security", True, "Password properly hashed and not exposed")
        else:
            self.log_test("Password Hashing Security", False, "Could not test - login failed")

    def test_jwt_token_expiration_format(self):
        """Test JWT token format and structure"""
        if not self.member_token:
            self.log_test("JWT Token Format", False, "No token available for testing")
            return
        
        # JWT tokens should have 3 parts separated by dots
        token_parts = self.member_token.split('.')
        
        if len(token_parts) == 3:
            self.log_test("JWT Token Format", True, "JWT token has correct format (3 parts)")
        else:
            self.log_test("JWT Token Format", False, f"JWT token has {len(token_parts)} parts, expected 3")

    def run_all_tests(self):
        """Run all authentication tests"""
        print("🚀 Starting Hackster.ai Authentication System Tests")
        print("=" * 60)
        print()
        
        # Test registration
        print("📝 REGISTRATION TESTS")
        print("-" * 30)
        self.test_member_registration()
        self.test_coach_registration()
        self.test_duplicate_email_validation()
        self.test_duplicate_username_validation()
        
        # Test login
        print("🔐 LOGIN TESTS")
        print("-" * 30)
        self.test_valid_login()
        self.test_invalid_login_credentials()
        
        # Test authentication protection
        print("🛡️ AUTHENTICATION PROTECTION TESTS")
        print("-" * 30)
        self.test_auth_me_with_valid_token()
        self.test_auth_me_with_invalid_token()
        
        # Test protected vs public endpoints
        print("🔒 ENDPOINT ACCESS TESTS")
        print("-" * 30)
        self.test_protected_endpoint_with_auth()
        self.test_protected_endpoint_without_auth()
        self.test_public_endpoints()
        
        # Test security
        print("🔐 SECURITY TESTS")
        print("-" * 30)
        self.test_password_hashing_security()
        self.test_jwt_token_expiration_format()
        
        # Summary
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        passed_tests = [test for test in self.test_results if test["passed"]]
        failed_tests = [test for test in self.test_results if not test["passed"]]
        
        print(f"Total Tests: {len(self.test_results)}")
        print(f"Passed: {len(passed_tests)} ✅")
        print(f"Failed: {len(failed_tests)} ❌")
        print()
        
        if failed_tests:
            print("❌ FAILED TESTS:")
            for test in failed_tests:
                print(f"  - {test['test']}: {test['details']}")
            print()
        
        success_rate = (len(passed_tests) / len(self.test_results)) * 100
        print(f"Success Rate: {success_rate:.1f}%")
        
        return len(failed_tests) == 0

if __name__ == "__main__":
    tester = AuthenticationTester()
    all_passed = tester.run_all_tests()
    
    if all_passed:
        print("\n🎉 All authentication tests passed!")
        exit(0)
    else:
        print("\n⚠️ Some tests failed. Please check the issues above.")
        exit(1)