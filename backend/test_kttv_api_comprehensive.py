#!/usr/bin/env python3
"""
Comprehensive KTTV API testing with various authentication methods and parameters
"""
import asyncio
import httpx
import json
import logging
from datetime import datetime, timedelta
from config import *

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class KTTVAPITester:
    """Comprehensive KTTV API testing"""
    
    def __init__(self):
        self.base_urls = {
            'stations': STATIONS_API_BASE_URL_KTTV,
            'stats': STATS_API_BASE_URL_KTTV
        }
        self.api_key = API_KEY
        
    async def test_authentication_methods(self, url: str, endpoint_name: str):
        """Test various authentication methods for KTTV API"""
        
        auth_methods = [
            # Method 1: No authentication (public endpoint)
            {
                'name': 'No Auth (Public)',
                'headers': {},
                'params': {}
            },
            # Method 2: API Key in header (x-api-key)
            {
                'name': 'API Key Header (x-api-key)',
                'headers': {'x-api-key': self.api_key},
                'params': {}
            },
            # Method 3: API Key in query parameter
            {
                'name': 'API Key Query Param',
                'headers': {},
                'params': {'api_key': self.api_key}
            },
            # Method 4: Different header names
            {
                'name': 'Authorization Bearer',
                'headers': {'Authorization': f'Bearer {self.api_key}'},
                'params': {}
            },
            # Method 5: Alternative header names
            {
                'name': 'API-KEY Header',
                'headers': {'API-KEY': self.api_key},
                'params': {}
            },
            # Method 6: Alternative query param names
            {
                'name': 'Key Query Param',
                'headers': {},
                'params': {'key': self.api_key}
            },
            # Method 7: Token in header
            {
                'name': 'Token Header',
                'headers': {'token': self.api_key},
                'params': {}
            },
            # Method 8: Basic auth style
            {
                'name': 'Authorization API-Key',
                'headers': {'Authorization': f'API-Key {self.api_key}'},
                'params': {}
            }
        ]
        
        logger.info(f"\n🔍 Testing {endpoint_name} endpoint: {url}")
        logger.info("=" * 60)
        
        successful_methods = []
        
        for method in auth_methods:
            try:
                logger.info(f"\n🧪 Testing: {method['name']}")
                logger.info(f"   Headers: {method['headers']}")
                logger.info(f"   Params: {method['params']}")
                
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.get(
                        url, 
                        headers=method['headers'], 
                        params=method['params']
                    )
                    
                    logger.info(f"   Status: {response.status_code}")
                    
                    if response.status_code == 200:
                        data = response.json()
                        logger.info(f"   ✅ SUCCESS! Response type: {type(data)}")
                        
                        if isinstance(data, dict):
                            logger.info(f"   Keys: {list(data.keys())}")
                        elif isinstance(data, list):
                            logger.info(f"   Array length: {len(data)}")
                            if data and isinstance(data[0], dict):
                                logger.info(f"   First item keys: {list(data[0].keys())}")
                        
                        successful_methods.append({
                            'method': method['name'],
                            'headers': method['headers'],
                            'params': method['params'],
                            'response_sample': str(data)[:200] + "..." if len(str(data)) > 200 else str(data)
                        })
                    elif response.status_code == 403:
                        logger.info(f"   ❌ Forbidden (403)")
                    elif response.status_code == 401:
                        logger.info(f"   ❌ Unauthorized (401)")
                    elif response.status_code == 404:
                        logger.info(f"   ❌ Not Found (404)")
                    else:
                        logger.info(f"   ❌ Error {response.status_code}: {response.text[:100]}")
                        
            except Exception as e:
                logger.error(f"   ❌ Exception: {e}")
        
        return successful_methods
    
    async def test_time_parameters(self, successful_method: dict):
        """Test stats endpoint with time parameters"""
        if not successful_method:
            logger.warning("⚠️ No successful authentication method found")
            return
        
        logger.info(f"\n📅 Testing time parameters with: {successful_method['method']}")
        logger.info("=" * 50)
        
        # Test different time ranges (last 2 months as requested)
        end_time = datetime.now()
        start_time = end_time - timedelta(days=60)  # 2 months
        
        time_formats = [
            # Format 1: Standard format
            {
                'name': 'Standard Format',
                'start_time': start_time.strftime('%Y-%m-%d %H:%M:%S'),
                'end_time': end_time.strftime('%Y-%m-%d %H:%M:%S')
            },
            # Format 2: ISO format
            {
                'name': 'ISO Format',
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat()
            },
            # Format 3: Date only
            {
                'name': 'Date Only',
                'start_time': start_time.strftime('%Y-%m-%d'),
                'end_time': end_time.strftime('%Y-%m-%d')
            },
            # Format 4: Unix timestamp
            {
                'name': 'Unix Timestamp',
                'start_time': str(int(start_time.timestamp())),
                'end_time': str(int(end_time.timestamp()))
            }
        ]
        
        stats_url = self.base_urls['stats']
        
        for time_format in time_formats:
            logger.info(f"\n🕐 Testing time format: {time_format['name']}")
            
            # Test different parameter names
            param_combinations = [
                {'start_time': time_format['start_time'], 'end_time': time_format['end_time']},
                {'startTime': time_format['start_time'], 'endTime': time_format['end_time']},
                {'from': time_format['start_time'], 'to': time_format['end_time']},
                {'start': time_format['start_time'], 'end': time_format['end_time']},
                {'begin': time_format['start_time'], 'finish': time_format['end_time']}
            ]
            
            for params in param_combinations:
                try:
                    # Combine with successful auth method
                    all_params = {**successful_method['params'], **params}
                    
                    logger.info(f"   Params: {params}")
                    
                    async with httpx.AsyncClient(timeout=30.0) as client:
                        response = await client.get(
                            stats_url,
                            headers=successful_method['headers'],
                            params=all_params
                        )
                        
                        logger.info(f"   Status: {response.status_code}")
                        
                        if response.status_code == 200:
                            data = response.json()
                            logger.info(f"   ✅ SUCCESS! Data type: {type(data)}")
                            
                            if isinstance(data, dict) and data:
                                logger.info(f"   Keys: {list(data.keys())[:5]}")  # Show first 5 keys
                            elif isinstance(data, list) and data:
                                logger.info(f"   Array length: {len(data)}")
                                
                            return {
                                'method': successful_method,
                                'time_params': params,
                                'data_sample': data
                            }
                        else:
                            logger.info(f"   ❌ Error: {response.status_code}")
                            
                except Exception as e:
                    logger.error(f"   ❌ Exception: {e}")
        
        return None
    
    async def analyze_response_structure(self, successful_response):
        """Analyze successful response structure"""
        if not successful_response:
            return
            
        logger.info(f"\n🔬 Analyzing Response Structure")
        logger.info("=" * 40)
        
        data = successful_response['data_sample']
        
        if isinstance(data, dict):
            logger.info("📊 Response is a dictionary")
            for key, value in list(data.items())[:3]:  # Show first 3 items
                logger.info(f"   {key}: {type(value)}")
                if isinstance(value, list) and value:
                    logger.info(f"      First item: {type(value[0])}")
                    if isinstance(value[0], dict):
                        logger.info(f"      First item keys: {list(value[0].keys())}")
                elif isinstance(value, dict):
                    logger.info(f"      Keys: {list(value.keys())[:3]}")
        
        elif isinstance(data, list):
            logger.info(f"📊 Response is an array with {len(data)} items")
            if data and isinstance(data[0], dict):
                logger.info(f"   First item keys: {list(data[0].keys())}")
    
    async def run_comprehensive_test(self):
        """Run comprehensive KTTV API test"""
        logger.info("🚀 Starting Comprehensive KTTV API Test")
        logger.info("=" * 60)
        
        results = {
            'stations': {'successful_methods': [], 'working_config': None},
            'stats': {'successful_methods': [], 'working_config': None}
        }
        
        # Test stations endpoint
        logger.info("\n📡 Testing STATIONS endpoint")
        stations_methods = await self.test_authentication_methods(
            self.base_urls['stations'], 'STATIONS'
        )
        results['stations']['successful_methods'] = stations_methods
        
        # Test stats endpoint
        logger.info("\n📊 Testing STATS endpoint")
        stats_methods = await self.test_authentication_methods(
            self.base_urls['stats'], 'STATS'
        )
        results['stats']['successful_methods'] = stats_methods
        
        # If stats endpoint has successful methods, test time parameters
        if stats_methods:
            logger.info(f"\n⏰ Testing time parameters for STATS")
            working_stats = await self.test_time_parameters(stats_methods[0])
            if working_stats:
                results['stats']['working_config'] = working_stats
                await self.analyze_response_structure(working_stats)
        
        # Generate final report
        logger.info("\n" + "=" * 60)
        logger.info("📋 COMPREHENSIVE TEST RESULTS")
        logger.info("=" * 60)
        
        for endpoint, result in results.items():
            logger.info(f"\n🔍 {endpoint.upper()} Endpoint:")
            if result['successful_methods']:
                logger.info(f"   ✅ Found {len(result['successful_methods'])} working methods")
                for method in result['successful_methods']:
                    logger.info(f"      - {method['method']}")
                
                if result.get('working_config'):
                    logger.info(f"   ✅ Time parameters working")
                    config = result['working_config']
                    logger.info(f"      Method: {config['method']['method']}")
                    logger.info(f"      Time params: {config['time_params']}")
            else:
                logger.info(f"   ❌ No working authentication methods found")
        
        return results

async def main():
    """Main test function"""
    tester = KTTVAPITester()
    results = await tester.run_comprehensive_test()
    
    # Save results to file
    with open('kttv_api_test_results.json', 'w', encoding='utf-8') as f:
        # Convert any non-serializable objects to strings
        serializable_results = json.loads(json.dumps(results, default=str))
        json.dump(serializable_results, f, indent=2, ensure_ascii=False)
    
    logger.info(f"\n💾 Detailed results saved to kttv_api_test_results.json")

if __name__ == "__main__":
    asyncio.run(main())