"""
Backend Testing for Hackster Health Goals Assessment V2
Tests the redesigned questionnaire and recommendations flow
"""

import requests
import json
from typing import Dict, Any, List

# Backend URL from frontend/.env
BASE_URL = "https://health-revolution-1.preview.emergentagent.com/api"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_test(name: str, passed: bool, details: str = ""):
    status = f"{Colors.GREEN}✓ PASS{Colors.END}" if passed else f"{Colors.RED}✗ FAIL{Colors.END}"
    print(f"{status} - {name}")
    if details:
        print(f"  {details}")
    if not passed:
        print()

def test_health_endpoint():
    """Test 1: GET /api/health - returns 200, status healthy"""
    print(f"\n{Colors.BLUE}=== Test 1: Health Check ==={Colors.END}")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        passed = response.status_code == 200
        
        if passed:
            data = response.json()
            has_status = "status" in data
            is_healthy = data.get("status") == "healthy" if has_status else False
            passed = has_status and is_healthy
            print_test("GET /api/health returns 200 with healthy status", passed, 
                      f"Status: {data.get('status')}, Database: {data.get('database')}")
        else:
            print_test("GET /api/health returns 200", False, f"Status code: {response.status_code}")
        
        return passed
    except Exception as e:
        print_test("GET /api/health", False, f"Error: {str(e)}")
        return False

def test_questionnaire_endpoint():
    """Test 2: GET /api/questionnaire - returns new v2 questionnaire"""
    print(f"\n{Colors.BLUE}=== Test 2: Questionnaire V2 ==={Colors.END}")
    try:
        response = requests.get(f"{BASE_URL}/questionnaire", timeout=10)
        passed = response.status_code == 200
        
        if not passed:
            print_test("GET /api/questionnaire returns 200", False, f"Status code: {response.status_code}")
            return False
        
        data = response.json()
        
        # Check questionnaire ID
        is_v2 = data.get("id") == "biohacking-assessment-v2"
        print_test("Questionnaire ID is 'biohacking-assessment-v2'", is_v2, 
                  f"ID: {data.get('id')}")
        
        # Check number of questions
        questions = data.get("questions", [])
        has_19_questions = len(questions) == 19
        print_test("Has 19 questions", has_19_questions, f"Count: {len(questions)}")
        
        # Check categories
        categories = set(q.get("category") for q in questions)
        expected_categories = {"About You", "Primary Goal", "Current Baseline", "Lifestyle", "Preferences"}
        has_all_categories = expected_categories.issubset(categories)
        print_test("Has all 5 categories", has_all_categories, 
                  f"Categories: {', '.join(sorted(categories))}")
        
        # Check for primary goal question with 4 priority goals
        primary_goal_q = next((q for q in questions if q.get("id") == "primary_goal"), None)
        if primary_goal_q:
            options = primary_goal_q.get("options", [])
            expected_goals = [
                "Increase Energy",
                "Improve Vitality / Longevity",
                "Boost Immune System",
                "Weight Loss / Metabolic Health"
            ]
            has_priority_goals = all(goal in options for goal in expected_goals)
            print_test("Primary goal has 4 priority goals", has_priority_goals,
                      f"Options: {', '.join(options)}")
        else:
            print_test("Primary goal question exists", False, "Question not found")
        
        return is_v2 and has_19_questions and has_all_categories
        
    except Exception as e:
        print_test("GET /api/questionnaire", False, f"Error: {str(e)}")
        return False

def test_vendors_endpoint():
    """Test 3: GET /api/vendors - returns at least 7 vendors including new ones"""
    print(f"\n{Colors.BLUE}=== Test 3: Vendors ==={Colors.END}")
    try:
        response = requests.get(f"{BASE_URL}/vendors", timeout=10)
        passed = response.status_code == 200
        
        if not passed:
            print_test("GET /api/vendors returns 200", False, f"Status code: {response.status_code}")
            return False
        
        vendors = response.json()
        vendor_count = len(vendors)
        has_7_vendors = vendor_count >= 7
        print_test("Has at least 7 vendors", has_7_vendors, f"Count: {vendor_count}")
        
        # Check for new vendors
        vendor_slugs = [v.get("slug") for v in vendors]
        new_vendors = ["bio-well", "curawaves", "stemregen"]
        
        for slug in new_vendors:
            has_vendor = slug in vendor_slugs
            vendor_name = next((v.get("name") for v in vendors if v.get("slug") == slug), "Not found")
            print_test(f"Has vendor '{slug}'", has_vendor, f"Name: {vendor_name}")
        
        all_new_vendors = all(slug in vendor_slugs for slug in new_vendors)
        
        return has_7_vendors and all_new_vendors
        
    except Exception as e:
        print_test("GET /api/vendors", False, f"Error: {str(e)}")
        return False

