#!/usr/bin/env python3
"""
Comprehensive API testing and debugging script
Follows SOLID principles with proper separation of concerns
"""
import asyncio
import httpx
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from config import *

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class APITester:
    """Single Responsibility: Test and diagnose API endpoints"""
    
    def __init__(self):
        self.api_configs = {
            'nokttv': {
                'stations_url': STATIONS_API_BASE_URL_NOKTTV,
                'stats_url': STATS_API_BASE_URL_NOKTTV,
                'api_key': API_KEY,
                'name': 'Non-KTTV API'
            },
            'kttv': {
                'stations_url': STATIONS_API_BASE_URL_KTTV,
                'stats_url': STATS_API_BASE_URL_KTTV,
                'api_key': None,
                'name': 'KTTV API'
            }
        }
    
    async def test_endpoint(self, url: str, headers: Dict = None, params: Dict = None, 
                           endpoint_name: str = "") -> Tuple[int, Dict]:
        """Test a single endpoint with comprehensive error handling"""
        try:
            headers = headers or {}
            params = params or {}
            
            logging.info(f"🔍 Testing {endpoint_name}: {url}")
            logging.info(f"📋 Headers: {headers}")
            logging.info(f"📋 Params: {params}")
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, headers=headers, params=params)
                
                result = {
                    'status_code': response.status_code,
                    'headers': dict(response.headers),
                    'url': str(response.url),
                    'data': None,
                    'error': None
                }
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        result['data'] = data
                        logging.info(f"✅ {endpoint_name} successful - Status: {response.status_code}")
                        self._analyze_response_structure(data, endpoint_name)
                    except json.JSONDecodeError as e:
                        result['error'] = f"JSON decode error: {e}"
                        result['raw_text'] = response.text[:1000]
                        logging.error(f"❌ {endpoint_name} JSON error: {e}")
                else:
                    result['error'] = response.text[:1000]
                    logging.error(f"❌ {endpoint_name} failed - Status: {response.status_code}")
                    logging.error(f"Error: {response.text[:200]}")
                
                return response.status_code, result
                
        except Exception as e:
            logging.error(f"❌ {endpoint_name} connection error: {e}")
            return 0, {'error': str(e), 'status_code': 0}
    
    def _analyze_response_structure(self, data: Dict, endpoint_name: str):
        """Analyze and log response structure"""
        try:
            logging.info(f"📊 {endpoint_name} Response Analysis:")
            logging.info(f"   Type: {type(data)}")
            
            if isinstance(data, dict):
                logging.info(f"   Keys: {list(data.keys())}")
                
                # Look for data arrays
                for key in ['data', 'results', 'stations', 'stats']:
                    if key in data:
                        items = data[key]
                        if isinstance(items, list):
                            logging.info(f"   {key}: {len(items)} items")
                            if items:
                                first_item = items[0]
                                if isinstance(first_item, dict):
                                    logging.info(f"   First {key} item keys: {list(first_item.keys())}")
                                    
                                    # Look for specific fields
                                    for field in ['code', 'station_id', 'name', 'latitude', 'longitude']:
                                        if field in first_item:
                                            logging.info(f"   Found {field}: {first_item[field]}")
                        else:
                            logging.info(f"   {key}: {type(items)} - {items}")
            
            elif isinstance(data, list):
                logging.info(f"   Direct list with {len(data)} items")
                if data:
                    first_item = data[0]
                    if isinstance(first_item, dict):
                        logging.info(f"   First item keys: {list(first_item.keys())}")
                        
        except Exception as e:
            logging.error(f"❌ Response analysis error: {e}")

class AuthenticationTester:
    """Single Responsibility: Test different authentication methods"""
    
    def __init__(self, api_configs: Dict):
        self.api_configs = api_configs
    
    async def test_auth_methods(self, api_type: str, base_url: str):
        """Test different authentication methods"""
        config = self.api_configs[api_type]
        api_key = config.get('api_key')
        
        if not api_key:
            logging.info(f"⏭️ Skipping auth tests for {api_type} - no API key")
            return
        
        auth_methods = [
            ('x-api-key header', {'x-api-key': api_key}),
            ('api_key query param', {}, {'api_key': api_key}),
            ('key query param', {}, {'key': api_key}),
            ('Authorization header', {'Authorization': f'Bearer {api_key}'}),
            ('Authorization API-KEY', {'Authorization': f'API-KEY {api_key}'})
        ]
        
        tester = APITester()
        
        for method_name, headers, params in [(m[0], m[1], m[2] if len(m) > 2 else {}) for m in auth_methods]:
            logging.info(f"🔐 Testing {method_name} for {api_type}")
            status, result = await tester.test_endpoint(
                base_url, headers, params, f"{api_type} {method_name}"
            )
            if status == 200:
                logging.info(f"✅ {method_name} works for {api_type}!")
                return method_name
        
        return None

