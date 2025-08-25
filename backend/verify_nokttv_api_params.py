#!/usr/bin/env python3
"""
VERIFY NOKTTV API PARAMETERS

Script để test chính xác NOKTTV API có hỗ trợ time parameters hay không
Cần test thực tế để biết chắc chắn API behavior
"""

import asyncio
import httpx
import sys
import os
from datetime import datetime, timedelta

# Add path
sys.path.append(os.path.dirname(__file__))
from config import *

async def test_nokttv_stations_api():
    """Test NOKTTV stations API"""
    print("\n=== TESTING NOKTTV STATIONS API ===")
    
    url = STATIONS_API_BASE_URL_NOKTTV
    headers = {'x-api-key': API_KEY} if API_KEY else {}
    
    print(f"URL: {url}")
    print(f"Headers: {headers}")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=headers)
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"Response type: {type(data)}")
                if isinstance(data, list):
                    print(f"Stations count: {len(data)}")
                    if data:
                        print(f"First station keys: {list(data[0].keys())}")
                elif isinstance(data, dict):
                    print(f"Response keys: {list(data.keys())}")
            else:
                print(f"Error: {response.text[:200]}")
                
    except Exception as e:
        print(f"Exception: {e}")

async def test_nokttv_stats_without_params():
    """Test NOKTTV stats API without time parameters"""
    print("\n=== TESTING NOKTTV STATS API (NO PARAMS) ===")
    
    url = STATS_API_BASE_URL_NOKTTV  
    headers = {'x-api-key': API_KEY} if API_KEY else {}
    
    print(f"URL: {url}")
    print(f"Headers: {headers}")
    print("Params: {} (empty)")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=headers)
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"Response type: {type(data)}")
                if isinstance(data, dict):
                    print(f"Stations in response: {len(data)}")
                    # Sample first station data
                    for uuid, measurements in list(data.items())[:1]:
                        print(f"Sample UUID: {uuid}")
                        print(f"Measurements type: {type(measurements)}")
                        if isinstance(measurements, list) and measurements:
                            print(f"Sample measurement keys: {list(measurements[0].keys()) if measurements[0] else 'empty'}")
                            if measurements:
                                sample = measurements[0]
                                time_field = sample.get('time_point', sample.get('timestamp', sample.get('time')))
                                print(f"Time field: {time_field}")
                elif isinstance(data, list):
                    print(f"List length: {len(data)}")
            else:
                print(f"Error: {response.text[:200]}")
                
    except Exception as e:
        print(f"Exception: {e}")

async def test_nokttv_stats_with_time_params():
    """Test NOKTTV stats API WITH time parameters"""
    print("\n=== TESTING NOKTTV STATS API (WITH TIME PARAMS) ===")
    
    url = STATS_API_BASE_URL_NOKTTV
    headers = {'x-api-key': API_KEY} if API_KEY else {}
    
    # Test time parameters  
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=2)
    
    params = {
        'start_time': start_time.strftime('%Y-%m-%d %H:%M:%S'),
        'end_time': end_time.strftime('%Y-%m-%d %H:%M:%S')
    }
    
    print(f"URL: {url}")
    print(f"Headers: {headers}")  
    print(f"Params: {params}")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=headers, params=params)
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"Response type: {type(data)}")
                if isinstance(data, dict):
                    print(f"Stations in response: {len(data)}")
                    print("✅ NOKTTV API ACCEPTS TIME PARAMETERS!")
                    
                    # Compare data volume with no-params version
                    print("📊 Time-filtered data received successfully")
                elif isinstance(data, list):
                    print(f"List length: {len(data)}")
                    print("✅ NOKTTV API ACCEPTS TIME PARAMETERS!")
            else:
                print(f"❌ Failed with time params: {response.status_code}")
                print(f"Error: {response.text[:200]}")
                print("❓ NOKTTV API might NOT support time parameters")
                
    except Exception as e:
        print(f"Exception: {e}")

async def test_nokttv_stats_different_time_formats():
    """Test different time parameter formats"""
    print("\n=== TESTING DIFFERENT TIME FORMATS ===")
    
    url = STATS_API_BASE_URL_NOKTTV
    headers = {'x-api-key': API_KEY} if API_KEY else {}
    
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=1)
    
    # Different format attempts
    formats_to_test = [
        {
            'name': 'YYYY-MM-DD HH:MM:SS', 
            'params': {
                'start_time': start_time.strftime('%Y-%m-%d %H:%M:%S'),
                'end_time': end_time.strftime('%Y-%m-%d %H:%M:%S')
            }
        },
        {
            'name': 'ISO format',
            'params': {
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat()
            }
        },
        {
            'name': 'Date only',
            'params': {
                'date': datetime.now().strftime('%Y-%m-%d')
            }
        }
    ]
    
    for fmt in formats_to_test:
        print(f"\nTesting {fmt['name']}: {fmt['params']}")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, headers=headers, params=fmt['params'])
                print(f"  Status: {response.status_code}")
                
                if response.status_code == 200:
                    print(f"  ✅ {fmt['name']} format WORKS!")
                else:
                    print(f"  ❌ {fmt['name']} format failed: {response.text[:100]}")
                    
        except Exception as e:
            print(f"  Exception: {e}")

async def main():
    """Main test function"""
    print("🔍 NOKTTV API PARAMETER VERIFICATION")
    print("="*50)
    print("Testing to determine if NOKTTV API supports time parameters...")
    
    # Test stations (known to work)
    await test_nokttv_stations_api()
    
    # Test stats without params (current approach)
    await test_nokttv_stats_without_params()
    
    # Test stats WITH time params (unknown if supported)
    await test_nokttv_stats_with_time_params()
    
    # Test different time formats
    await test_nokttv_stats_different_time_formats()
    
    print("\n" + "="*50)
    print("📊 CONCLUSION:")
    print("Based on the results above:")
    print("1. If time params work → NOKTTV DOES support time filtering")  
    print("2. If time params fail → NOKTTV only returns current data")
    print("3. This will determine the correct collection strategy")

if __name__ == "__main__":
    asyncio.run(main())