def test_products_endpoint():
    """Test 4: GET /api/products - returns 25+ products from all vendors"""
    print(f"\n{Colors.BLUE}=== Test 4: Products ==={Colors.END}")
    try:
        response = requests.get(f"{BASE_URL}/products", timeout=10)
        passed = response.status_code == 200
        
        if not passed:
            print_test("GET /api/products returns 200", False, f"Status code: {response.status_code}")
            return False
        
        products = response.json()
        product_count = len(products)
        has_25_products = product_count >= 25
        print_test("Has at least 25 products", has_25_products, f"Count: {product_count}")
        
        # Check vendor distribution
        vendor_names = set(p.get("vendor_name") for p in products)
        expected_vendors = ["Thorne", "Apex Energetics", "Standard Process", "Bio-Well", "CuraWaves", "StemRegen"]
        
        print(f"\n  Vendors represented: {', '.join(sorted(vendor_names))}")
        
        # Spot-check specific products
        product_names = [p.get("name") for p in products]
        spot_check_products = [
            "STEMREGEN® Mobilize",
            "Bio-Well GDV Camera",
            "CuraWaves Wave Therapy Device",
            "Berberine"
        ]
        
        print(f"\n  Spot-checking key products:")
        for product_name in spot_check_products:
            found = any(product_name.lower() in name.lower() for name in product_names)
            print_test(f"  Has '{product_name}'", found)
        
        all_spot_checks = all(
            any(product_name.lower() in name.lower() for name in product_names)
            for product_name in spot_check_products
        )
        
        return has_25_products and all_spot_checks
        
    except Exception as e:
        print_test("GET /api/products", False, f"Error: {str(e)}")
        return False

def test_coaches_endpoint():
    """Test 5: GET /api/coaches - returns at least 6 coaches including Laura Zook"""
    print(f"\n{Colors.BLUE}=== Test 5: Coaches ==={Colors.END}")
    try:
        response = requests.get(f"{BASE_URL}/coaches", timeout=10)
        passed = response.status_code == 200
        
        if not passed:
            print_test("GET /api/coaches returns 200", False, f"Status code: {response.status_code}")
            return False
        
        coaches = response.json()
        coach_count = len(coaches)
        has_6_coaches = coach_count >= 6
        print_test("Has at least 6 approved+active coaches", has_6_coaches, f"Count: {coach_count}")
        
        # Check for Laura Zook
        laura = next((c for c in coaches if c.get("name") == "Laura Zook"), None)
        has_laura = laura is not None
        
        if has_laura:
            rating = laura.get("rating", 0)
            is_5_star = rating == 5.0
            print_test("Has Laura Zook with 5.0 rating", is_5_star, 
                      f"Rating: {rating}, Specialties: {', '.join(laura.get('specialties', [])[:3])}")
        else:
            print_test("Has Laura Zook", False, "Coach not found")
        
        # Check for other new coaches
        new_coaches = ["Dr. James Okafor", "Maya Patel"]
        for coach_name in new_coaches:
            found = any(c.get("name") == coach_name for c in coaches)
            print_test(f"Has '{coach_name}'", found)
        
        return has_6_coaches and has_laura
        
    except Exception as e:
        print_test("GET /api/coaches", False, f"Error: {str(e)}")
        return False