class DataIntegrityChecker:
    """Single Responsibility: Check data integrity and mapping issues"""
    
    @staticmethod
    def check_station_stats_mapping(stations: List[Dict], stats: List[Dict]) -> Dict:
        """Check if stations and stats can be properly mapped"""
        result = {
            'stations_count': len(stations),
            'stats_count': len(stats),
            'mappable_count': 0,
            'unmappable_stats': [],
            'station_keys': set(),
            'stats_keys': set(),
            'mapping_analysis': {}
        }
        
        if not stations or not stats:
            return result
        
        # Collect all possible keys
        for station in stations[:3]:  # Sample first 3
            if isinstance(station, dict):
                result['station_keys'].update(station.keys())
        
        for stat in stats[:3]:  # Sample first 3
            if isinstance(stat, dict):
                result['stats_keys'].update(stat.keys())
        
        # Create station lookup with multiple possible keys
        station_lookup = {}
        for station in stations:
            for key in ['code', 'station_id', 'id', 'stationId']:
                if key in station and station[key]:
                    station_lookup[str(station[key])] = station
        
        # Try to map stats to stations
        for stat in stats:
            mapped = False
            for key in ['station_id', 'code', 'id', 'stationId']:
                if key in stat and str(stat[key]) in station_lookup:
                    result['mappable_count'] += 1
                    mapped = True
                    break
            
            if not mapped:
                result['unmappable_stats'].append({k: v for k, v in stat.items() if k in ['station_id', 'code', 'id', 'stationId']})
        
        result['station_keys'] = list(result['station_keys'])
        result['stats_keys'] = list(result['stats_keys'])
        
        return result

async def main():
    """Main function to run comprehensive API tests"""
    logging.info("🚀 Starting comprehensive API testing...")
    
    tester = APITester()
    auth_tester = AuthenticationTester(tester.api_configs)
    checker = DataIntegrityChecker()
    
    results = {}
    
    for api_type, config in tester.api_configs.items():
        logging.info(f"\n{'='*50}")
        logging.info(f"Testing {config['name']} ({api_type.upper()})")
        logging.info(f"{'='*50}")
        
        api_results = {'stations': None, 'stats': None, 'auth_method': None}
        
        # Test authentication methods
        if config.get('api_key'):
            auth_method = await auth_tester.test_auth_methods(api_type, config['stations_url'])
            api_results['auth_method'] = auth_method
        
        # Test stations endpoint
        headers = {}
        if api_type == 'nokttv' and config.get('api_key'):
            headers['x-api-key'] = config['api_key']
        
        status, result = await tester.test_endpoint(
            config['stations_url'], headers, {}, f"{api_type} Stations"
        )
        api_results['stations'] = result
        
        # Test stats endpoint
        status, result = await tester.test_endpoint(
            config['stats_url'], headers, {}, f"{api_type} Stats"
        )
        api_results['stats'] = result
        
        # Check data mapping if both endpoints work
        if (api_results['stations'] and api_results['stations'].get('data') and 
            api_results['stats'] and api_results['stats'].get('data')):
            
            stations_data = api_results['stations']['data']
            stats_data = api_results['stats']['data']
            
            # Extract actual data arrays
            if isinstance(stations_data, dict):
                stations_data = stations_data.get('data', stations_data.get('stations', []))
            if isinstance(stats_data, dict):
                stats_data = stats_data.get('data', stats_data.get('stats', []))
            
            mapping_check = checker.check_station_stats_mapping(stations_data, stats_data)
            api_results['mapping_analysis'] = mapping_check
            
            logging.info(f"📊 Mapping Analysis for {api_type}:")
            logging.info(f"   Stations: {mapping_check['stations_count']}")
            logging.info(f"   Stats: {mapping_check['stats_count']}")
            logging.info(f"   Mappable: {mapping_check['mappable_count']}")
            logging.info(f"   Station keys: {mapping_check['station_keys']}")
            logging.info(f"   Stats keys: {mapping_check['stats_keys']}")
        
        results[api_type] = api_results
    
    # Generate comprehensive report
    logging.info(f"\n{'='*50}")
    logging.info("COMPREHENSIVE TEST REPORT")
    logging.info(f"{'='*50}")
    
    for api_type, api_results in results.items():
        config = tester.api_configs[api_type]
        logging.info(f"\n🔍 {config['name']} Summary:")
        
        stations_ok = api_results['stations'] and api_results['stations'].get('status_code') == 200
        stats_ok = api_results['stats'] and api_results['stats'].get('status_code') == 200
        
        logging.info(f"   Stations endpoint: {'✅' if stations_ok else '❌'}")
        logging.info(f"   Stats endpoint: {'✅' if stats_ok else '❌'}")
        
        if api_results.get('mapping_analysis'):
            ma = api_results['mapping_analysis']
            logging.info(f"   Data mapping: {ma['mappable_count']}/{ma['stats_count']} mappable")
        
        if not stations_ok:
            error = api_results['stations'].get('error', 'Unknown error')
            logging.info(f"   Stations error: {error[:100]}...")
        
        if not stats_ok:
            error = api_results['stats'].get('error', 'Unknown error')
            logging.info(f"   Stats error: {error[:100]}...")
    
    # Save detailed results to file
    with open('api_test_results.json', 'w', encoding='utf-8') as f:
        # Convert datetime objects to strings for JSON serialization
        json_results = json.loads(json.dumps(results, default=str))
        json.dump(json_results, f, indent=2, ensure_ascii=False)
    
    logging.info(f"\n💾 Detailed results saved to api_test_results.json")

if __name__ == "__main__":
    asyncio.run(main())