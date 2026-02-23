#!/usr/bin/env python3

import requests
import sys
import json
import time
from datetime import datetime

class ResumeMatcherAPITester:
    def __init__(self, base_url="https://resume-matcher-93.preview.exampleagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.job_seeker_token = None
        self.employer_token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
        
        result = {
            "test": name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {name}")
        if details:
            print(f"    Details: {details}")

    def run_api_test(self, name, method, endpoint, expected_status, data=None, headers=None, token=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        request_headers = {'Content-Type': 'application/json'}
        
        if headers:
            request_headers.update(headers)
        
        if token:
            request_headers['Authorization'] = f'Bearer {token}'

        try:
            if method == 'GET':
                response = requests.get(url, headers=request_headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=request_headers, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=request_headers, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=request_headers, timeout=30)

            success = response.status_code == expected_status
            
            if success:
                try:
                    response_data = response.json()
                    self.log_test(name, True, f"Status: {response.status_code}")
                    return True, response_data
                except:
                    self.log_test(name, True, f"Status: {response.status_code} (No JSON response)")
                    return True, {}
            else:
                try:
                    error_data = response.json()
                    self.log_test(name, False, f"Expected {expected_status}, got {response.status_code}: {error_data}")
                except:
                    self.log_test(name, False, f"Expected {expected_status}, got {response.status_code}")
                return False, {}

        except Exception as e:
            self.log_test(name, False, f"Exception: {str(e)}")
            return False, {}

    def test_auth_signup_job_seeker(self):
        """Test job seeker signup"""
        timestamp = int(time.time())
        test_data = {
            "email": f"jobseeker{timestamp}@test.com",
            "password": "TestPass123!",
            "name": f"Job Seeker {timestamp}",
            "role": "job_seeker"
        }
        
        success, response = self.run_api_test(
            "Job Seeker Signup",
            "POST",
            "auth/signup",
            200,
            data=test_data
        )
        
        if success and 'token' in response:
            self.job_seeker_token = response['token']
            self.job_seeker_data = test_data
            return True
        return False

    def test_auth_signup_employer(self):
        """Test employer signup"""
        timestamp = int(time.time())
        test_data = {
            "email": f"employer{timestamp}@test.com",
            "password": "TestPass123!",
            "name": f"Employer {timestamp}",
            "role": "employer"
        }
        
        success, response = self.run_api_test(
            "Employer Signup",
            "POST",
            "auth/signup",
            200,
            data=test_data
        )
        
        if success and 'token' in response:
            self.employer_token = response['token']
            self.employer_data = test_data
            return True
        return False

    def test_auth_login_job_seeker(self):
        """Test job seeker login"""
        if not hasattr(self, 'job_seeker_data'):
            self.log_test("Job Seeker Login", False, "No job seeker data available")
            return False
            
        login_data = {
            "email": self.job_seeker_data['email'],
            "password": self.job_seeker_data['password']
        }
        
        success, response = self.run_api_test(
            "Job Seeker Login",
            "POST",
            "auth/login",
            200,
            data=login_data
        )
        
        return success and 'token' in response

    def test_auth_login_employer(self):
        """Test employer login"""
        if not hasattr(self, 'employer_data'):
            self.log_test("Employer Login", False, "No employer data available")
            return False
            
        login_data = {
            "email": self.employer_data['email'],
            "password": self.employer_data['password']
        }
        
        success, response = self.run_api_test(
            "Employer Login",
            "POST",
            "auth/login",
            200,
            data=login_data
        )
        
        return success and 'token' in response

    def test_auth_me_job_seeker(self):
        """Test get current user for job seeker"""
        if not self.job_seeker_token:
            self.log_test("Get Job Seeker Profile", False, "No job seeker token")
            return False
            
        success, response = self.run_api_test(
            "Get Job Seeker Profile",
            "GET",
            "auth/me",
            200,
            token=self.job_seeker_token
        )
        
        return success and response.get('role') == 'job_seeker'

    def test_auth_me_employer(self):
        """Test get current user for employer"""
        if not self.employer_token:
            self.log_test("Get Employer Profile", False, "No employer token")
            return False
            
        success, response = self.run_api_test(
            "Get Employer Profile",
            "GET",
            "auth/me",
            200,
            token=self.employer_token
        )
        
        return success and response.get('role') == 'employer'

    def test_create_job(self):
        """Test job creation by employer"""
        if not self.employer_token:
            self.log_test("Create Job", False, "No employer token")
            return False
            
        job_data = {
            "title": "Senior Software Engineer",
            "company": "Test Company Inc",
            "location": "San Francisco, CA",
            "job_type": "Full-time",
            "description": "We are looking for a senior software engineer with experience in Python and React.",
            "requirements": [
                "5+ years of Python experience",
                "3+ years of React experience",
                "Bachelor's degree in Computer Science"
            ],
            "salary_range": "$120,000 - $160,000"
        }
        
        success, response = self.run_api_test(
            "Create Job",
            "POST",
            "jobs",
            200,
            data=job_data,
            token=self.employer_token
        )
        
        if success and 'id' in response:
            self.job_id = response['id']
            return True
        return False

    def test_get_jobs_as_job_seeker(self):
        """Test getting jobs as job seeker (should include match scores)"""
        if not self.job_seeker_token:
            self.log_test("Get Jobs (Job Seeker)", False, "No job seeker token")
            return False
            
        success, response = self.run_api_test(
            "Get Jobs (Job Seeker)",
            "GET",
            "jobs",
            200,
            token=self.job_seeker_token
        )
        
        return success

    def test_get_jobs_as_employer(self):
        """Test getting jobs as employer"""
        if not self.employer_token:
            self.log_test("Get Jobs (Employer)", False, "No employer token")
            return False
            
        success, response = self.run_api_test(
            "Get Jobs (Employer)",
            "GET",
            "jobs",
            200,
            token=self.employer_token
        )
        
        return success

    def test_get_my_jobs(self):
        """Test getting employer's own jobs"""
        if not self.employer_token:
            self.log_test("Get My Jobs", False, "No employer token")
            return False
            
        success, response = self.run_api_test(
            "Get My Jobs",
            "GET",
            "jobs/employer/my-jobs",
            200,
            token=self.employer_token
        )
        
        return success

    def test_get_job_detail(self):
        """Test getting job details"""
        if not hasattr(self, 'job_id') or not self.job_seeker_token:
            self.log_test("Get Job Detail", False, "No job ID or job seeker token")
            return False
            
        success, response = self.run_api_test(
            "Get Job Detail",
            "GET",
            f"jobs/{self.job_id}",
            200,
            token=self.job_seeker_token
        )
        
        return success

    def test_get_resumes(self):
        """Test getting resumes for job seeker"""
        if not self.job_seeker_token:
            self.log_test("Get Resumes", False, "No job seeker token")
            return False
            
        success, response = self.run_api_test(
            "Get Resumes",
            "GET",
            "resumes",
            200,
            token=self.job_seeker_token
        )
        
        return success

    def test_get_applications(self):
        """Test getting applications for job seeker"""
        if not self.job_seeker_token:
            self.log_test("Get Applications", False, "No job seeker token")
            return False
            
        success, response = self.run_api_test(
            "Get Applications",
            "GET",
            "applications",
            200,
            token=self.job_seeker_token
        )
        
        return success

    def test_apply_to_job_without_resume(self):
        """Test applying to job without resume (should fail)"""
        if not hasattr(self, 'job_id') or not self.job_seeker_token:
            self.log_test("Apply Without Resume", False, "No job ID or job seeker token")
            return False
            
        app_data = {"job_id": self.job_id}
        
        success, response = self.run_api_test(
            "Apply Without Resume",
            "POST",
            "applications",
            400,  # Should fail with 400
            data=app_data,
            token=self.job_seeker_token
        )
        
        return success

    def run_all_tests(self):
        """Run all API tests"""
        print("🚀 Starting Resume Matcher API Tests")
        print(f"📍 Testing against: {self.base_url}")
        print("=" * 60)
        
        # Authentication Tests
        print("\n📝 Authentication Tests")
        self.test_auth_signup_job_seeker()
        self.test_auth_signup_employer()
        self.test_auth_login_job_seeker()
        self.test_auth_login_employer()
        self.test_auth_me_job_seeker()
        self.test_auth_me_employer()
        
        # Job Management Tests
        print("\n💼 Job Management Tests")
        self.test_create_job()
        self.test_get_jobs_as_job_seeker()
        self.test_get_jobs_as_employer()
        self.test_get_my_jobs()
        self.test_get_job_detail()
        
        # Resume and Application Tests
        print("\n📄 Resume & Application Tests")
        self.test_get_resumes()
        self.test_get_applications()
        self.test_apply_to_job_without_resume()
        
        # Print Results
        print("\n" + "=" * 60)
        print(f"📊 Test Results: {self.tests_passed}/{self.tests_run} passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed!")
            return 0
        else:
            print("⚠️  Some tests failed. Check details above.")
            return 1

def main():
    tester = ResumeMatcherAPITester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())