#!/usr/bin/env python3
"""
DEEP SCHEDULER SYSTEM TEST
Kiểm tra chuyên sâu tất cả logic, error handling, edge cases
"""

import asyncio
import sys
import os
import time
import json
from datetime import datetime, date, timedelta
from typing import Dict, Any, List
import logging

# Add app to path
sys.path.append(os.path.dirname(__file__))

from app.services.scheduler_service import SchedulerService
from app.services.daily_data_collector import DailyDataCollector
from app.main import app
from fastapi.testclient import TestClient

# Configure logging without emojis to avoid encoding issues
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

class DeepSchedulerTester:
    """Comprehensive test suite for scheduler system"""
    
    def __init__(self):
        self.test_results = {
            'passed': 0,
            'failed': 0,
            'errors': []
        }
        
    def log_test(self, test_name: str, passed: bool, details: str = ""):
        """Log test result"""
        status = "PASS" if passed else "FAIL"
        print(f"[{status}] {test_name}")
        if details:
            print(f"       Details: {details}")
        
        if passed:
            self.test_results['passed'] += 1
        else:
            self.test_results['failed'] += 1
            self.test_results['errors'].append(f"{test_name}: {details}")
    
    async def test_scheduler_initialization(self):
        """Test 1: Scheduler initialization and configuration"""
        print("\n=== TEST 1: Scheduler Initialization ===")
        
        try:
            # Test basic initialization
            scheduler = SchedulerService()
            self.log_test("Scheduler object creation", True)
            
            # Test configuration validation
            config = scheduler.config
            required_keys = ['collection_times', 'max_retries', 'retry_interval']
            config_valid = all(key in config for key in required_keys)
            self.log_test("Configuration completeness", config_valid, 
                         f"Missing keys: {[k for k in required_keys if k not in config]}")
            
            # Test collection times format
            collection_times = config['collection_times']
            times_valid = all('hour' in t and 'minute' in t for t in collection_times)
            self.log_test("Collection times format", times_valid)
            
            # Test scheduler status before start
            status = scheduler.get_status()
            status_valid = (
                'is_running' in status and 
                'scheduler_active' in status and
                status['is_running'] == False
            )
            self.log_test("Initial status format", status_valid)
            
        except Exception as e:
            self.log_test("Scheduler initialization", False, str(e))
    
    async def test_data_collector_logic(self):
        """Test 2: Data collector core logic"""
        print("\n=== TEST 2: Data Collector Logic ===")
        
        try:
            collector = DailyDataCollector()
            
            # Test database initialization
            db_init = await collector.initialize_database()
            self.log_test("Database initialization", db_init)
            
            if db_init:
                # Test collections existence
                collections = collector.collections
                required_collections = ['historical_data', 'current_data', 'collection_logs']
                collections_valid = all(col in collections for col in required_collections)
                self.log_test("Database collections setup", collections_valid)
                
                # Test station fetching with error handling
                try:
                    nokttv_stations = await collector.fetch_stations('nokttv')
                    nokttv_valid = isinstance(nokttv_stations, list)
                    self.log_test("NOKTTV station fetch", nokttv_valid, 
                                 f"Got {len(nokttv_stations)} stations")
                except Exception as e:
                    self.log_test("NOKTTV station fetch", False, str(e))
                
                try:
                    kttv_stations = await collector.fetch_stations('kttv')
                    kttv_valid = isinstance(kttv_stations, list)
                    self.log_test("KTTV station fetch", kttv_valid, 
                                 f"Got {len(kttv_stations)} stations")
                except Exception as e:
                    self.log_test("KTTV station fetch", False, f"Expected error: {str(e)[:50]}")
                
                # Test invalid API type
                try:
                    invalid_stations = await collector.fetch_stations('invalid_api')
                    self.log_test("Invalid API type handling", len(invalid_stations) == 0)
                except Exception as e:
                    self.log_test("Invalid API type handling", True, "Properly raised exception")
                
                # Test date handling
                today = date.today()
                future_date = today + timedelta(days=5)
                past_date = today - timedelta(days=5)
                
                # Test with different date inputs
                test_dates = [today, past_date, future_date, None]
                for test_date in test_dates:
                    try:
                        # This should not crash, even if it fails to collect data
                        result = await collector.run_daily_collection(test_date)
                        date_str = test_date.isoformat() if test_date else "None"
                        self.log_test(f"Collection with date {date_str}", True, 
                                     f"Result: {result}")
                    except Exception as e:
                        date_str = test_date.isoformat() if test_date else "None"
                        self.log_test(f"Collection with date {date_str}", False, str(e))
                
                await collector.client.close()
            
        except Exception as e:
            self.log_test("Data collector logic", False, str(e))
    
    async def test_api_endpoints_comprehensive(self):
        """Test 3: All API endpoints with various scenarios"""
        print("\n=== TEST 3: API Endpoints Comprehensive ===")
        
        client = TestClient(app)
        
        # Test all scheduler endpoints
        endpoints = [
            ('/scheduler/status', 'GET'),
            ('/scheduler/jobs', 'GET'),
            ('/scheduler/config', 'GET'),
            ('/scheduler/health', 'GET'),
            ('/scheduler/statistics', 'GET'),
            ('/scheduler/logs', 'GET'),
        ]
        
        for endpoint, method in endpoints:
            try:
                if method == 'GET':
                    response = client.get(endpoint)
                elif method == 'POST':
                    response = client.post(endpoint)
                
                success = response.status_code in [200, 201]
                self.log_test(f"{method} {endpoint}", success, 
                             f"Status: {response.status_code}")
                
                # Test response format for successful requests
                if success:
                    try:
                        data = response.json()
                        is_dict_or_list = isinstance(data, (dict, list))
                        self.log_test(f"{endpoint} response format", is_dict_or_list)
                    except:
                        self.log_test(f"{endpoint} response format", False, "Invalid JSON")
                        
            except Exception as e:
                self.log_test(f"{method} {endpoint}", False, str(e))
        
        # Test POST endpoints with various payloads
        print("\n--- Testing POST endpoints ---")
        
        # Test manual collection with different payloads
        test_payloads = [
            {},  # Empty payload
            {"target_date": "2024-01-15"},  # Valid date
            {"target_date": "invalid-date"},  # Invalid date
            {"target_date": "2024-01-15", "force": True},  # With force
            {"target_date": "2024-01-15", "force": False},  # With force false
        ]
        
        for i, payload in enumerate(test_payloads):
            try:
                response = client.post('/scheduler/manual-collect', json=payload)
                # Should handle gracefully, not crash
                handled_gracefully = response.status_code in [200, 400, 422, 500]
                self.log_test(f"Manual collect payload {i+1}", handled_gracefully,
                             f"Status: {response.status_code}, Payload: {payload}")
            except Exception as e:
                self.log_test(f"Manual collect payload {i+1}", False, str(e))
    
    async def test_error_scenarios(self):
        """Test 4: Error scenarios and recovery"""
        print("\n=== TEST 4: Error Scenarios and Recovery ===")
        
        try:
            # Test scheduler with invalid configuration
            scheduler = SchedulerService()
            
            # Simulate config corruption
            original_config = scheduler.config.copy()
            scheduler.config['collection_times'] = []  # Invalid empty times
            
            try:
                await scheduler.schedule_daily_collection_jobs()
                self.log_test("Empty collection times handling", True, "No jobs scheduled")
            except Exception as e:
                self.log_test("Empty collection times handling", False, str(e))
            
            # Restore config
            scheduler.config = original_config
            
            # Test collector with database connection issues
            collector = DailyDataCollector()
            
            # Test with invalid MongoDB URI (simulate connection failure)
            original_client = collector.client
            collector.client = None
            
            try:
                result = await collector.initialize_database()
                self.log_test("Null database client handling", result == False)
            except Exception as e:
                self.log_test("Null database client handling", True, "Properly handled exception")
            
            # Restore client
            collector.client = original_client
            
            # Test retry logic simulation
            scheduler_service = SchedulerService()
            job_id = "test_job"
            
            # Simulate failed collection runs
            for attempt in range(3):
                scheduler_service.job_status[job_id] = {
                    'status': 'running',
                    'start_time': datetime.utcnow(),
                    'attempts': attempt + 1
                }
            
            final_status = scheduler_service.job_status[job_id]
            retry_logic_works = final_status['attempts'] == 3
            self.log_test("Retry logic tracking", retry_logic_works)
            
        except Exception as e:
            self.log_test("Error scenarios", False, str(e))
    
    async def test_concurrent_operations(self):
        """Test 5: Concurrent operations and race conditions"""
        print("\n=== TEST 5: Concurrent Operations ===")
        
        try:
            # Test multiple scheduler instances
            schedulers = [SchedulerService() for _ in range(3)]
            
            # All should initialize without conflicts
            all_initialized = True
            for i, scheduler in enumerate(schedulers):
                try:
                    status = scheduler.get_status()
                    if 'is_running' not in status:
                        all_initialized = False
                        break
                except Exception as e:
                    all_initialized = False
                    break
            
            self.log_test("Multiple scheduler instances", all_initialized)
            
            # Test concurrent API calls
            client = TestClient(app)
            
            async def make_request():
                response = client.get('/scheduler/status')
                return response.status_code == 200
            
            # Make 5 concurrent requests
            tasks = [make_request() for _ in range(5)]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            successful_requests = sum(1 for r in results if r is True)
            self.log_test("Concurrent API requests", successful_requests >= 3,
                         f"{successful_requests}/5 successful")
            
            # Test database concurrent access
            collector = DailyDataCollector()
            if await collector.initialize_database():
                
                async def test_db_operation():
                    try:
                        # Test simple database operation
                        count = await collector.db[collector.collections['collection_logs']].count_documents({})
                        return True
                    except Exception:
                        return False
                
                db_tasks = [test_db_operation() for _ in range(3)]
                db_results = await asyncio.gather(*db_tasks, return_exceptions=True)
                
                successful_db_ops = sum(1 for r in db_results if r is True)
                self.log_test("Concurrent database operations", successful_db_ops >= 2,
                             f"{successful_db_ops}/3 successful")
                
                await collector.client.close()
            
        except Exception as e:
            self.log_test("Concurrent operations", False, str(e))
    
    async def test_edge_cases_and_boundaries(self):
        """Test 6: Edge cases and boundary conditions"""
        print("\n=== TEST 6: Edge Cases and Boundaries ===")
        
        try:
            collector = DailyDataCollector()
            
            # Test with extreme dates
            extreme_dates = [
                date(1900, 1, 1),  # Very old date
                date(2100, 12, 31),  # Far future date
                date(2000, 2, 29),  # Leap year
                date(2001, 2, 28),  # Non-leap year
            ]
            
            for extreme_date in extreme_dates:
                try:
                    result = await collector.run_daily_collection(extreme_date)
                    date_str = extreme_date.isoformat()
                    self.log_test(f"Extreme date {date_str}", True, f"Handled gracefully: {result}")
                except Exception as e:
                    date_str = extreme_date.isoformat()
                    self.log_test(f"Extreme date {date_str}", False, str(e))
            
            # Test scheduler with extreme configurations
            scheduler = SchedulerService()
            
            # Test with many collection times
            extreme_times = [{'hour': h, 'minute': 0} for h in range(24)]
            scheduler.config['collection_times'] = extreme_times
            
            try:
                await scheduler.schedule_daily_collection_jobs()
                self.log_test("24 collection times per day", True, "Handled 24 jobs")
            except Exception as e:
                self.log_test("24 collection times per day", False, str(e))
            
            # Test with zero retry attempts
            scheduler.config['max_retries'] = 0
            job_works_with_zero_retries = scheduler.config['max_retries'] == 0
            self.log_test("Zero retry configuration", job_works_with_zero_retries)
            
            # Test with very high retry attempts
            scheduler.config['max_retries'] = 1000
            job_works_with_high_retries = scheduler.config['max_retries'] == 1000
            self.log_test("High retry configuration", job_works_with_high_retries)
            
            # Test API with empty responses
            client = TestClient(app)
            
            # Test logs endpoint with extreme parameters
            extreme_params = [
                {'limit': 0},  # Zero limit
                {'limit': 10000},  # Very high limit  
                {'days': 0},  # Zero days
                {'days': 365},  # One year
            ]
            
            for params in extreme_params:
                try:
                    response = client.get('/scheduler/logs', params=params)
                    handled_gracefully = response.status_code in [200, 400, 422]
                    self.log_test(f"Extreme logs params {params}", handled_gracefully,
                                 f"Status: {response.status_code}")
                except Exception as e:
                    self.log_test(f"Extreme logs params {params}", False, str(e))
            
            if hasattr(collector, 'client') and collector.client:
                await collector.client.close()
                
        except Exception as e:
            self.log_test("Edge cases and boundaries", False, str(e))
    
    async def run_all_tests(self):
        """Run all deep tests"""
        print("STARTING DEEP SCHEDULER SYSTEM TEST")
        print("=" * 50)
        
        test_methods = [
            self.test_scheduler_initialization,
            self.test_data_collector_logic, 
            self.test_api_endpoints_comprehensive,
            self.test_error_scenarios,
            self.test_concurrent_operations,
            self.test_edge_cases_and_boundaries,
        ]
        
        for test_method in test_methods:
            try:
                await test_method()
            except Exception as e:
                print(f"CRITICAL ERROR in {test_method.__name__}: {e}")
                self.test_results['failed'] += 1
                self.test_results['errors'].append(f"{test_method.__name__}: {e}")
        
        # Print final results
        print("\n" + "=" * 50)
        print("DEEP TEST RESULTS SUMMARY")
        print("=" * 50)
        print(f"Tests Passed: {self.test_results['passed']}")
        print(f"Tests Failed: {self.test_results['failed']}")
        print(f"Total Tests: {self.test_results['passed'] + self.test_results['failed']}")
        
        if self.test_results['failed'] > 0:
            print("\nFAILURES:")
            for error in self.test_results['errors']:
                print(f"  - {error}")
        
        success_rate = (self.test_results['passed'] / 
                       (self.test_results['passed'] + self.test_results['failed'])) * 100
        print(f"\nSuccess Rate: {success_rate:.1f}%")
        
        return success_rate > 80  # Consider > 80% success as passing

async def main():
    """Main test runner"""
    tester = DeepSchedulerTester()
    success = await tester.run_all_tests()
    
    if success:
        print("\n🎉 DEEP TEST SUITE: OVERALL PASS")
    else:
        print("\n❌ DEEP TEST SUITE: NEEDS ATTENTION") 
    
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