def test_questionnaire_submit_weight_loss():
    """Test 6: POST /api/questionnaire/submit - weight-loss persona"""
    print(f"\n{Colors.BLUE}=== Test 6: Questionnaire Submit - Weight Loss Persona ==={Colors.END}")
    
    # Weight loss persona responses
    responses = [
        {"question_id": "age_range", "answer": "40-49"},
        {"question_id": "gender", "answer": "Female"},
        {"question_id": "height_weight_goal", "answer": "I want to lose 15-30 lbs"},
        {"question_id": "primary_goal", "answer": "Weight Loss / Metabolic Health"},
        {"question_id": "primary_goal_why", "answer": "I want to lose weight and improve my metabolic health for better energy and longevity"},
        {"question_id": "secondary_goals", "answer": ["More Energy", "Better Sleep", "Gut Health"]},
        {"question_id": "energy_level", "answer": 4},
        {"question_id": "sleep_quality", "answer": 5},
        {"question_id": "stress_level", "answer": 7},
        {"question_id": "immune_resilience", "answer": "Occasionally (2-3x a year)"},
        {"question_id": "metabolic_signals", "answer": ["Cravings for sugar / carbs", "Energy crashes after meals", "Belly fat hard to lose"]},
        {"question_id": "health_concerns", "answer": ["Fatigue / low energy", "Blood sugar", "Gut / digestion"]},
        {"question_id": "exercise_frequency", "answer": "3-4 times/week"},
        {"question_id": "diet_type", "answer": "Mostly Healthy / Whole Foods"},
        {"question_id": "current_supplements", "answer": ["Multivitamin", "Vitamin D"]},
        {"question_id": "openness_to_devices", "answer": "Curious — open to learning"},
        {"question_id": "wants_baseline_scan", "answer": "Maybe"},
        {"question_id": "wants_coach", "answer": "Yes — I want a coach to guide me"},
        {"question_id": "budget", "answer": "$100-200"}
    ]
    
    try:
        response = requests.post(
            f"{BASE_URL}/questionnaire/submit",
            json={"responses": responses},
            timeout=30
        )
        
        passed = response.status_code == 200
        
        if not passed:
            print_test("POST /api/questionnaire/submit returns 200", False, 
                      f"Status code: {response.status_code}, Error: {response.text[:200]}")
            return False
        
        data = response.json()
        
        # Check recommended_products
        products = data.get("recommended_products", [])
        has_products = 4 <= len(products) <= 7
        print_test("Has 4-7 recommended products", has_products, f"Count: {len(products)}")
        
        if products:
            print(f"\n  Recommended products:")
            for i, p in enumerate(products[:5], 1):
                print(f"    {i}. {p.get('name')} ({p.get('brand')})")
        
        # Check for at least one Thorne product
        has_thorne = any(p.get("brand") == "Thorne" for p in products)
        print_test("Has at least one Thorne product", has_thorne)
        
        # Check for device (CuraWaves or Bio-Well)
        has_device = any(
            p.get("brand") in ["CuraWaves", "Bio-Well"] or 
            "device" in p.get("name", "").lower() or
            "curawaves" in p.get("name", "").lower() or
            "bio-well" in p.get("name", "").lower()
            for p in products
        )
        print_test("Has at least one device (CuraWaves or Bio-Well)", has_device)
        
        # Check recommended_coaches
        coaches = data.get("recommended_coaches", [])
        has_3_coaches = len(coaches) == 3
        print_test("Has exactly 3 recommended coaches", has_3_coaches, f"Count: {len(coaches)}")
        
        if coaches:
            print(f"\n  Recommended coaches:")
            for i, c in enumerate(coaches, 1):
                print(f"    {i}. {c.get('name')} (Rating: {c.get('rating')}, Match Score: {c.get('match_score')})")
                print(f"       Specialties: {', '.join(c.get('specialties', [])[:3])}")
        
        # Check coach fields
        if coaches:
            first_coach = coaches[0]
            required_fields = ["id", "name", "specialties", "rating", "profile_image", "match_score"]
            has_all_fields = all(field in first_coach for field in required_fields)
            print_test("Coach has all required fields", has_all_fields,
                      f"Fields: {', '.join(required_fields)}")
        
        # Check coach_match_specialties
        coach_specialties = data.get("coach_match_specialties", [])
        has_specialties = len(coach_specialties) > 0
        print_test("Has coach_match_specialties", has_specialties,
                  f"Keywords: {', '.join(coach_specialties[:5])}")
        
        # Check other fields
        has_health_score = "health_score" in data
        has_primary_goals = "primary_goals" in data and len(data.get("primary_goals", [])) > 0
        has_lifestyle_tips = "lifestyle_tips" in data and len(data.get("lifestyle_tips", [])) > 0
        has_summary = "personalized_summary" in data and len(data.get("personalized_summary", "")) > 0
        
        print_test("Has health_score", has_health_score, f"Score: {data.get('health_score')}")
        print_test("Has primary_goals", has_primary_goals, f"Goals: {', '.join(data.get('primary_goals', []))}")
        print_test("Has lifestyle_tips", has_lifestyle_tips, f"Count: {len(data.get('lifestyle_tips', []))}")
        print_test("Has personalized_summary", has_summary)
        
        return (has_products and has_3_coaches and has_all_fields and 
                has_health_score and has_primary_goals and has_lifestyle_tips and has_summary)
        
    except Exception as e:
        print_test("POST /api/questionnaire/submit (weight-loss)", False, f"Error: {str(e)}")
        return False

