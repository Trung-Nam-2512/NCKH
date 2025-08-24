#!/usr/bin/env python3
"""
Test FastAPI server directly to identify the database connection issue
"""
import asyncio
import httpx
import json
import logging
from app.services.realtime_service import EnhancedRealtimeService
from app.services.data_service import DataService

logging.basicConfig(level=logging.ERROR)  # Reduce noise

async def prepare_data_for_fastapi_test():
    """Prepare data specifically for FastAPI test"""
    
    print("Step 1: Preparing data for FastAPI test...")
    
    data_service = DataService()
    realtime_service = EnhancedRealtimeService(data_service)
    await realtime_service.initialize_database()
    
    # Generate and insert data
    from create_test_data import generate_realistic_water_level_data
    
    test_records = generate_realistic_water_level_data()
    print(f"Generated {len(test_records)} test records")
    
    collection = realtime_service.db.realtime_data
    await collection.delete_many({})  # Clear
    
    # Insert in batches
    batch_size = 1000
    for i in range(0, len(test_records), batch_size):
        batch = test_records[i:i+batch_size]
        await collection.insert_many(batch)
    
    final_count = await collection.count_documents({})
    print(f"Inserted {final_count} records into database")
    
    # Verify frequency data
    freq_data = await realtime_service.get_frequency_ready_data(min_years=1)
    print(f"Frequency-ready data: {len(freq_data)} records")
    
    return final_count > 0

async def test_fastapi_endpoint():
    """Test the actual FastAPI endpoint"""
    
    print("\nStep 2: Testing FastAPI endpoint...")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Test the integration endpoint
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
                print("SUCCESS: FastAPI endpoint worked!")
                print(f"Message: {result.get('message', 'N/A')}")
                if 'data_summary' in result:
                    print(f"Records: {result['data_summary'].get('total_records', 'N/A')}")
                    print(f"Stations: {result['data_summary'].get('stations_count', 'N/A')}")
                return True
            else:
                print(f"FAILED: HTTP {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
    except Exception as e:
        print(f"ERROR connecting to FastAPI: {e}")
        return False

async def main():
    print("=== COMPREHENSIVE FASTAPI TEST ===")
    
    # Step 1: Prepare data
    data_prepared = await prepare_data_for_fastapi_test()
    
    if not data_prepared:
        print("FAILED: Could not prepare data")
        return False
    
    # Step 2: Test FastAPI
    api_working = await test_fastapi_endpoint()
    
    if api_working:
        print("\nSUCCESS: Everything working correctly!")
        print("The issue may be intermittent or related to timing.")
        return True
    else:
        print("\nFAILED: FastAPI endpoint not working")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    if success:
        print("\nSystem is working correctly.")
    else:
        print("\nSystem has issues that need resolution.")