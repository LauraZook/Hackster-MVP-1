#!/usr/bin/env python3
"""
Backend API Testing for Hackster.ai - Phase 1 Affiliate System
Tests ONLY the new affiliate tracking, grouped checkout, practitioner orders, and admin CRUD endpoints.
"""

import requests
import json
import sys
from typing import Dict, Any, Optional

# Backend URL from environment
BACKEND_URL = "https://health-revolution-1.preview.emergentagent.com/api"

# Admin credentials from test_credentials.md
ADMIN_EMAIL = "lzook@plzcompany.com"
ADMIN_PASSWORD = "HacksterAdmin2025!"

# Test results tracking
test_results = []

def log_test(test_name: str, passed: bool, details: str = ""):
    """Log test result"""
    status = "✅ PASS" if passed else "❌ FAIL"
    result = f"{status} - {test_name}"
    if details:
        result += f"\n    Details: {details}"
    print(result)
    test_results.append({"name": test_name, "passed": passed, "details": details})

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

def test_admin_login() -> Optional[str]:
    """Test 1: Admin login and return access token"""
    print("\n=== TEST 1: Admin Login ===")
    success, data, status = make_request("POST", "/auth/login", json_data={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    
    if success and "access_token" in data:
        # Verify role is admin
        token = data["access_token"]
        # Get user info to verify admin role
        success2, user_data, _ = make_request("GET", "/auth/me", headers={
            "Authorization": f"Bearer {token}"
        })
        if success2 and user_data.get("role") == "admin":
            log_test("Admin Login", True, f"Token received, role=admin")
            return token
        else:
            log_test("Admin Login", False, f"Token received but role is not admin: {user_data.get('role')}")
            return None
    else:
        log_test("Admin Login", False, f"Status {status}, Response: {data}")
        return None

def test_affiliate_redirect(product_id: str):
    """Test 2: GET /api/go/{product_id} - Affiliate tracking redirect"""
    print("\n=== TEST 2: Affiliate Redirect Tracking ===")
    
    # Test 2a: JSON format (returns URL + click_id)
    success, data, status = make_request("GET", f"/go/{product_id}", params={"format": "json"})
    if success and "url" in data and "click_id" in data:
        url = data["url"]
        click_id = data["click_id"]
        # Verify URL contains tracking params
        has_tracking = "aff=hackster" in url or "ref=hackster" in url or "partner=hackster" in url
        has_subid = "subId=" in url or "subid=" in url
        if has_tracking:
            log_test("Affiliate Redirect (JSON format)", True, 
                    f"URL: {url[:80]}..., click_id: {click_id}, has_tracking: {has_tracking}, has_subid: {has_subid}")
        else:
            log_test("Affiliate Redirect (JSON format)", False, 
                    f"URL missing tracking param: {url}")
    else:
        log_test("Affiliate Redirect (JSON format)", False, f"Status {status}, Response: {data}")
    
    # Test 2b: Redirect format (302)
    try:
        resp = requests.get(f"{BACKEND_URL}/go/{product_id}", allow_redirects=False, timeout=30)
        if resp.status_code == 302 and "Location" in resp.headers:
            location = resp.headers["Location"]
            has_tracking = "aff=hackster" in location or "ref=hackster" in location or "partner=hackster" in location
            log_test("Affiliate Redirect (302 redirect)", True, 
                    f"Redirects to: {location[:80]}..., has_tracking: {has_tracking}")
        else:
            log_test("Affiliate Redirect (302 redirect)", False, 
                    f"Expected 302, got {resp.status_code}")
    except Exception as e:
        log_test("Affiliate Redirect (302 redirect)", False, f"Error: {str(e)}")

def test_grouped_checkout(thorne_product_id: str, practitioner_product_id: str):
    """Test 3: POST /api/stack/checkout - Grouped checkout with mixed vendors"""
    print("\n=== TEST 3: Grouped Checkout (Mixed Vendors) ===")
    
    success, data, status = make_request("POST", "/stack/checkout", json_data={
        "items": [
            {"product_id": thorne_product_id, "quantity": 2},
            {"product_id": practitioner_product_id, "quantity": 1}
        ],
        "source": "stack"
    })
    
    if success and "vendor_groups" in data:
        vendor_groups = data["vendor_groups"]
        has_affiliate = False
        has_practitioner = False
        
        for group in vendor_groups:
            if group.get("fulfillment_type") == "affiliate":
                has_affiliate = True
                # Verify affiliate group has checkout_url
                if not group.get("checkout_url"):
                    log_test("Grouped Checkout - Affiliate group", False, 
                            f"Affiliate group missing checkout_url: {group}")
                    continue
                # Verify requires_practitioner_order is false
                if group.get("requires_practitioner_order"):
                    log_test("Grouped Checkout - Affiliate group", False, 
                            f"Affiliate group has requires_practitioner_order=true")
                    continue
            
            if group.get("fulfillment_type") == "practitioner_order":
                has_practitioner = True
                # Verify practitioner group has requires_practitioner_order=true
                if not group.get("requires_practitioner_order"):
                    log_test("Grouped Checkout - Practitioner group", False, 
                            f"Practitioner group missing requires_practitioner_order")
                    continue
                # Verify checkout_url is null
                if group.get("checkout_url"):
                    log_test("Grouped Checkout - Practitioner group", False, 
                            f"Practitioner group should not have checkout_url")
                    continue
        
        # Verify response structure
        checks = []
        checks.append(("has_affiliate_group", has_affiliate))
        checks.append(("has_practitioner_group", has_practitioner))
        checks.append(("grand_total > 0", data.get("grand_total", 0) > 0))
        checks.append(("est_commission_total >= 0", data.get("est_commission_total", -1) >= 0))
        checks.append(("has_practitioner_orders = true", data.get("has_practitioner_orders") == True))
        checks.append(("vendor_count >= 2", data.get("vendor_count", 0) >= 2))
        checks.append(("item_count >= 2", data.get("item_count", 0) >= 2))
        
        all_passed = all(check[1] for check in checks)
        details = ", ".join([f"{check[0]}={check[1]}" for check in checks])
        log_test("Grouped Checkout", all_passed, details)
    else:
        log_test("Grouped Checkout", False, f"Status {status}, Response: {data}")

def test_practitioner_order_create():
    """Test 4: POST /api/practitioner-orders - Create practitioner order"""
    print("\n=== TEST 4: Create Practitioner Order ===")
    
    # Get a practitioner product first
    success, products, _ = make_request("GET", "/products", params={"limit": 100})
    practitioner_product = None
    if success and isinstance(products, list):
        for p in products:
            vendor_id = p.get("vendor_id", "")
            if "apex" in vendor_id.lower() or "standard" in vendor_id.lower():
                practitioner_product = p
                break
    
    if not practitioner_product:
        log_test("Create Practitioner Order", False, "No practitioner products found")
        return None
    
    success, data, status = make_request("POST", "/practitioner-orders", json_data={
        "customer_name": "Jane Test",
        "customer_email": "jane@test.com",
        "items": [{"product_id": practitioner_product["id"], "quantity": 2}]
    })
    
    if success and "id" in data:
        checks = []
        checks.append(("has_id", "id" in data))
        checks.append(("estimated_total > 0", data.get("estimated_total", 0) > 0))
        checks.append(("status = new", data.get("status") == "new"))
        checks.append(("vendors populated", len(data.get("vendors", [])) > 0))
        
        all_passed = all(check[1] for check in checks)
        details = ", ".join([f"{check[0]}={check[1]}" for check in checks])
        log_test("Create Practitioner Order", all_passed, details)
        return data["id"]
    else:
        log_test("Create Practitioner Order", False, f"Status {status}, Response: {data}")
        return None

def test_admin_practitioner_orders(admin_token: str, order_id: Optional[str]):
    """Test 5: Admin practitioner order management"""
    print("\n=== TEST 5: Admin Practitioner Order Management ===")
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Test 5a: GET /api/admin/practitioner-orders
    success, data, status = make_request("GET", "/admin/practitioner-orders", headers=headers)
    if success and isinstance(data, list):
        log_test("Admin List Practitioner Orders", True, f"Found {len(data)} orders")
    else:
        log_test("Admin List Practitioner Orders", False, f"Status {status}, Response: {data}")
    
    # Test 5b: PUT /api/admin/practitioner-orders/{id} - Update status
    if order_id:
        success, data, status = make_request("PUT", f"/admin/practitioner-orders/{order_id}", 
                                            headers=headers, json_data={"status": "contacted"})
        if success:
            # Verify status was updated
            success2, orders, _ = make_request("GET", "/admin/practitioner-orders", headers=headers)
            if success2:
                updated_order = next((o for o in orders if o.get("id") == order_id), None)
                if updated_order and updated_order.get("status") == "contacted":
                    log_test("Admin Update Practitioner Order", True, "Status updated to 'contacted'")
                else:
                    log_test("Admin Update Practitioner Order", False, 
                            f"Status not updated correctly: {updated_order.get('status') if updated_order else 'order not found'}")
            else:
                log_test("Admin Update Practitioner Order", False, "Could not verify update")
        else:
            log_test("Admin Update Practitioner Order", False, f"Status {status}, Response: {data}")

def test_admin_product_crud(admin_token: str):
    """Test 6: Admin product CRUD"""
    print("\n=== TEST 6: Admin Product CRUD ===")
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Get a real vendor UUID first
    success, vendors, _ = make_request("GET", "/vendors")
    if not success or not vendors:
        log_test("Admin Product CRUD", False, "Could not fetch vendors")
        return
    
    vendor_id = vendors[0]["id"]
    
    # Test 6a: POST /api/admin/products - Create product
    product_data = {
        "vendor_id": vendor_id,
        "vendor_name": vendors[0]["name"],
        "name": "Test Product QA",
        "slug": "test-product-qa",
        "price": 29.99,
        "category": "supplements",
        "description": "QA test product"
    }
    success, data, status = make_request("POST", "/admin/products", headers=headers, json_data=product_data)
    
    if success and "id" in data:
        product_id = data["id"]
        checks = []
        checks.append(("has_id", "id" in data))
        checks.append(("vendor_name_filled", data.get("vendor_name") != ""))
        
        all_passed = all(check[1] for check in checks)
        details = ", ".join([f"{check[0]}={check[1]}" for check in checks])
        log_test("Admin Create Product", all_passed, details)
        
        # Test 6b: PUT /api/admin/products/{id} - Update product
        success2, data2, status2 = make_request("PUT", f"/admin/products/{product_id}", 
                                               headers=headers, json_data={"price": 34.99})
        if success2 and data2.get("price") == 34.99:
            log_test("Admin Update Product", True, f"Price updated to {data2.get('price')}")
        else:
            log_test("Admin Update Product", False, f"Status {status2}, Response: {data2}")
        
        # Test 6c: DELETE /api/admin/products/{id} - Delete product
        success3, data3, status3 = make_request("DELETE", f"/admin/products/{product_id}", headers=headers)
        if success3:
            log_test("Admin Delete Product", True, "Product deleted successfully")
        else:
            log_test("Admin Delete Product", False, f"Status {status3}, Response: {data3}")
    else:
        log_test("Admin Create Product", False, f"Status {status}, Response: {data}")

def test_admin_vendor_crud(admin_token: str):
    """Test 7: Admin vendor CRUD"""
    print("\n=== TEST 7: Admin Vendor CRUD ===")
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Test 7a: POST /api/admin/vendors - Create vendor
    vendor_data = {
        "name": "QA Vendor",
        "slug": "qa-vendor",
        "description": "QA test vendor",
        "website": "https://qa.com"
    }
    success, data, status = make_request("POST", "/admin/vendors", headers=headers, json_data=vendor_data)
    
    if success and "id" in data:
        vendor_id = data["id"]
        log_test("Admin Create Vendor", True, f"Vendor created with id: {vendor_id}")
        
        # Test 7b: PUT /api/admin/vendors/{id} - Update vendor
        success2, data2, status2 = make_request("PUT", f"/admin/vendors/{vendor_id}", 
                                               headers=headers, json_data={"commission_rate": 0.2})
        if success2 and data2.get("commission_rate") == 0.2:
            log_test("Admin Update Vendor", True, f"Commission rate updated to {data2.get('commission_rate')}")
        else:
            log_test("Admin Update Vendor", False, f"Status {status2}, Response: {data2}")
        
        # Test 7c: DELETE /api/admin/vendors/{id} - Delete vendor
        success3, data3, status3 = make_request("DELETE", f"/admin/vendors/{vendor_id}", headers=headers)
        if success3:
            log_test("Admin Delete Vendor", True, "Vendor deleted successfully")
        else:
            log_test("Admin Delete Vendor", False, f"Status {status3}, Response: {data3}")
    else:
        log_test("Admin Create Vendor", False, f"Status {status}, Response: {data}")

def test_admin_analytics(admin_token: str):
    """Test 8: GET /api/admin/affiliate/analytics"""
    print("\n=== TEST 8: Admin Affiliate Analytics ===")
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    success, data, status = make_request("GET", "/admin/affiliate/analytics", headers=headers)
    
    if success:
        checks = []
        checks.append(("has_total_clicks", "total_clicks" in data))
        checks.append(("total_clicks > 0", data.get("total_clicks", 0) > 0))
        checks.append(("has_by_vendor", "by_vendor" in data and isinstance(data["by_vendor"], list)))
        checks.append(("has_top_products", "top_products" in data and isinstance(data["top_products"], list)))
        checks.append(("has_recent_clicks", "recent_clicks" in data and isinstance(data["recent_clicks"], list)))
        checks.append(("has_est_commission", "est_commission" in data and isinstance(data["est_commission"], (int, float))))
        
        all_passed = all(check[1] for check in checks)
        details = ", ".join([f"{check[0]}={check[1]}" for check in checks])
        log_test("Admin Affiliate Analytics", all_passed, details)
    else:
        log_test("Admin Affiliate Analytics", False, f"Status {status}, Response: {data}")

def test_security_admin_endpoints():
    """Test 9: Security - Admin endpoints without token"""
    print("\n=== TEST 9: Security - Admin Endpoints Without Token ===")
    
    # Test without any token
    endpoints = [
        ("GET", "/admin/affiliate/analytics"),
        ("GET", "/admin/practitioner-orders"),
        ("POST", "/admin/products")
    ]
    
    all_blocked = True
    for method, endpoint in endpoints:
        success, data, status = make_request(method, endpoint)
        # Should return 401 (unauthorized) or 403 (forbidden)
        if status in [401, 403]:
            print(f"  ✓ {method} {endpoint} correctly blocked (status {status})")
        else:
            print(f"  ✗ {method} {endpoint} NOT blocked (status {status})")
            all_blocked = False
    
    log_test("Security - Admin Endpoints Without Token", all_blocked, 
            "All admin endpoints should return 401/403 without token")

def main():
    """Run all Phase-1 affiliate system tests"""
    print("=" * 80)
    print("HACKSTER.AI - PHASE 1 AFFILIATE SYSTEM BACKEND TESTING")
    print("=" * 80)
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Admin Email: {ADMIN_EMAIL}")
    
    # Get product IDs for testing
    print("\n=== SETUP: Fetching Product IDs ===")
    success, products, _ = make_request("GET", "/products", params={"limit": 100})
    if not success or not isinstance(products, list):
        print("❌ FATAL: Could not fetch products")
        sys.exit(1)
    
    # Find Thorne (affiliate) and Apex/Standard Process (practitioner) products
    thorne_product = None
    practitioner_product = None
    
    for p in products:
        vendor_id = p.get("vendor_id", "").lower()
        if "thorne" in vendor_id and not thorne_product:
            thorne_product = p
        if ("apex" in vendor_id or "standard" in vendor_id) and not practitioner_product:
            practitioner_product = p
    
    if not thorne_product:
        print("❌ FATAL: No Thorne products found")
        sys.exit(1)
    if not practitioner_product:
        print("❌ FATAL: No practitioner products found")
        sys.exit(1)
    
    print(f"✓ Thorne product: {thorne_product['name']} (id: {thorne_product['id']})")
    print(f"✓ Practitioner product: {practitioner_product['name']} (id: {practitioner_product['id']})")
    
    # Run tests
    admin_token = test_admin_login()
    if not admin_token:
        print("\n❌ FATAL: Admin login failed, cannot continue with admin tests")
        sys.exit(1)
    
    test_affiliate_redirect(thorne_product["id"])
    test_grouped_checkout(thorne_product["id"], practitioner_product["id"])
    order_id = test_practitioner_order_create()
    test_admin_practitioner_orders(admin_token, order_id)
    test_admin_product_crud(admin_token)
    test_admin_vendor_crud(admin_token)
    test_admin_analytics(admin_token)
    test_security_admin_endpoints()
    
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
                print(f"  - {r['name']}")
                if r["details"]:
                    print(f"    {r['details']}")
    
    print("\n" + "=" * 80)
    
    # Exit with appropriate code
    sys.exit(0 if passed == total else 1)

if __name__ == "__main__":
    main()
