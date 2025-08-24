#!/usr/bin/env python3
"""
Test KTTV API với tham số thời gian để lấy dữ liệu 2 tháng
"""
import asyncio
import httpx
import json
import logging
from datetime import datetime, timedelta
from config import *

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_kttv_stats_with_time():
    """Test KTTV stats API với các tham số thời gian khác nhau"""
    
    api_key = API_KEY
    stations_url = STATIONS_API_BASE_URL_KTTV
    stats_url = STATS_API_BASE_URL_KTTV
    
    headers = {'x-api-key': api_key}
    
    logger.info("🔍 Testing KTTV API with time parameters")
    logger.info("=" * 50)
    
    # 1. First get stations
    logger.info("\n📡 Step 1: Getting KTTV stations...")
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(stations_url, headers=headers)
            
            if response.status_code == 200:
                stations = response.json()
                logger.info(f"✅ Found {len(stations)} KTTV stations")
                
                # Show sample stations
                for i, station in enumerate(stations[:3]):
                    logger.info(f"   Station {i+1}: {station['code']} - {station['name']}")
                
            else:
                logger.error(f"❌ Failed to get stations: {response.status_code}")
                return
                
    except Exception as e:
        logger.error(f"❌ Error getting stations: {e}")
        return
    
    # 2. Test stats with different time formats and ranges
    logger.info("\n📊 Step 2: Testing stats endpoint with time parameters...")
    
    # Create time ranges (2 months as requested)
    end_time = datetime.now()
    start_time = end_time - timedelta(days=60)  # 2 months
    
    # Different time ranges to test
    time_ranges = [
        {
            'name': '2 months (60 days)',
            'start': end_time - timedelta(days=60),
            'end': end_time
        },
        {
            'name': '1 month (30 days)', 
            'start': end_time - timedelta(days=30),
            'end': end_time
        },
        {
            'name': '1 week (7 days)',
            'start': end_time - timedelta(days=7),
            'end': end_time
        },
        {
            'name': '1 day (yesterday)',
            'start': end_time - timedelta(days=1),
            'end': end_time
        }
    ]
    
    # Different time formats to test
    time_formats = [
        {
            'name': 'Standard Format (YYYY-MM-DD HH:MM:SS)',
            'formatter': lambda dt: dt.strftime('%Y-%m-%d %H:%M:%S')
        },
        {
            'name': 'Date Only (YYYY-MM-DD)',
            'formatter': lambda dt: dt.strftime('%Y-%m-%d')
        },
        {
            'name': 'ISO Format',
            'formatter': lambda dt: dt.isoformat()
        },
        {
            'name': 'ISO Format with Z',
            'formatter': lambda dt: dt.strftime('%Y-%m-%dT%H:%M:%SZ')
        }
    ]
    
    # Different parameter names to test
    param_names = [
        {'start': 'start_time', 'end': 'end_time'},
        {'start': 'startTime', 'end': 'endTime'},
        {'start': 'from', 'end': 'to'},
        {'start': 'begin', 'end': 'finish'},
        {'start': 'start', 'end': 'end'}
    ]
    
    successful_configs = []
    
    for time_range in time_ranges:
        logger.info(f"\n⏰ Testing time range: {time_range['name']}")
        
        for time_format in time_formats:
            logger.info(f"\n📅 Testing format: {time_format['name']}")
            
            start_formatted = time_format['formatter'](time_range['start'])
            end_formatted = time_format['formatter'](time_range['end'])
            
            for param_combo in param_names:
                logger.info(f"   Trying params: {param_combo['start']} & {param_combo['end']}")
                
                params = {
                    param_combo['start']: start_formatted,
                    param_combo['end']: end_formatted
                }
                
                try:
                    async with httpx.AsyncClient(timeout=30.0) as client:
                        response = await client.get(
                            stats_url, 
                            headers=headers, 
                            params=params
                        )
                        
                        logger.info(f"      Status: {response.status_code}")
                        
                        if response.status_code == 200:
                            data = response.json()
                            
                            if isinstance(data, dict) and data:
                                logger.info(f"      ✅ SUCCESS! Found {len(data)} station records")
                                
                                # Analyze first few records
                                for i, (station_uuid, measurements) in enumerate(list(data.items())[:2]):
                                    if measurements:
                                        logger.info(f"         Station {i+1}: {len(measurements)} measurements")
                                        if isinstance(measurements, list) and measurements:
                                            first_measurement = measurements[0]
                                            logger.info(f"         First measurement keys: {list(first_measurement.keys())}")
                                
                                successful_configs.append({
                                    'time_range': time_range['name'],
                                    'time_format': time_format['name'],
                                    'params': params,
                                    'data_sample': {k: v[:2] if isinstance(v, list) else v for k, v in list(data.items())[:2]}
                                })
                                
                                # Stop on first success for this time range
                                break
                                
                            elif isinstance(data, list):
                                logger.info(f"      ✅ SUCCESS! Found {len(data)} records")
                                successful_configs.append({
                                    'time_range': time_range['name'],
                                    'time_format': time_format['name'],
                                    'params': params,
                                    'data_sample': data[:2]  # First 2 items
                                })
                                break
                            else:
                                logger.info(f"      ⚠️ Empty response")
                                
                        elif response.status_code == 400:
                            error_text = response.text
                            logger.info(f"      ❌ Bad Request: {error_text[:100]}...")
                            
                        elif response.status_code == 403:
                            logger.info(f"      ❌ Forbidden")
                            
                        else:
                            logger.info(f"      ❌ Error {response.status_code}: {response.text[:50]}")
                            
                except Exception as e:
                    logger.error(f"      ❌ Exception: {e}")
                
                # If we found a working config, break inner loops
                if successful_configs and successful_configs[-1]['time_range'] == time_range['name']:
                    break
            
            # If we found a working config, break format loop
            if successful_configs and successful_configs[-1]['time_range'] == time_range['name']:
                break
    
    # Report results
    logger.info("\n" + "=" * 60)
    logger.info("📋 KTTV API TEST RESULTS")
    logger.info("=" * 60)
    
    logger.info(f"✅ STATIONS Endpoint: Working (34 stations)")
    logger.info(f"✅ STATS Endpoint: {'Working' if successful_configs else 'Failed'}")
    
    if successful_configs:
        logger.info(f"\n🎉 Found {len(successful_configs)} working configurations:")
        for config in successful_configs:
            logger.info(f"\n   📊 {config['time_range']}:")
            logger.info(f"      Format: {config['time_format']}")
            logger.info(f"      Params: {config['params']}")
            
            # Show data sample
            data_sample = config['data_sample']
            if isinstance(data_sample, dict):
                logger.info(f"      Data: {len(data_sample)} stations with measurements")
            elif isinstance(data_sample, list):
                logger.info(f"      Data: {len(data_sample)} measurement records")
    
    # Save results
    with open('kttv_working_config.json', 'w', encoding='utf-8') as f:
        result = {
            'stations_working': True,
            'stats_working': len(successful_configs) > 0,
            'total_stations': len(stations) if 'stations' in locals() else 0,
            'working_configs': successful_configs
        }
        json.dump(result, f, indent=2, ensure_ascii=False, default=str)
    
    logger.info(f"\n💾 Results saved to kttv_working_config.json")
    
    return successful_configs

if __name__ == "__main__":
    asyncio.run(test_kttv_stats_with_time())