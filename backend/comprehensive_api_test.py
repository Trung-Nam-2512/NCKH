#!/usr/bin/env python3
"""
COMPREHENSIVE API TESTING
Kiểm tra chuyên sâu cả 2 API: NOKTTV và KTTV
"""

import asyncio
import sys
import os
import json
import time
from datetime import datetime, date
import httpx
from typing import Dict, List, Any

# Add app to path
sys.path.append(os.path.dirname(__file__))

from app.config import config

class ComprehensiveAPITester:
    """Test suite for both APIs"""
    
    def __init__(self):
        self.nokttv_base = "https://openapi.vrain.vn/v1"
        self.kttv_base = "https://kttv-open.vrain.vn/v1"
        self.api_key = config.API_KEY
        
        self.test_results = {
            'nokttv': {'passed': 0, 'failed': 0, 'errors': []},
            'kttv': {'passed': 0, 'failed': 0, 'errors': []},
            'config': {'passed': 0, 'failed': 0, 'errors': []}
        }
    
    def log_result(self, api_type: str, test_name: str, passed: bool, details: str = ""):
        """Log test result"""
        status = "PASS" if passed else "FAIL"
        print(f"[{api_type.upper()}] [{status}] {test_name}")
        if details:
            print(f"    Details: {details}")
        
        if passed:
            self.test_results[api_type]['passed'] += 1
        else:
            self.test_results[api_type]['failed'] += 1
            self.test_results[api_type]['errors'].append(f"{test_name}: {details}")
    
    async def test_nokttv_api(self):
        """Test NOKTTV API comprehensively"""
        print("\n=== TESTING NOKTTV API ===")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            
            # Test 1: Stations endpoint
            try:
                headers = {"x-api-key": self.api_key} if self.api_key else {}
                response = await client.get(f"{self.nokttv_base}/stations", headers=headers)
                
                self.log_result('nokttv', 'Stations endpoint accessibility', 
                               response.status_code == 200,
                               f"Status: {response.status_code}")
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        is_list = isinstance(data, list)
                        self.log_result('nokttv', 'Stations response format', is_list,
                                       f"Type: {type(data)}, Length: {len(data) if is_list else 'N/A'}")
                        
                        if is_list and len(data) > 0:
                            # Test station structure
                            station = data[0]
                            required_fields = ['id', 'name', 'latitude', 'longitude']
                            has_required = all(field in station for field in required_fields)
                            self.log_result('nokttv', 'Station structure validation', has_required,
                                           f"Fields: {list(station.keys())}")
                    except Exception as e:
                        self.log_result('nokttv', 'Stations response parsing', False, str(e))
                
            except Exception as e:
                self.log_result('nokttv', 'Stations endpoint accessibility', False, str(e))
            
            # Test 2: Stats endpoint
            try:
                headers = {"x-api-key": self.api_key} if self.api_key else {}
                response = await client.get(f"{self.nokttv_base}/stations/stats", headers=headers)
                
                self.log_result('nokttv', 'Stats endpoint accessibility',
                               response.status_code == 200,
                               f"Status: {response.status_code}")
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        is_list = isinstance(data, list)
                        self.log_result('nokttv', 'Stats response format', is_list,
                                       f"Type: {type(data)}, Length: {len(data) if is_list else 'N/A'}")
                    except Exception as e:
                        self.log_result('nokttv', 'Stats response parsing', False, str(e))
                
            except Exception as e:
                self.log_result('nokttv', 'Stats endpoint accessibility', False, str(e))
            
            # Test 3: Multiple requests for stability
            success_count = 0
            total_requests = 5
            
            for i in range(total_requests):
                try:
                    headers = {"x-api-key": self.api_key} if self.api_key else {}
                    response = await client.get(f"{self.nokttv_base}/stations", headers=headers)
                    if response.status_code == 200:
                        success_count += 1
                    await asyncio.sleep(0.5)  # Small delay between requests
                except:
                    pass
            
            stability_rate = (success_count / total_requests) * 100
            self.log_result('nokttv', 'API stability test', stability_rate >= 80,
                           f"Success: {success_count}/{total_requests} ({stability_rate:.1f}%)")
    
    async def test_kttv_api(self):
        """Test KTTV API comprehensively"""
        print("\n=== TESTING KTTV API ===")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            
            # Test different authentication methods
            auth_methods = [
                {"name": "No auth", "headers": {}},
                {"name": "API Key header", "headers": {"x-api-key": self.api_key} if self.api_key else {}},
                {"name": "Authorization header", "headers": {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}},
                {"name": "API Key param", "params": {"api_key": self.api_key} if self.api_key else {}},
            ]
            
            for auth_method in auth_methods:
                try:
                    headers = auth_method.get("headers", {})
                    params = auth_method.get("params", {})
                    
                    response = await client.get(f"{self.kttv_base}/stations", 
                                               headers=headers, params=params)
                    
                    success = response.status_code == 200
                    self.log_result('kttv', f'Stations with {auth_method["name"]}', success,
                                   f"Status: {response.status_code}")
                    
                    if success:
                        try:
                            data = response.json()
                            is_list = isinstance(data, list)
                            self.log_result('kttv', 'Stations response format', is_list,
                                           f"Type: {type(data)}, Length: {len(data) if is_list else 'N/A'}")
                            break  # Found working auth method
                        except Exception as e:
                            self.log_result('kttv', 'Stations response parsing', False, str(e))
                    
                except Exception as e:
                    self.log_result('kttv', f'Stations with {auth_method["name"]}', False, str(e))
            
            # Test stats endpoint with working auth (if found)
            if self.api_key:
                try:
                    headers = {"x-api-key": self.api_key}
                    response = await client.get(f"{self.kttv_base}/stations/stats", headers=headers)
                    
                    self.log_result('kttv', 'Stats endpoint accessibility',
                                   response.status_code == 200,
                                   f"Status: {response.status_code}")
                    
                    if response.status_code == 200:
                        try:
                            data = response.json()
                            is_list = isinstance(data, list)
                            self.log_result('kttv', 'Stats response format', is_list,
                                           f"Type: {type(data)}, Length: {len(data) if is_list else 'N/A'}")
                        except Exception as e:
                            self.log_result('kttv', 'Stats response parsing', False, str(e))
                    
                except Exception as e:
                    self.log_result('kttv', 'Stats endpoint accessibility', False, str(e))
    
    async def test_api_error_handling(self):
        """Test how APIs handle various error scenarios"""
        print("\n=== TESTING ERROR HANDLING ===")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            
            # Test invalid endpoints
            invalid_endpoints = [
                "/stations/invalid",
                "/nonexistent",
                "/stations/123/invalid"
            ]
            
            for api_name, base_url in [("nokttv", self.nokttv_base), ("kttv", self.kttv_base)]:
                for endpoint in invalid_endpoints:
                    try:
                        headers = {"x-api-key": self.api_key} if self.api_key else {}
                        response = await client.get(f"{base_url}{endpoint}", headers=headers)
                        
                        # Should return 404 or similar error code
                        handles_gracefully = response.status_code in [404, 400, 403, 405]
                        self.log_result(api_name, f'Invalid endpoint handling {endpoint}', 
                                       handles_gracefully,
                                       f"Status: {response.status_code}")
                        
                    except Exception as e:
                        # Network errors are also acceptable for invalid endpoints
                        self.log_result(api_name, f'Invalid endpoint handling {endpoint}', True,
                                       f"Network error (expected): {str(e)[:50]}")
    
    async def test_api_configuration(self):
        """Test API configuration and environment setup"""
        print("\n=== TESTING CONFIGURATION ===")
        
        # Test environment variables
        api_key_configured = bool(self.api_key)
        self.log_result('config', 'API key configuration', api_key_configured,
                       f"API Key present: {api_key_configured}")
        
        # Test URLs accessibility
        async with httpx.AsyncClient(timeout=10.0) as client:
            for api_name, base_url in [("nokttv", self.nokttv_base), ("kttv", self.kttv_base)]:
                try:
                    # Simple connectivity test
                    response = await client.get(base_url, follow_redirects=True)
                    reachable = response.status_code < 500  # Any response means server is reachable
                    self.log_result('config', f'{api_name.upper()} server reachability', reachable,
                                   f"Status: {response.status_code}")
                except Exception as e:
                    self.log_result('config', f'{api_name.upper()} server reachability', False,
                                   f"Error: {str(e)[:50]}")
    
    async def run_comprehensive_test(self):
        """Run all tests"""
        print("COMPREHENSIVE API TESTING")
        print("=" * 50)
        print(f"NOKTTV Base URL: {self.nokttv_base}")
        print(f"KTTV Base URL: {self.kttv_base}")
        print(f"API Key Configured: {bool(self.api_key)}")
        print("=" * 50)
        
        # Run all test suites
        await self.test_api_configuration()
        await self.test_nokttv_api()
        await self.test_kttv_api()
        await self.test_api_error_handling()
        
        # Print comprehensive results
        print("\n" + "=" * 50)
        print("COMPREHENSIVE TEST RESULTS")
        print("=" * 50)
        
        total_passed = 0
        total_failed = 0
        
        for api_type in ['nokttv', 'kttv', 'config']:
            if api_type in self.test_results:
                passed = self.test_results[api_type]['passed']
                failed = self.test_results[api_type]['failed']
                total_passed += passed
                total_failed += failed
                
                if passed + failed > 0:
                    success_rate = (passed / (passed + failed)) * 100
                    print(f"{api_type.upper()}: {passed}/{passed + failed} tests passed ({success_rate:.1f}%)")
                    
                    if self.test_results[api_type]['errors']:
                        print(f"  Failures:")
                        for error in self.test_results[api_type]['errors'][:3]:  # Show first 3
                            print(f"    - {error}")
        
        overall_success_rate = (total_passed / (total_passed + total_failed)) * 100 if (total_passed + total_failed) > 0 else 0
        
        print(f"\nOVERALL: {total_passed}/{total_passed + total_failed} tests passed ({overall_success_rate:.1f}%)")
        
        # Final assessment
        if overall_success_rate >= 90:
            print("API STATUS: EXCELLENT - Both APIs working perfectly")
        elif overall_success_rate >= 70:
            print("API STATUS: GOOD - Minor issues detected")
        elif overall_success_rate >= 50:
            print("API STATUS: ACCEPTABLE - Some configuration needed")
        else:
            print("API STATUS: POOR - Significant issues need attention")
        
        return overall_success_rate > 70

async def main():
    """Main test runner"""
    tester = ComprehensiveAPITester()
    success = await tester.run_comprehensive_test()
    
    print(f"\nAPI COMPREHENSIVE TEST: {'PASSED' if success else 'NEEDS ATTENTION'}")
    return success

if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Test suite failed: {e}")
        sys.exit(1)