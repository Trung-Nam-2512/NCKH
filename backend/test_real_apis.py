#!/usr/bin/env python3
"""
Test real APIs to understand data structure
"""
import asyncio
import httpx
import json
import logging
from datetime import datetime, timedelta
from config import *

logging.basicConfig(level=logging.INFO)

async def test_real_apis():
    """Test both KTTV and non-KTTV APIs"""
    
    # API configurations
    apis = [
        {
            'name': 'Non-KTTV Stations',
            'url': STATIONS_API_BASE_URL_NOKTTV,
            'headers': {},
            'type': 'stations'
        },
        {
            'name': 'Non-KTTV Stats',
            'url': STATS_API_BASE_URL_NOKTTV,
            'headers': {
                'x-api-key': API_KEY
            },
            'type': 'stats'
        },
        {
            'name': 'KTTV Stations',
            'url': STATIONS_API_BASE_URL_KTTV,
            'headers': {},
            'type': 'stations'
        },
        {
            'name': 'KTTV Stats',
            'url': STATS_API_BASE_URL_KTTV,
            'headers': {},
            'type': 'stats'
        }
    ]
    
    for api in apis:
        logging.info(f"\n🔍 Testing {api['name']}: {api['url']}")
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(api['url'], headers=api['headers'])
                logging.info(f"Status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    logging.info(f"✅ {api['name']} is working!")
                    
                    # Analyze data structure
                    if api['type'] == 'stations':
                        stations = data.get('data', [])
                        logging.info(f"📊 Found {len(stations)} stations")
                        
                        if stations:
                            # Show first station structure
                            first_station = stations[0]
                            logging.info(f"📋 First station structure:")
                            logging.info(f"   Keys: {list(first_station.keys())}")
                            
                            # Look for code and coordinates
                            if 'code' in first_station:
                                logging.info(f"   Code: {first_station['code']}")
                            if 'latitude' in first_station:
                                logging.info(f"   Latitude: {first_station['latitude']}")
                            if 'longitude' in first_station:
                                logging.info(f"   Longitude: {first_station['longitude']}")
                            if 'name' in first_station:
                                logging.info(f"   Name: {first_station['name']}")
                    
                    elif api['type'] == 'stats':
                        stats = data.get('data', [])
                        logging.info(f"📊 Found {len(stats)} station stats")
                        
                        if stats:
                            # Show first stat structure
                            first_stat = stats[0]
                            logging.info(f"📋 First stat structure:")
                            logging.info(f"   Keys: {list(first_stat.keys())}")
                            
                            # Look for station_id and measurements
                            if 'station_id' in first_stat:
                                logging.info(f"   Station ID: {first_stat['station_id']}")
                            if 'value' in first_stat:
                                values = first_stat['value']
                                logging.info(f"   Values count: {len(values)}")
                                if values:
                                    latest_value = values[-1]
                                    logging.info(f"   Latest value keys: {list(latest_value.keys())}")
                                    if 'time_point' in latest_value:
                                        logging.info(f"   Latest time: {latest_value['time_point']}")
                                    if 'depth' in latest_value:
                                        logging.info(f"   Latest depth: {latest_value['depth']}")
                
                else:
                    logging.warning(f"❌ {api['name']} failed: {response.text[:200]}")
                    
        except Exception as e:
            logging.error(f"❌ {api['name']} connection failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_real_apis()) 