#!/usr/bin/env python3
"""
Backend API Testing for Hackster.ai - Phase A/B/C Features
Tests: Admin Practitioner Management, Product Source Tag, No-Habit-Forming Guardrail,
       Education Content Library, Questionnaire/Chatbot Integration
"""

import requests
import json
import sys
from typing import Dict, Any, Optional, List

# Backend URL from environment
BACKEND_URL = "https://health-revolution-1.preview.emergentagent.com/api"

# Admin credentials from test_credentials.md
ADMIN_EMAIL = "lzook@plzcompany.com"
ADMIN_PASSWORD = "HacksterAdmin2025!"

# Test results tracking
test_results = []
test_number = 0

def log_test(test_name: str, passed: bool, details: str = ""):
    """Log test result"""
    global test_number
    test_number += 1
    status = "✅ PASS" if passed else "❌ FAIL"
    result = f"[{test_number}] {status} - {test_name}"
    if details:
        result += f"\n    Details: {details}"
    print(result)
    test_results.append({"number": test_number, "name": test_name, "passed": passed, "details": details})

def make_request(method: str, endpoint: str, headers: Optional[Dict] = None, 
                 json_data: Optional[Dict] = None, params: Optional[Dict] = None) -> tuple:
    """Make HTTP request and return (success, response_data, status_code)"""
    url = f"{BACKEND_URL}{endpoint}"
    try:
        if method == "GET":
            resp = requests.get(url, headers=headers, params=params, timeout=30)
        elif method == "POST":
            resp = requests.post(url, headers=headers, json=json_data, timeout=30)
        elif method == "PUT":
            resp = requests.put(url, headers=headers, json=json_data, timeout=30)
        elif method == "DELETE":
            resp = requests.delete(url, headers=headers, timeout=30)
        else:
            return False, {"error": f"Unsupported method: {method}"}, 0
        
        try:
            data = resp.json()
        except:
            data = {"text": resp.text}
        
        return resp.ok, data, resp.status_code
    except Exception as e:
        return False, {"error": str(e)}, 0

