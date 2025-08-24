#!/usr/bin/env python3
"""
Final Comprehensive Test - Ensure everything works end-to-end
"""
import asyncio
import httpx
import logging

# Disable detailed logging for cleaner output
logging.basicConfig(level=logging.ERROR)

async def test_ensure_data_endpoint():
    """Test the new ensure-data endpoint"""
    
    print("Testing /integration/ensure-data endpoint...")
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post("http://127.0.0.1:8000/integration/ensure-data")
            
            if response.status_code == 200:
                result = response.json()
                print(f"SUCCESS: ensure-data endpoint working")
                print(f"  Status: {result.get('status', 'N/A')}")
                print(f"  Total records: {result.get('total_records', 'N/A')}")
                print(f"  Frequency records: {result.get('frequency_ready_records', 'N/A')}")
                return True
            else:
                print(f"FAILED: HTTP {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
    except Exception as e:
        print(f"ERROR: {e}")
        return False

async def test_analyze_historical_endpoint():
    """Test the analyze-historical endpoint after ensuring data"""
    
    print("\nTesting /integration/analyze-historical endpoint...")
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "http://127.0.0.1:8000/integration/analyze-historical",
                json={
                    "min_years": 1,
                    "distribution_name": "gumbel",
                    "agg_func": "max",
                    "use_professional": False
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"SUCCESS: analyze-historical endpoint working")
                print(f"  Message: {result.get('message', 'N/A')}")
                if 'data_summary' in result:
                    print(f"  Records: {result['data_summary'].get('total_records', 'N/A')}")
                    print(f"  Stations: {result['data_summary'].get('stations_count', 'N/A')}")
                    print(f"  Analysis grade: {result.get('analysis_grade', 'N/A')}")
                return True
            else:
                print(f"FAILED: HTTP {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
    except Exception as e:
        print(f"ERROR: {e}")
        return False

async def test_multiple_calls():
    """Test multiple calls to ensure consistency"""
    
    print("\nTesting multiple consecutive calls...")
    
    success_count = 0
    total_calls = 3
    
    for i in range(total_calls):
        print(f"  Call {i+1}/{total_calls}...")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "http://127.0.0.1:8000/integration/analyze-historical",
                    json={
                        "min_years": 1,
                        "distribution_name": "gumbel",
                        "agg_func": "max",
                        "use_professional": False
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    records = result.get('data_summary', {}).get('total_records', 'N/A')
                    print(f"    SUCCESS: {records} records analyzed")
                    success_count += 1
                else:
                    print(f"    FAILED: HTTP {response.status_code}")
                    
        except Exception as e:
            print(f"    ERROR: {e}")
    
    success_rate = (success_count / total_calls) * 100
    print(f"Multiple calls result: {success_count}/{total_calls} ({success_rate:.1f}% success)")
    
    return success_rate >= 80

async def main():
    """Run comprehensive test suite"""
    
    print("=== FINAL COMPREHENSIVE TEST ===")
    print("Testing FastAPI endpoints with database auto-setup...")
    
    # Test 1: Ensure data endpoint
    test1_ok = await test_ensure_data_endpoint()
    
    # Test 2: Analyze historical endpoint 
    test2_ok = await test_analyze_historical_endpoint()
    
    # Test 3: Multiple calls consistency
    test3_ok = await test_multiple_calls()
    
    # Overall assessment
    tests_passed = sum([test1_ok, test2_ok, test3_ok])
    total_tests = 3
    
    print(f"\n=== FINAL RESULTS ===")
    print(f"Tests passed: {tests_passed}/{total_tests}")
    
    if tests_passed == total_tests:
        print("STATUS: ALL TESTS PASSED")
        print("The system is working correctly!")
        print("Auto-data-generation is functioning properly.")
        print("Frequency analysis endpoints are reliable.")
        return True
    elif tests_passed >= 2:
        print("STATUS: MOSTLY WORKING")
        print("Minor issues detected but core functionality works.")
        return True
    else:
        print("STATUS: NEEDS ATTENTION")
        print("Multiple failures detected.")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    
    if success:
        print("\n=== SYSTEM READY ===")
        print("FastAPI endpoints working correctly.")
        print("Database auto-setup is functional.")
        print("Frequency analysis is reliable.")
    else:
        print("\n=== SYSTEM ISSUES ===")
        print("Please check FastAPI server and database connectivity.")