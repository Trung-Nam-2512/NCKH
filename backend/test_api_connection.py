#!/usr/bin/env python3
"""
Test API connection to get real-time data
"""
import asyncio
import httpx
import json
from datetime import datetime, timedelta

async def test_api_connection():
    """Test connection to the water level API"""
    
    # Test different API endpoints
    apis = [
        {
            'name': 'KTTV Open API',
            'url': 'https://kttv-open.vrain.vn/v1/stations',
            'params': {}
        },
        {
            'name': 'TSTV API',
            'url': 'https://tstv.baonamdts.com/api/stats',
            'params': {
                'start_time': '2025-08-02 05:00:00',
                'end_time': '2025-08-02 23:00:00',
                'api_key': '25ab243d80'
            }
        }
    ]
    
    for api in apis:
        print(f"\n🔍 Testing {api['name']}: {api['url']}")
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(api['url'], params=api['params'])
                print(f"Status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ Success! Data preview:")
                    print(json.dumps(data, indent=2)[:500] + "...")
                    
                    # Check if data has recent timestamps
                    if 'data' in data:
                        for station in data['data'][:3]:  # Check first 3 stations
                            if 'value' in station and station['value']:
                                latest_time = station['value'][-1].get('time_point', 'N/A')
                                print(f"Latest data time: {latest_time}")
                else:
                    print(f"❌ Error: {response.text[:200]}")
                    
        except Exception as e:
            print(f"❌ Connection failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_api_connection()) 