def test_questionnaire_submit_longevity():
    """Test 7: POST /api/questionnaire/submit - longevity persona"""
    print(f"\n{Colors.BLUE}=== Test 7: Questionnaire Submit - Longevity Persona ==={Colors.END}")
    
    # Longevity persona responses
    responses = [
        {"question_id": "age_range", "answer": "50-59"},
        {"question_id": "gender", "answer": "Male"},
        {"question_id": "height_weight_goal", "answer": "I'm at a healthy weight and want to maintain"},
        {"question_id": "primary_goal", "answer": "Improve Vitality / Longevity"},
        {"question_id": "primary_goal_why", "answer": "I want to optimize my healthspan and live a long, vibrant life"},
        {"question_id": "secondary_goals", "answer": ["More Energy", "Mental Focus / Brain Health", "Heart Health"]},
        {"question_id": "energy_level", "answer": 7},
        {"question_id": "sleep_quality", "answer": 7},
        {"question_id": "stress_level", "answer": 5},
        {"question_id": "immune_resilience", "answer": "Rarely (1x a year or less)"},
        {"question_id": "metabolic_signals", "answer": ["None of these"]},
        {"question_id": "health_concerns", "answer": ["None"]},
        {"question_id": "exercise_frequency", "answer": "5+ times/week"},
        {"question_id": "diet_type", "answer": "Mediterranean"},
        {"question_id": "current_supplements", "answer": ["Vitamin D", "Omega-3 / Fish Oil", "NAD+ / NR"]},
        {"question_id": "openness_to_devices", "answer": "Very open — I love biohacking tools"},
        {"question_id": "wants_baseline_scan", "answer": "Yes, definitely"},
        {"question_id": "wants_coach", "answer": "Maybe — show me coach options"},
        {"question_id": "budget", "answer": "$200-500"}
    ]
    
    try:
        response = requests.post(
            f"{BASE_URL}/questionnaire/submit",
            json={"responses": responses},
            timeout=30
        )
        
        passed = response.status_code == 200
        
        if not passed:
            print_test("POST /api/questionnaire/submit returns 200", False, 
                      f"Status code: {response.status_code}")
            return False
        
        data = response.json()
        products = data.get("recommended_products", [])
        
        print(f"\n  Recommended products for longevity:")
        for i, p in enumerate(products[:7], 1):
            print(f"    {i}. {p.get('name')} ({p.get('brand')})")
        
        # Check for StemRegen or NiaCel products
        has_longevity_product = any(
            "stemregen" in p.get("name", "").lower() or
            "niacel" in p.get("name", "").lower() or
            "nad" in p.get("name", "").lower() or
            p.get("brand") == "StemRegen"
            for p in products
        )
        print_test("Has longevity product (StemRegen or NiaCel)", has_longevity_product)
        
        # Check coaches
        coaches = data.get("recommended_coaches", [])
        print(f"\n  Recommended coaches for longevity:")
        for i, c in enumerate(coaches, 1):
            print(f"    {i}. {c.get('name')} - Specialties: {', '.join(c.get('specialties', [])[:3])}")
        
        return has_longevity_product and len(coaches) == 3
        
    except Exception as e:
        print_test("POST /api/questionnaire/submit (longevity)", False, f"Error: {str(e)}")
        return False