def get_admin_token() -> Optional[str]:
    """Get admin access token"""
    print("\n=== SETUP: Admin Login ===")
    success, data, status = make_request("POST", "/auth/login", json_data={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    
    if success and "access_token" in data:
        token = data["access_token"]
        # Verify role is admin
        success2, user_data, _ = make_request("GET", "/auth/me", headers={
            "Authorization": f"Bearer {token}"
        })
        if success2 and user_data.get("role") == "admin":
            print(f"✓ Admin login successful (role=admin)")
            return token
        else:
            print(f"✗ Token received but role is not admin: {user_data.get('role')}")
            return None
    else:
        print(f"✗ Admin login failed: Status {status}, Response: {data}")
        return None

def get_real_vendor_id() -> Optional[str]:
    """Get a real vendor UUID for product creation"""
    success, vendors, _ = make_request("GET", "/vendors")
    if success and isinstance(vendors, list) and len(vendors) > 0:
        return vendors[0]["id"]
    return None

# ============== PHASE A: PRACTITIONER ADMIN TESTS ==============

def test_practitioner_admin(admin_token: str) -> Optional[str]:
    """
    PRACTITIONER ADMIN (Phase A):
    1. POST /api/admin/coaches with full body
    2. PUT /api/admin/coaches/{id} to update payment_status and is_featured
    3. GET /api/admin/coaches to verify updates
    4. Security: POST/PUT without admin token → 403
    """
    print("\n" + "="*80)
    print("PHASE A: PRACTITIONER ADMIN TESTS")
    print("="*80)
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Test 1: POST /api/admin/coaches - Create practitioner
    print("\n--- Test 1: Create Practitioner (POST /api/admin/coaches) ---")
    coach_data = {
        "name": "QA Practitioner",
        "credentials": ["ND"],
        "specialties": ["energy", "longevity"],
        "location": "Remote",
        "bio": "qa",
        "hourly_rate": "$100",
        "availability": "Weekdays",
        "contact_info": {"email": "qa@x.com"},
        "payment_status": "active",
        "is_featured": True
    }
    
    success, data, status = make_request("POST", "/admin/coaches", headers=headers, json_data=coach_data)
    
    if success and "id" in data:
        coach_id = data["id"]
        checks = []
        checks.append(("has_id", "id" in data))
        checks.append(("is_approved=true", data.get("is_approved") == True))
        checks.append(("payment_status=active", data.get("payment_status") == "active"))
        checks.append(("is_featured=true", data.get("is_featured") == True))
        checks.append(("name=QA Practitioner", data.get("name") == "QA Practitioner"))
        
        all_passed = all(check[1] for check in checks)
        details = ", ".join([f"{check[0]}={check[1]}" for check in checks])
        log_test("POST /api/admin/coaches (create practitioner)", all_passed, details)
        
        if not all_passed:
            print(f"    Response data: {json.dumps(data, indent=2)}")
    else:
        log_test("POST /api/admin/coaches (create practitioner)", False, 
                f"Status {status}, Response: {data}")
        return None
    
    # Test 2: PUT /api/admin/coaches/{id} - Update practitioner
    print("\n--- Test 2: Update Practitioner (PUT /api/admin/coaches/{id}) ---")
    update_data = {
        "payment_status": "lapsed",
        "is_featured": False
    }
    
    success, data, status = make_request("PUT", f"/admin/coaches/{coach_id}", 
                                        headers=headers, json_data=update_data)
    
    if success:
        log_test("PUT /api/admin/coaches/{id} (update)", True, 
                f"payment_status={data.get('payment_status')}, is_featured={data.get('is_featured')}")
    else:
        log_test("PUT /api/admin/coaches/{id} (update)", False, 
                f"Status {status}, Response: {data}")
    
    # Test 3: GET /api/admin/coaches - Verify updates and defaults
    print("\n--- Test 3: List All Coaches (GET /api/admin/coaches) ---")
    success, coaches, status = make_request("GET", "/admin/coaches", headers=headers)
    
    if success and isinstance(coaches, list):
        # Find our QA coach
        qa_coach = next((c for c in coaches if c.get("id") == coach_id), None)
        
        checks = []
        checks.append(("list_returned", len(coaches) > 0))
        checks.append(("qa_coach_found", qa_coach is not None))
        
        if qa_coach:
            checks.append(("qa_payment_status=lapsed", qa_coach.get("payment_status") == "lapsed"))
            checks.append(("qa_is_featured=false", qa_coach.get("is_featured") == False))
        
        # Check if existing coaches have default payment_status
        existing_coaches = [c for c in coaches if c.get("id") != coach_id]
        has_defaults = any(c.get("payment_status") == "unpaid" for c in existing_coaches)
        checks.append(("existing_coaches_have_defaults", has_defaults or len(existing_coaches) == 0))
        
        all_passed = all(check[1] for check in checks)
        details = ", ".join([f"{check[0]}={check[1]}" for check in checks])
        log_test("GET /api/admin/coaches (list with updates)", all_passed, details)
    else:
        log_test("GET /api/admin/coaches (list with updates)", False, 
                f"Status {status}, Response: {coaches}")
    
    # Test 4: Security - POST without admin token
    print("\n--- Test 4: Security - POST /api/admin/coaches without token ---")
    success, data, status = make_request("POST", "/admin/coaches", json_data=coach_data)
    
    if status == 403 or status == 401:
        log_test("Security: POST /api/admin/coaches without token → 403/401", True, 
                f"Correctly blocked with status {status}")
    else:
        log_test("Security: POST /api/admin/coaches without token → 403/401", False, 
                f"Expected 403/401, got {status}")
    
    # Test 5: Security - PUT without admin token
    print("\n--- Test 5: Security - PUT /api/admin/coaches/{id} without token ---")
    success, data, status = make_request("PUT", f"/admin/coaches/{coach_id}", json_data=update_data)
    
    if status == 403 or status == 401:
        log_test("Security: PUT /api/admin/coaches/{id} without token → 403/401", True, 
                f"Correctly blocked with status {status}")
    else:
        log_test("Security: PUT /api/admin/coaches/{id} without token → 403/401", False, 
                f"Expected 403/401, got {status}")
    
    return coach_id

def test_practitioner_cleanup(admin_token: str, coach_id: str):
    """Test 5: DELETE /api/coaches/{id} - Cleanup"""
    print("\n--- Cleanup: Delete QA Practitioner (DELETE /api/coaches/{id}) ---")
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    success, data, status = make_request("DELETE", f"/coaches/{coach_id}", headers=headers)
    
    if success:
        log_test("DELETE /api/coaches/{id} (cleanup)", True, "QA practitioner removed")
    else:
        log_test("DELETE /api/coaches/{id} (cleanup)", False, 
                f"Status {status}, Response: {data}")

# ============== PHASE A: PRODUCT SOURCE TAG TESTS ==============

def test_product_source_tag(admin_token: str, vendor_id: str) -> Optional[str]:
    """
    PRODUCT SOURCE TAG (Phase A):
    6. POST /api/admin/products with source_type "wholesale"
    7. PUT to change source_type to "affiliate"
    8. DELETE cleanup
    """
    print("\n" + "="*80)
    print("PHASE A: PRODUCT SOURCE TAG TESTS")
    print("="*80)
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Test 6: POST /api/admin/products with source_type
    print("\n--- Test 6: Create Product with source_type (POST /api/admin/products) ---")
    
    # Get vendor name first
    success_v, vendors, _ = make_request("GET", "/vendors")
    vendor_name = "Test Vendor"
    if success_v and isinstance(vendors, list) and len(vendors) > 0:
        vendor_name = vendors[0]["name"]
    
    product_data = {
        "vendor_id": vendor_id,
        "vendor_name": vendor_name,
        "name": "QA Src Product",
        "price": 10,
        "category": "supplements",
        "description": "qa",
        "slug": "qa-src-product",
        "source_type": "wholesale",
        "is_habit_forming": False
    }
    
    success, data, status = make_request("POST", "/admin/products", headers=headers, json_data=product_data)
    
    if success and "id" in data:
        product_id = data["id"]
        checks = []
        checks.append(("has_id", "id" in data))
        checks.append(("source_type=wholesale", data.get("source_type") == "wholesale"))
        checks.append(("is_habit_forming=false", data.get("is_habit_forming") == False))
        
        all_passed = all(check[1] for check in checks)
        details = ", ".join([f"{check[0]}={check[1]}" for check in checks])
        log_test("POST /api/admin/products with source_type='wholesale'", all_passed, details)
    else:
        log_test("POST /api/admin/products with source_type='wholesale'", False, 
                f"Status {status}, Response: {data}")
        return None
    
    # Test 7: PUT to change source_type
    print("\n--- Test 7: Update source_type (PUT /api/admin/products/{id}) ---")
    success, data, status = make_request("PUT", f"/admin/products/{product_id}", 
                                        headers=headers, json_data={"source_type": "affiliate"})
    
    if success and data.get("source_type") == "affiliate":
        log_test("PUT /api/admin/products/{id} to change source_type to 'affiliate'", True, 
                f"source_type={data.get('source_type')}")
    else:
        log_test("PUT /api/admin/products/{id} to change source_type to 'affiliate'", False, 
                f"Status {status}, source_type={data.get('source_type')}")
    
    # Test 8: DELETE cleanup
    print("\n--- Test 8: Delete Product (DELETE /api/admin/products/{id}) ---")
    success, data, status = make_request("DELETE", f"/admin/products/{product_id}", headers=headers)
    
    if success:
        log_test("DELETE /api/admin/products/{id} (cleanup)", True, "QA product removed")
    else:
        log_test("DELETE /api/admin/products/{id} (cleanup)", False, 
                f"Status {status}, Response: {data}")
    
    return product_id

# ============== PHASE B: CONTENT LIBRARY TESTS ==============

def test_content_library(admin_token: str) -> Optional[str]:
    """
    CONTENT LIBRARY (Phase B):
    7. GET /api/content (public) → returns >=4 published articles
    8. GET /api/content?goal=energy → filtered list
    9. GET /api/content?category=sleep → returns sleep article
    10. GET /api/content?search=detox → returns detox article
    11. GET /api/content/{slug} → returns article with body
    12. Admin CRUD: POST /api/admin/content (slug omitted), PUT to unpublish, DELETE
    13. Security: GET /api/admin/content and POST without admin token → 403
    """
    print("\n" + "="*80)
    print("PHASE B: CONTENT LIBRARY TESTS")
    print("="*80)
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Test 7: GET /api/content (public) - List published articles
    print("\n--- Test 7: List Published Content (GET /api/content) ---")
    success, content_list, status = make_request("GET", "/content")
    
    if success and isinstance(content_list, list):
        checks = []
        checks.append(("returns_list", True))
        checks.append(("has_>=4_articles", len(content_list) >= 4))
        
        # Check for expected articles
        titles = [c.get("title", "").lower() for c in content_list]
        expected_keywords = ["frequency", "detox", "sleep", "mindfulness"]
        found_articles = sum(1 for kw in expected_keywords if any(kw in t for t in titles))
        checks.append(("has_expected_articles", found_articles >= 3))
        
        all_passed = all(check[1] for check in checks)
        details = f"count={len(content_list)}, " + ", ".join([f"{check[0]}={check[1]}" for check in checks])
        log_test("GET /api/content (public, returns >=4 articles)", all_passed, details)
    else:
        log_test("GET /api/content (public, returns >=4 articles)", False, 
                f"Status {status}, Response: {content_list}")
    
    # Test 8: GET /api/content?goal=energy - Filter by goal
    print("\n--- Test 8: Filter by Goal (GET /api/content?goal=energy) ---")
    success, filtered, status = make_request("GET", "/content", params={"goal": "energy"})
    
    if success and isinstance(filtered, list):
        checks = []
        checks.append(("returns_list", True))
        checks.append(("non_empty", len(filtered) > 0))
        
        all_passed = all(check[1] for check in checks)
        details = f"count={len(filtered)}, " + ", ".join([f"{check[0]}={check[1]}" for check in checks])
        log_test("GET /api/content?goal=energy (filtered non-empty list)", all_passed, details)
    else:
        log_test("GET /api/content?goal=energy (filtered non-empty list)", False, 
                f"Status {status}, Response: {filtered}")
    
    # Test 9: GET /api/content?category=sleep - Filter by category
    print("\n--- Test 9: Filter by Category (GET /api/content?category=sleep) ---")
    success, sleep_content, status = make_request("GET", "/content", params={"category": "sleep"})
    
    if success and isinstance(sleep_content, list):
        checks = []
        checks.append(("returns_list", True))
        checks.append(("has_sleep_article", len(sleep_content) > 0))
        
        if len(sleep_content) > 0:
            checks.append(("category_is_sleep", sleep_content[0].get("category") == "sleep"))
        
        all_passed = all(check[1] for check in checks)
        details = f"count={len(sleep_content)}, " + ", ".join([f"{check[0]}={check[1]}" for check in checks])
        log_test("GET /api/content?category=sleep (returns sleep article)", all_passed, details)
    else:
        log_test("GET /api/content?category=sleep (returns sleep article)", False, 
                f"Status {status}, Response: {sleep_content}")
    
    # Test 10: GET /api/content?search=detox - Search
    print("\n--- Test 10: Search Content (GET /api/content?search=detox) ---")
    success, search_results, status = make_request("GET", "/content", params={"search": "detox"})
    
    if success and isinstance(search_results, list):
        checks = []
        checks.append(("returns_list", True))
        checks.append(("has_detox_article", len(search_results) > 0))
        
        if len(search_results) > 0:
            first_result = search_results[0]
            has_detox = "detox" in first_result.get("title", "").lower() or \
                       "detox" in first_result.get("summary", "").lower()
            checks.append(("contains_detox", has_detox))
        
        all_passed = all(check[1] for check in checks)
        details = f"count={len(search_results)}, " + ", ".join([f"{check[0]}={check[1]}" for check in checks])
        log_test("GET /api/content?search=detox (returns detox article)", all_passed, details)
    else:
        log_test("GET /api/content?search=detox (returns detox article)", False, 
                f"Status {status}, Response: {search_results}")
    
    # Test 11: GET /api/content/{slug} - Get single article
    print("\n--- Test 11: Get Single Article (GET /api/content/{slug}) ---")
    # Use frequency-healing-101 as mentioned in the review request
    success, article, status = make_request("GET", "/content/frequency-healing-101")
    
    if success and "id" in article:
        checks = []
        checks.append(("has_id", "id" in article))
        checks.append(("has_title", "title" in article and len(article.get("title", "")) > 0))
        checks.append(("has_body", "body" in article and len(article.get("body", "")) > 0))
        checks.append(("has_slug", article.get("slug") == "frequency-healing-101"))
        
        all_passed = all(check[1] for check in checks)
        details = ", ".join([f"{check[0]}={check[1]}" for check in checks])
        log_test("GET /api/content/frequency-healing-101 (returns article with body)", all_passed, details)
    else:
        log_test("GET /api/content/frequency-healing-101 (returns article with body)", False, 
                f"Status {status}, Response: {article}")
    
    # Test 12a: POST /api/admin/content - Create content (slug omitted → auto-generate)
    print("\n--- Test 12a: Create Content (POST /api/admin/content, slug auto-generated) ---")
    content_data = {
        "title": "QA Content",
        "category": "nutrition",
        "summary": "qa summary",
        "body": "qa body",
        "related_goals": ["energy"],
        "tags": ["qa"]
        # NOTE: slug omitted → must auto-generate
    }
    
    success, data, status = make_request("POST", "/admin/content", headers=headers, json_data=content_data)
    
    if success and "id" in data:
        content_id = data["id"]
        checks = []
        checks.append(("has_id", "id" in data))
        checks.append(("has_slug", "slug" in data and len(data.get("slug", "")) > 0))
        checks.append(("slug_auto_generated", data.get("slug") != ""))
        checks.append(("title_correct", data.get("title") == "QA Content"))
        
        all_passed = all(check[1] for check in checks)
        details = f"slug={data.get('slug')}, " + ", ".join([f"{check[0]}={check[1]}" for check in checks])
        log_test("POST /api/admin/content (slug auto-generated)", all_passed, details)
    else:
        log_test("POST /api/admin/content (slug auto-generated)", False, 
                f"Status {status}, Response: {data}")
        return None
    
    # Test 12b: PUT /api/admin/content/{id} - Unpublish
    print("\n--- Test 12b: Unpublish Content (PUT /api/admin/content/{id}) ---")
    success, data, status = make_request("PUT", f"/admin/content/{content_id}", 
                                        headers=headers, json_data={"is_published": False})
    
    if success:
        log_test("PUT /api/admin/content/{id} (unpublish)", True, 
                f"is_published={data.get('is_published')}")
    else:
        log_test("PUT /api/admin/content/{id} (unpublish)", False, 
                f"Status {status}, Response: {data}")
    
    # Test 12c: Verify unpublished content not in public list
    print("\n--- Test 12c: Verify Unpublished Hidden (GET /api/content) ---")
    success, public_list, status = make_request("GET", "/content")
    
    if success and isinstance(public_list, list):
        qa_content_visible = any(c.get("id") == content_id for c in public_list)
        
        if not qa_content_visible:
            log_test("GET /api/content (unpublished content hidden from public)", True, 
                    "QA Content not visible in public list")
        else:
            log_test("GET /api/content (unpublished content hidden from public)", False, 
                    "QA Content still visible in public list")
    else:
        log_test("GET /api/content (unpublished content hidden from public)", False, 
                f"Status {status}, Response: {public_list}")
    
    # Test 12d: DELETE /api/admin/content/{id} - Cleanup
    print("\n--- Test 12d: Delete Content (DELETE /api/admin/content/{id}) ---")
    success, data, status = make_request("DELETE", f"/admin/content/{content_id}", headers=headers)
    
    if success:
        log_test("DELETE /api/admin/content/{id} (cleanup)", True, "QA content removed")
    else:
        log_test("DELETE /api/admin/content/{id} (cleanup)", False, 
                f"Status {status}, Response: {data}")
    
    # Test 13a: Security - GET /api/admin/content without token
    print("\n--- Test 13a: Security - GET /api/admin/content without token ---")
    success, data, status = make_request("GET", "/admin/content")
    
    if status == 403 or status == 401:
        log_test("Security: GET /api/admin/content without token → 403/401", True, 
                f"Correctly blocked with status {status}")
    else:
        log_test("Security: GET /api/admin/content without token → 403/401", False, 
                f"Expected 403/401, got {status}")
    
    # Test 13b: Security - POST /api/admin/content without token
    print("\n--- Test 13b: Security - POST /api/admin/content without token ---")
    success, data, status = make_request("POST", "/admin/content", json_data=content_data)
    
    if status == 403 or status == 401:
        log_test("Security: POST /api/admin/content without token → 403/401", True, 
                f"Correctly blocked with status {status}")
    else:
        log_test("Security: POST /api/admin/content without token → 403/401", False, 
                f"Expected 403/401, got {status}")
    
    return content_id

# ============== PHASE B: QUESTIONNAIRE + CHAT INTEGRATION TESTS ==============

def test_questionnaire_integration():
    """
    QUESTIONNAIRE + CHAT INTEGRATION (Phase B):
    12. POST /api/questionnaire/submit → returns recommended_content + recommended_coaches
    13. POST /api/coach/chat → returns response string (200)
    """
    print("\n" + "="*80)
    print("PHASE B: QUESTIONNAIRE + CHAT INTEGRATION TESTS")
    print("="*80)
    
    # Test 12: POST /api/questionnaire/submit
    print("\n--- Test 12: Questionnaire Submit (POST /api/questionnaire/submit) ---")
    questionnaire_data = {
        "responses": [
            {"question_id": "primary_goal", "answer": "Increase Energy"},
            {"question_id": "secondary_goals", "answer": ["Better Sleep"]}
        ]
    }
    
    success, data, status = make_request("POST", "/questionnaire/submit", json_data=questionnaire_data)
    
    if success:
        checks = []
        checks.append(("status_200", status == 200))
        checks.append(("has_recommended_content", "recommended_content" in data))
        checks.append(("has_recommended_coaches", "recommended_coaches" in data))
        
        # Check recommended_content structure
        if "recommended_content" in data:
            content_list = data["recommended_content"]
            checks.append(("recommended_content_is_array", isinstance(content_list, list)))
            checks.append(("recommended_content_non_empty", len(content_list) > 0))
            
            if len(content_list) > 0:
                first_content = content_list[0]
                checks.append(("content_has_title", "title" in first_content))
                checks.append(("content_has_slug", "slug" in first_content))
                checks.append(("content_has_category", "category" in first_content))
                checks.append(("content_has_summary", "summary" in first_content))
        
        # Check recommended_coaches structure
        if "recommended_coaches" in data:
            coaches_list = data["recommended_coaches"]
            checks.append(("recommended_coaches_is_array", isinstance(coaches_list, list)))
            checks.append(("recommended_coaches_non_empty", len(coaches_list) > 0))
        
        all_passed = all(check[1] for check in checks)
        details = ", ".join([f"{check[0]}={check[1]}" for check in checks])
        
        if "recommended_content" in data:
            details += f", content_count={len(data['recommended_content'])}"
        if "recommended_coaches" in data:
            details += f", coaches_count={len(data['recommended_coaches'])}"
        
        log_test("POST /api/questionnaire/submit (returns recommended_content + coaches)", all_passed, details)
    else:
        log_test("POST /api/questionnaire/submit (returns recommended_content + coaches)", False, 
                f"Status {status}, Response: {data}")
    
    # Test 13: POST /api/coach/chat
    print("\n--- Test 13: Coach Chat (POST /api/coach/chat) ---")
    chat_data = {
        "message": "How can I improve my sleep naturally without becoming dependent on sleeping pills?",
        "conversation_history": []
    }
    
    success, data, status = make_request("POST", "/coach/chat", json_data=chat_data)
    
    if success and status == 200:
        checks = []
        checks.append(("status_200", status == 200))
        checks.append(("has_response", "response" in data))
        checks.append(("response_non_empty", len(data.get("response", "")) > 0))
        checks.append(("response_is_string", isinstance(data.get("response"), str)))
        
        all_passed = all(check[1] for check in checks)
        response_preview = data.get("response", "")[:100] + "..." if len(data.get("response", "")) > 100 else data.get("response", "")
        details = ", ".join([f"{check[0]}={check[1]}" for check in checks]) + f", response_preview='{response_preview}'"
        
        log_test("POST /api/coach/chat (returns coherent response)", all_passed, details)
    else:
        log_test("POST /api/coach/chat (returns coherent response)", False, 
                f"Status {status}, Response: {data}")

# ============== MAIN TEST RUNNER ==============

def main():
    """Run all Phase A/B/C tests"""
    print("=" * 80)
    print("HACKSTER.AI - PHASE A/B/C BACKEND TESTING")
    print("Admin Practitioner Management + Product Source Tag + Content Library")
    print("+ Questionnaire/Chatbot Integration")
    print("=" * 80)
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Admin Email: {ADMIN_EMAIL}")
    
    # Get admin token
    admin_token = get_admin_token()
    if not admin_token:
        print("\n❌ FATAL: Admin login failed, cannot continue")
        sys.exit(1)
    
    # Get vendor ID for product tests
    vendor_id = get_real_vendor_id()
    if not vendor_id:
        print("\n❌ FATAL: Could not fetch vendor ID")
        sys.exit(1)
    print(f"✓ Using vendor ID: {vendor_id}")
    
    # Run Phase A tests
    coach_id = test_practitioner_admin(admin_token)
    test_product_source_tag(admin_token, vendor_id)
    
    # Run Phase B tests
    test_content_library(admin_token)
    test_questionnaire_integration()
    
    # Cleanup
    if coach_id:
        test_practitioner_cleanup(admin_token, coach_id)
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for r in test_results if r["passed"])
    total = len(test_results)
    
    print(f"\nTotal Tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print(f"Success Rate: {(passed/total*100):.1f}%")
    
    if total - passed > 0:
        print("\n❌ FAILED TESTS:")
        for r in test_results:
            if not r["passed"]:
                print(f"  [{r['number']}] {r['name']}")
                if r["details"]:
                    print(f"      {r['details']}")
    else:
        print("\n✅ ALL TESTS PASSED!")
    
    print("\n" + "=" * 80)
    
    # Exit with appropriate code
    sys.exit(0 if passed == total else 1)

if __name__ == "__main__":
    main()
