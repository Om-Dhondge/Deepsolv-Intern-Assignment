import requests
import sys
import json
from datetime import datetime
import time

class LinkedInInsightsAPITester:
    def __init__(self, base_url="https://companywatch.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
        
        result = {
            "test_name": name,
            "success": success,
            "details": details,
            "timestamp": datetime.utcnow().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {name}")
        if details:
            print(f"    Details: {details}")

    def test_health_check(self):
        """Test GET /api/ - Health check endpoint"""
        try:
            response = requests.get(f"{self.api_url}/", timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                expected_keys = ["message", "version"]
                has_keys = all(key in data for key in expected_keys)
                success = has_keys
                details = f"Status: {response.status_code}, Response: {data}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text}"
                
            self.log_test("Health Check Endpoint", success, details)
            return success
            
        except Exception as e:
            self.log_test("Health Check Endpoint", False, f"Error: {str(e)}")
            return False

    def test_scrape_page(self, page_id="microsoft"):
        """Test GET /api/pages/{page_id} - Scrape and retrieve page details"""
        try:
            print(f"\n🔍 Testing page scraping for '{page_id}' (this may take 15-30 seconds)...")
            response = requests.get(f"{self.api_url}/pages/{page_id}", timeout=60)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                required_fields = ["page_id", "page_url", "page_name"]
                has_required = all(field in data for field in required_fields)
                success = has_required and data["page_id"] == page_id
                details = f"Status: {response.status_code}, Page: {data.get('page_name', 'N/A')}, Followers: {data.get('follower_count', 0)}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
                
            self.log_test(f"Scrape Page ({page_id})", success, details)
            return success, response.json() if success else None
            
        except Exception as e:
            self.log_test(f"Scrape Page ({page_id})", False, f"Error: {str(e)}")
            return False, None

    def test_list_pages(self):
        """Test GET /api/pages - List all pages with pagination"""
        try:
            response = requests.get(f"{self.api_url}/pages", timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                required_fields = ["pages", "total", "page", "page_size", "total_pages"]
                has_required = all(field in data for field in required_fields)
                success = has_required and isinstance(data["pages"], list)
                details = f"Status: {response.status_code}, Total pages: {data.get('total', 0)}, Current page: {data.get('page', 0)}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
                
            self.log_test("List Pages", success, details)
            return success
            
        except Exception as e:
            self.log_test("List Pages", False, f"Error: {str(e)}")
            return False

    def test_list_pages_with_filters(self):
        """Test GET /api/pages with filters"""
        try:
            # Test with name filter
            params = {"name": "microsoft", "page_size": 5}
            response = requests.get(f"{self.api_url}/pages", params=params, timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                success = "pages" in data and isinstance(data["pages"], list)
                details = f"Status: {response.status_code}, Filtered results: {len(data.get('pages', []))}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
                
            self.log_test("List Pages with Filters", success, details)
            return success
            
        except Exception as e:
            self.log_test("List Pages with Filters", False, f"Error: {str(e)}")
            return False

    def test_page_posts(self, page_id="microsoft"):
        """Test GET /api/pages/{page_id}/posts - Get posts with pagination"""
        try:
            response = requests.get(f"{self.api_url}/pages/{page_id}/posts", timeout=15)
            success = response.status_code in [200, 404]  # 404 is acceptable if page not scraped yet
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["posts", "total", "page", "page_size", "total_pages"]
                has_required = all(field in data for field in required_fields)
                success = has_required and isinstance(data["posts"], list)
                details = f"Status: {response.status_code}, Posts found: {len(data.get('posts', []))}"
            elif response.status_code == 404:
                details = f"Status: {response.status_code}, Page not found (expected if not scraped yet)"
            else:
                success = False
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
                
            self.log_test(f"Get Page Posts ({page_id})", success, details)
            return success
            
        except Exception as e:
            self.log_test(f"Get Page Posts ({page_id})", False, f"Error: {str(e)}")
            return False

    def test_page_employees(self, page_id="microsoft"):
        """Test GET /api/pages/{page_id}/employees - Get employees with pagination"""
        try:
            response = requests.get(f"{self.api_url}/pages/{page_id}/employees", timeout=15)
            success = response.status_code in [200, 404]  # 404 is acceptable if page not scraped yet
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["users", "total", "page", "page_size", "total_pages"]
                has_required = all(field in data for field in required_fields)
                success = has_required and isinstance(data["users"], list)
                details = f"Status: {response.status_code}, Employees found: {len(data.get('users', []))}"
            elif response.status_code == 404:
                details = f"Status: {response.status_code}, Page not found (expected if not scraped yet)"
            else:
                success = False
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
                
            self.log_test(f"Get Page Employees ({page_id})", success, details)
            return success
            
        except Exception as e:
            self.log_test(f"Get Page Employees ({page_id})", False, f"Error: {str(e)}")
            return False

    def test_page_followers(self, page_id="microsoft"):
        """Test GET /api/pages/{page_id}/followers - Get follower information"""
        try:
            response = requests.get(f"{self.api_url}/pages/{page_id}/followers", timeout=10)
            success = response.status_code in [200, 404]  # 404 is acceptable if page not scraped yet
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["page_id", "follower_count"]
                has_required = all(field in data for field in required_fields)
                success = has_required and data["page_id"] == page_id
                details = f"Status: {response.status_code}, Follower count: {data.get('follower_count', 0)}"
            elif response.status_code == 404:
                details = f"Status: {response.status_code}, Page not found (expected if not scraped yet)"
            else:
                success = False
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
                
            self.log_test(f"Get Page Followers ({page_id})", success, details)
            return success
            
        except Exception as e:
            self.log_test(f"Get Page Followers ({page_id})", False, f"Error: {str(e)}")
            return False

    def run_all_tests(self):
        """Run all backend API tests"""
        print("🚀 Starting LinkedIn Insights API Tests")
        print(f"🌐 Testing against: {self.base_url}")
        print("=" * 60)
        
        # Test 1: Health check
        health_ok = self.test_health_check()
        
        if not health_ok:
            print("\n❌ Health check failed - stopping tests")
            return False
        
        # Test 2: Scrape a page (this will take time)
        scrape_ok, page_data = self.test_scrape_page("microsoft")
        
        # Test 3: List pages
        list_ok = self.test_list_pages()
        
        # Test 4: List pages with filters
        filter_ok = self.test_list_pages_with_filters()
        
        # Test 5-7: Test posts, employees, followers (use scraped page if available)
        test_page_id = "microsoft"
        posts_ok = self.test_page_posts(test_page_id)
        employees_ok = self.test_page_employees(test_page_id)
        followers_ok = self.test_page_followers(test_page_id)
        
        # Print summary
        print("\n" + "=" * 60)
        print(f"📊 Test Summary: {self.tests_passed}/{self.tests_run} tests passed")
        print(f"✅ Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed!")
            return True
        else:
            print("⚠️  Some tests failed - check details above")
            return False

def main():
    tester = LinkedInInsightsAPITester()
    success = tester.run_all_tests()
    
    # Save test results
    with open("/app/test_results_backend.json", "w") as f:
        json.dump({
            "timestamp": datetime.utcnow().isoformat(),
            "total_tests": tester.tests_run,
            "passed_tests": tester.tests_passed,
            "success_rate": (tester.tests_passed/tester.tests_run)*100 if tester.tests_run > 0 else 0,
            "results": tester.test_results
        }, f, indent=2)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())