def test_questionnaire_submit_immune():
    """Test 8: POST /api/questionnaire/submit - immune persona"""
    print(f"\n{Colors.BLUE}=== Test 8: Questionnaire Submit - Immune Support Persona ==={Colors.END}")
    
    # Immune support persona responses
    responses = [
        {"question_id": "age_range", "answer": "30-39"},
        {"question_id": "gender", "answer": "Female"},
        {"question_id": "height_weight_goal", "answer": "I'm at a healthy weight and want to maintain"},
        {"question_id": "primary_goal", "answer": "Boost Immune System"},
        {"question_id": "primary_goal_why", "answer": "I get sick frequently and want to strengthen my immune system"},
        {"question_id": "secondary_goals", "answer": ["More Energy", "Better Sleep", "Stress Resilience"]},
        {"question_id": "energy_level", "answer": 5},
        {"question_id": "sleep_quality", "answer": 6},
        {"question_id": "stress_level", "answer": 8},
        {"question_id": "immune_resilience", "answer": "Often (4-6x a year)"},
        {"question_id": "metabolic_signals", "answer": ["Brain fog"]},
        {"question_id": "health_concerns", "answer": ["Frequent illness", "Fatigue / low energy", "Mood / anxiety"]},
        {"question_id": "exercise_frequency", "answer": "1-2 times/week"},
        {"question_id": "diet_type", "answer": "Standard American Diet"},
        {"question_id": "current_supplements", "answer": ["None"]},
        {"question_id": "openness_to_devices", "answer": "Maybe later — supplements first"},
        {"question_id": "wants_baseline_scan", "answer": "No"},
        {"question_id": "wants_coach", "answer": "Maybe — show me coach options"},
        {"question_id": "budget", "answer": "$50-100"}
    ]
    
    try:
        response = requests.post(
            f"{BASE_URL}/questionnaire/submit",
            json={"responses": responses},
            timeout=30
        )
        
        passed = response.status_code == 200
        
        if not passed:
            print_test("POST /api/questionnaire/submit returns 200", False, 
                      f"Status code: {response.status_code}")
            return False
        
        data = response.json()
        products = data.get("recommended_products", [])
        
        print(f"\n  Recommended products for immune support:")
        for i, p in enumerate(products[:7], 1):
            print(f"    {i}. {p.get('name')} ({p.get('brand')})")
        
        # Check for immune-relevant products
        immune_keywords = ["vitamin d", "immuplex", "thymex", "curcumin", "immune"]
        has_immune_product = any(
            any(keyword in p.get("name", "").lower() for keyword in immune_keywords)
            for p in products
        )
        print_test("Has immune-relevant product (Vitamin D, Immuplex, Thymex, or Curcumin)", 
                  has_immune_product)
        
        # Check coaches
        coaches = data.get("recommended_coaches", [])
        print(f"\n  Recommended coaches for immune support:")
        for i, c in enumerate(coaches, 1):
            print(f"    {i}. {c.get('name')} - Specialties: {', '.join(c.get('specialties', [])[:3])}")
        
        return has_immune_product and len(coaches) == 3
        
    except Exception as e:
        print_test("POST /api/questionnaire/submit (immune)", False, f"Error: {str(e)}")
        return False

def run_all_tests():
    """Run all backend tests"""
    print(f"\n{Colors.YELLOW}{'='*80}{Colors.END}")
    print(f"{Colors.YELLOW}HACKSTER HEALTH GOALS ASSESSMENT V2 - BACKEND TESTING{Colors.END}")
    print(f"{Colors.YELLOW}{'='*80}{Colors.END}")
    print(f"\nBackend URL: {BASE_URL}\n")
    
    results = []
    
    # Run all tests
    results.append(("Health Check", test_health_endpoint()))
    results.append(("Questionnaire V2", test_questionnaire_endpoint()))
    results.append(("Vendors", test_vendors_endpoint()))
    results.append(("Products", test_products_endpoint()))
    results.append(("Coaches", test_coaches_endpoint()))
    results.append(("Submit - Weight Loss", test_questionnaire_submit_weight_loss()))
    results.append(("Submit - Longevity", test_questionnaire_submit_longevity()))
    results.append(("Submit - Immune", test_questionnaire_submit_immune()))
    
    # Summary
    print(f"\n{Colors.YELLOW}{'='*80}{Colors.END}")
    print(f"{Colors.YELLOW}TEST SUMMARY{Colors.END}")
    print(f"{Colors.YELLOW}{'='*80}{Colors.END}\n")
    
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)
    
    for test_name, passed in results:
        status = f"{Colors.GREEN}✓ PASS{Colors.END}" if passed else f"{Colors.RED}✗ FAIL{Colors.END}"
        print(f"{status} - {test_name}")
    
    print(f"\n{Colors.YELLOW}Total: {passed_count}/{total_count} tests passed{Colors.END}")
    
    if passed_count == total_count:
        print(f"\n{Colors.GREEN}🎉 ALL TESTS PASSED! 🎉{Colors.END}\n")
    else:
        print(f"\n{Colors.RED}❌ {total_count - passed_count} test(s) failed{Colors.END}\n")
    
    return passed_count == total_count

if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
