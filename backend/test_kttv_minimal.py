#!/usr/bin/env python3
"""
Minimal KTTV API test with shorter time ranges
"""
import asyncio
import httpx
import json
import logging
from datetime import datetime, timedelta
from config import *

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_kttv_minimal():
    """Test KTTV API with minimal requests"""
    
    api_key = API_KEY
    stations_url = STATIONS_API_BASE_URL_KTTV
    stats_url = STATS_API_BASE_URL_KTTV
    headers = {'x-api-key': api_key}
    
    logger.info("🔍 Minimal KTTV API Test")
    logger.info("=" * 40)
    
    # 1. Get stations
    logger.info("\n📡 Getting KTTV stations...")
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(stations_url, headers=headers)
            
            if response.status_code == 200:
                stations = response.json()
                logger.info(f"✅ Found {len(stations)} KTTV stations")
                
                # Show first 3 stations
                for i, station in enumerate(stations[:3]):
                    logger.info(f"   {i+1}. {station['code']} - {station['name']}")
                    logger.info(f"      UUID: {station['uuid']}")
                    logger.info(f"      Location: {station['latitude']}, {station['longitude']}")
                
            else:
                logger.error(f"❌ Stations failed: {response.status_code}")
                return
                
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return
    
    # 2. Test stats with very short time ranges
    logger.info(f"\n📊 Testing stats endpoint with short time ranges...")
    
    # Try very short time ranges
    time_ranges = [
        {
            'name': '1 hour',
            'start': datetime.now() - timedelta(hours=1),
            'end': datetime.now()
        },
        {
            'name': '3 hours',
            'start': datetime.now() - timedelta(hours=3),
            'end': datetime.now()
        },
        {
            'name': '6 hours',
            'start': datetime.now() - timedelta(hours=6),
            'end': datetime.now()
        },
        {
            'name': '12 hours',
            'start': datetime.now() - timedelta(hours=12),
            'end': datetime.now()
        },
        {
            'name': '1 day',
            'start': datetime.now() - timedelta(days=1),
            'end': datetime.now()
        }
    ]
    
    working_configs = []
    
    for time_range in time_ranges:
        logger.info(f"\n⏰ Testing: {time_range['name']}")
        
        # Standard format with start_time/end_time
        start_time = time_range['start'].strftime('%Y-%m-%d %H:%M:%S')
        end_time = time_range['end'].strftime('%Y-%m-%d %H:%M:%S')
        
        params = {
            'start_time': start_time,
            'end_time': end_time
        }
        
        try:
            logger.info(f"   Params: {params}")
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(stats_url, headers=headers, params=params)
                
                logger.info(f"   Status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"   ✅ SUCCESS!")
                    
                    if isinstance(data, dict):
                        logger.info(f"   📊 Found data for {len(data)} stations")
                        
                        # Show sample data
                        sample_stations = list(data.keys())[:2]
                        for station_uuid in sample_stations:
                            measurements = data[station_uuid]
                            if measurements:
                                logger.info(f"      Station {station_uuid[:8]}...: {len(measurements)} measurements")
                                if isinstance(measurements, list) and measurements:
                                    first_measurement = measurements[0]
                                    logger.info(f"         Sample: {first_measurement}")
                        
                        working_configs.append({
                            'time_range': time_range['name'],
                            'params': params,
                            'stations_count': len(data),
                            'sample_data': {k: v[:1] for k, v in list(data.items())[:2]}
                        })
                        
                        # Stop on first success
                        break
                        
                    elif isinstance(data, list):
                        logger.info(f"   📊 Found {len(data)} records")
                        working_configs.append({
                            'time_range': time_range['name'],
                            'params': params,
                            'records_count': len(data),
                            'sample_data': data[:1]
                        })
                        break
                    else:
                        logger.info(f"   ⚠️ Unexpected data type: {type(data)}")
                
                elif response.status_code == 400:
                    error = response.json()
                    logger.info(f"   ❌ Bad Request: {error.get('message', 'Unknown error')}")
                    
                elif response.status_code == 429:
                    logger.info(f"   ⚠️ Rate limited - waiting 5 seconds...")
                    await asyncio.sleep(5)
                    
                else:
                    logger.info(f"   ❌ Error {response.status_code}")
                
        except Exception as e:
            logger.error(f"   ❌ Exception: {e}")
        
        # Wait between requests to avoid rate limiting
        await asyncio.sleep(2)
    
    # Report results
    logger.info("\n" + "=" * 50)
    logger.info("📋 KTTV MINIMAL TEST RESULTS")
    logger.info("=" * 50)
    
    logger.info(f"✅ STATIONS: Working ({len(stations)} stations)")
    logger.info(f"📊 STATS: {'Working' if working_configs else 'Failed'}")
    
    if working_configs:
        config = working_configs[0]
        logger.info(f"\n🎉 Working Configuration:")
        logger.info(f"   Time Range: {config['time_range']}")
        logger.info(f"   Parameters: {config['params']}")
        logger.info(f"   Stations: {config.get('stations_count', config.get('records_count', 0))}")
        
        # Save working configuration
        result = {
            'kttv_working': True,
            'stations_count': len(stations),
            'working_config': config,
            'all_stations': stations[:5],  # First 5 stations
            'timestamp': datetime.now().isoformat()
        }
        
    else:
        logger.info("\n❌ No working configuration found")
        result = {
            'kttv_working': False,
            'stations_count': len(stations),
            'all_stations': stations[:5],
            'timestamp': datetime.now().isoformat()
        }
    
    # Save results
    with open('kttv_minimal_results.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False, default=str)
    
    logger.info(f"\n💾 Results saved to kttv_minimal_results.json")
    
    return result

if __name__ == "__main__":
    asyncio.run(test_kttv_minimal())