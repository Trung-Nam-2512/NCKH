#!/usr/bin/env python3
"""
CORRECTED DAILY DATA COLLECTOR

CORRECTED UNDERSTANDING:
1. KTTV Stats API: DEFINITELY has start_time/end_time params (confirmed in code)
2. NOKTTV Stats API: UNKNOWN - need to test if it supports time params
3. Collection strategy depends on actual API capabilities

STRATEGY:
- Test both APIs with and without time parameters  
- Implement adaptive collection based on API behavior
- Use time-window approach for APIs that support it
- Use current-data approach for APIs that don't support time params
"""

import asyncio
import httpx
import logging
import sys
import os
from datetime import datetime, timedelta, date
from typing import List, Dict, Optional, Tuple
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import UpdateOne
from pymongo.errors import BulkWriteError
import json

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from config import *

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
    handlers=[
        logging.FileHandler('corrected_daily_collector.log'),
        logging.StreamHandler()
    ]
)

class CorrectedDailyDataCollector:
    """
    CORRECTED DATA COLLECTOR với adaptive API handling
    
    Key Features:
    1. Auto-detect API capabilities (time params support)
    2. Adaptive collection strategies based on actual API behavior
    3. Proper duplicate prevention for each API type
    4. Time-window collection for time-aware APIs
    5. Current-data collection for non-time-aware APIs
    """
    
    def __init__(self):
        """Initialize với adaptive configuration"""
        self.mongo_uri = MONGODB_URI
        self.client = None
        self.db = None
        
        # Base API configurations
        self.api_configs = {
            'nokttv': {
                'stations_url': STATIONS_API_BASE_URL_NOKTTV,
                'stats_url': STATS_API_BASE_URL_NOKTTV,
                'api_key': API_KEY,
                'type': 'nokttv',
                'time_params_tested': False,       # Will be determined at runtime
                'supports_time_params': None,      # To be discovered
                'collection_strategy': 'TBD'       # To be determined
            },
            'kttv': {
                'stations_url': STATIONS_API_BASE_URL_KTTV,
                'stats_url': STATS_API_BASE_URL_KTTV,
                'api_key': None,
                'type': 'kttv',
                'time_params_tested': True,        # Confirmed in code
                'supports_time_params': True,      # Confirmed
                'max_range_hours': 2,
                'collection_strategy': 'TIME_WINDOW'
            }
        }
        
        # Time windows for time-aware APIs
        self.time_windows = [
            {'start_hour': 5, 'end_hour': 7, 'name': 'morning'},
            {'start_hour': 12, 'end_hour': 14, 'name': 'midday'},  
            {'start_hour': 20, 'end_hour': 22, 'name': 'evening'}
        ]
        
        self.station_mapping = {}
        
        # Collections
        self.collections = {
            'historical_data': 'historical_realtime_data',
            'current_data': 'realtime_depth',
            'collection_logs': 'data_collection_logs',
            'backup': 'historical_backup',
            'collection_windows': 'collection_time_windows',
            'api_capabilities': 'api_capability_cache'  # Cache API test results
        }

    async def initialize_database(self) -> bool:
        """Initialize database with enhanced indexes"""
        try:
            self.client = AsyncIOMotorClient(self.mongo_uri)
            self.db = self.client[DATABASE_NAME]
            
            # Enhanced unique index for better deduplication
            await self.db[self.collections['historical_data']].create_index([
                ('station_id', 1),
                ('time_point', 1),
                ('api_type', 1),
                ('collection_window', 1)
            ], unique=True, background=True)
            
            # Collection windows tracking
            await self.db[self.collections['collection_windows']].create_index([
                ('api_type', 1),
                ('collection_date', 1),
                ('time_window', 1)
            ], unique=True, background=True)
            
            # API capabilities cache
            await self.db[self.collections['api_capabilities']].create_index([
                ('api_type', 1)
            ], unique=True, background=True)
            
            logging.info("✅ Enhanced database indexes created")
            return True
            
        except Exception as e:
            logging.error(f"❌ Database initialization failed: {e}")
            return False

    async def test_api_time_parameter_support(self, api_type: str) -> bool:
        """
        Test if an API supports time parameters
        Returns True if API accepts start_time/end_time, False otherwise
        """
        logging.info(f"🧪 Testing {api_type.upper()} API time parameter support...")
        
        # Check cache first
        cached = await self.db[self.collections['api_capabilities']].find_one({
            'api_type': api_type
        })
        
        if cached and 'supports_time_params' in cached:
            supports = cached['supports_time_params']
            logging.info(f"📋 Using cached result for {api_type}: supports_time_params = {supports}")
            return supports
        
        config = self.api_configs[api_type]
        url = config['stats_url']
        headers = {'x-api-key': config['api_key']} if config['api_key'] else {}
        
        # Test time parameters
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=1)
        
        params = {
            'start_time': start_time.strftime('%Y-%m-%d %H:%M:%S'),
            'end_time': end_time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # First try with time parameters
                response = await client.get(url, headers=headers, params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    # If we get valid data structure, API supports time params
                    if self._is_valid_stats_response(data):
                        supports = True
                        logging.info(f"✅ {api_type.upper()} API SUPPORTS time parameters")
                    else:
                        supports = False
                        logging.info(f"❌ {api_type.upper()} API does NOT support time parameters")
                else:
                    # If time params cause error, try without params
                    response_no_params = await client.get(url, headers=headers)
                    if response_no_params.status_code == 200:
                        supports = False
                        logging.info(f"❌ {api_type.upper()} API does NOT support time parameters (error with params)")
                    else:
                        supports = False
                        logging.warning(f"⚠️ {api_type.upper()} API failed both with and without params")
                
                # Cache result
                await self.db[self.collections['api_capabilities']].update_one(
                    {'api_type': api_type},
                    {
                        '$set': {
                            'api_type': api_type,
                            'supports_time_params': supports,
                            'tested_at': datetime.utcnow(),
                            'test_params': params
                        }
                    },
                    upsert=True
                )
                
                return supports
                
        except Exception as e:
            logging.error(f"❌ Error testing {api_type} time params: {e}")
            # Default to False if testing fails
            return False

    def _is_valid_stats_response(self, data) -> bool:
        """Check if response contains valid stats data structure"""
        if isinstance(data, dict) and data:
            # Check for typical stats structure
            return True
        elif isinstance(data, list) and data:
            return True
        return False

    async def discover_api_capabilities(self):
        """
        Discover actual capabilities of each API
        This sets the collection strategy for each API type
        """
        logging.info("🔍 Discovering API capabilities...")
        
        for api_type in ['nokttv', 'kttv']:
            config = self.api_configs[api_type]
            
            if not config['time_params_tested']:
                # Test time parameter support
                supports_time = await self.test_api_time_parameter_support(api_type)
                config['supports_time_params'] = supports_time
                config['time_params_tested'] = True
                
                # Set collection strategy based on capability
                if supports_time:
                    config['collection_strategy'] = 'TIME_WINDOW'
                    config['duplicate_risk'] = 'HIGH'
                    logging.info(f"📊 {api_type.upper()}: TIME_WINDOW strategy (supports time params)")
                else:
                    config['collection_strategy'] = 'CURRENT_DATA'
                    config['duplicate_risk'] = 'LOW'
                    logging.info(f"📊 {api_type.upper()}: CURRENT_DATA strategy (no time params)")
            else:
                logging.info(f"📋 {api_type.upper()}: Using pre-configured strategy: {config['collection_strategy']}")

    async def fetch_stations(self, api_type: str) -> List[Dict]:
        """Fetch stations - same as before"""
        try:
            config = self.api_configs[api_type]
            url = config['stations_url']
            headers = {'x-api-key': config['api_key']} if config['api_key'] else {}
            
            logging.info(f"📡 Fetching {api_type.upper()} stations...")
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    stations = []
                    if isinstance(data, list):
                        stations = data
                    elif isinstance(data, dict):
                        stations = data.get('data', data.get('stations', data.get('results', [])))
                    
                    if not isinstance(stations, list):
                        stations = []
                    
                    logging.info(f"✅ Fetched {len(stations)} {api_type.upper()} stations")
                    return stations
                else:
                    logging.warning(f"⚠️ {api_type.upper()} stations failed: {response.status_code}")
                    return []
                    
        except Exception as e:
            logging.error(f"❌ Error fetching {api_type} stations: {e}")
            return []

    async def fetch_current_data(self, api_type: str) -> List[Dict]:
        """
        Fetch current data (no time parameters)
        For APIs that don't support time filtering
        """
        try:
            config = self.api_configs[api_type]
            url = config['stats_url']
            headers = {'x-api-key': config['api_key']} if config['api_key'] else {}
            
            logging.info(f"📡 Fetching {api_type.upper()} current data (no time params)...")
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    stats = []
                    if isinstance(data, list):
                        stats = data
                    elif isinstance(data, dict):
                        stats = data.get('data', data.get('stats', data.get('results', [])))
                    
                    if not isinstance(stats, list):
                        stats = []
                    
                    logging.info(f"✅ {api_type.upper()} current data: {len(stats)} records")
                    return stats
                else:
                    logging.warning(f"⚠️ {api_type.upper()} current data failed: {response.status_code}")
                    return []
                    
        except Exception as e:
            logging.error(f"❌ {api_type.upper()} current data error: {e}")
            return []

    async def fetch_time_window_data(self, api_type: str, start_time: datetime, end_time: datetime) -> List[Dict]:
        """
        Fetch data for specific time window
        For APIs that support time filtering
        """
        try:
            config = self.api_configs[api_type]
            url = config['stats_url']
            headers = {'x-api-key': config['api_key']} if config['api_key'] else {}
            
            # Validate time range if API has limits
            if 'max_range_hours' in config:
                duration = (end_time - start_time).total_seconds() / 3600
                if duration > config['max_range_hours']:
                    logging.warning(f"⚠️ Time range too wide: {duration:.1f}h > {config['max_range_hours']}h")
                    return []
            
            params = {
                'start_time': start_time.strftime('%Y-%m-%d %H:%M:%S'),
                'end_time': end_time.strftime('%Y-%m-%d %H:%M:%S')
            }
            
            logging.info(f"📡 Fetching {api_type.upper()} time window: {params['start_time']} - {params['end_time']}")
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, headers=headers, params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    stats = []
                    if isinstance(data, list):
                        stats = data
                    elif isinstance(data, dict):
                        stats = data.get('data', data.get('stats', data.get('results', [])))
                    
                    if not isinstance(stats, list):
                        stats = []
                    
                    logging.info(f"✅ {api_type.upper()} time window: {len(stats)} records")
                    return stats
                else:
                    logging.warning(f"⚠️ {api_type.upper()} time window failed: {response.status_code}")
                    return []
                    
        except Exception as e:
            logging.error(f"❌ {api_type.upper()} time window error: {e}")
            return []

    def create_station_mapping(self, stations: List[Dict], api_type: str):
        """Create station mapping - same as before"""
        mapped_count = 0
        
        for station in stations:
            station_id = None
            station_code = None
            
            for id_key in ['code', 'station_id', 'id', 'stationId']:
                if id_key in station and station[id_key]:
                    station_id = str(station[id_key])
                    station_code = station_id
                    break
            
            lat = station.get('latitude', station.get('lat', None))
            lon = station.get('longitude', station.get('lon', station.get('lng', None)))
            name = station.get('name', station.get('station_name', f'Trạm {station_code}' if station_code else 'Unknown'))
            
            if station_id and lat is not None and lon is not None:
                self.station_mapping[station_id] = {
                    'code': station_code,
                    'name': name,
                    'latitude': float(lat),
                    'longitude': float(lon),
                    'api_type': api_type,
                    'last_updated': datetime.utcnow()
                }
                mapped_count += 1
        
        logging.info(f"✅ Mapped {mapped_count}/{len(stations)} {api_type.upper()} stations")

    async def process_data_with_window_tracking(
        self, 
        stats: List[Dict], 
        api_type: str, 
        target_date: date,
        time_window: Optional[str] = None
    ) -> List[Dict]:
        """Process data with time window tracking"""
        documents = []
        processed_count = 0
        skipped_count = 0
        
        for stat in stats:
            station_id = None
            for id_key in ['station_id', 'code', 'stationId', 'id']:
                if id_key in stat and stat[id_key]:
                    station_id = str(stat[id_key])
                    break
            
            if not station_id or station_id not in self.station_mapping:
                skipped_count += 1
                continue
            
            station_info = self.station_mapping[station_id]
            values = stat.get('value', stat.get('values', stat.get('data', [])))
            if not isinstance(values, list):
                values = [values] if values else []
            
            for value in values:
                try:
                    time_point_str = value.get('time_point', value.get('timestamp', value.get('time', '')))
                    depth = value.get('depth', value.get('water_level', value.get('level', 0)))
                    
                    if time_point_str and depth is not None:
                        time_point = await self._parse_timestamp(time_point_str)
                        
                        if time_point:
                            document = {
                                'station_id': station_id,
                                'code': station_info['code'],
                                'name': station_info['name'],
                                'latitude': station_info['latitude'],
                                'longitude': station_info['longitude'],
                                'api_type': api_type,
                                'time_point': time_point,
                                'depth': float(depth),
                                'collection_date': target_date,
                                'collection_window': time_window or 'default',
                                'collection_strategy': self.api_configs[api_type]['collection_strategy'],
                                'created_at': datetime.utcnow()
                            }
                            documents.append(document)
                            processed_count += 1
                            
                except Exception as e:
                    logging.warning(f"⚠️ Error processing measurement: {e}")
                    continue
        
        logging.info(f"📊 Processed {processed_count} measurements, skipped {skipped_count} from {api_type.upper()}")
        return documents

    async def _parse_timestamp(self, timestamp_str: str) -> Optional[datetime]:
        """Parse timestamp - same as before"""
        try:
            if 'T' in str(timestamp_str):
                return datetime.fromisoformat(str(timestamp_str).replace('Z', '+00:00'))
            else:
                formats = ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M', '%Y/%m/%d %H:%M:%S']
                for fmt in formats:
                    try:
                        return datetime.strptime(str(timestamp_str), fmt)
                    except ValueError:
                        continue
        except Exception:
            pass
        return None

    async def collect_api_data(self, api_type: str, target_date: date) -> List[Dict]:
        """
        Collect data using appropriate strategy based on API capabilities
        """
        config = self.api_configs[api_type]
        strategy = config['collection_strategy']
        
        logging.info(f"📡 Collecting {api_type.upper()} data using {strategy} strategy")
        
        if strategy == 'CURRENT_DATA':
            # API doesn't support time params - collect current data only
            stats = await self.fetch_current_data(api_type)
            if not stats:
                return []
            
            documents = await self.process_data_with_window_tracking(
                stats, api_type, target_date, 'current'
            )
            return documents
            
        elif strategy == 'TIME_WINDOW':
            # API supports time params - collect multiple time windows
            all_documents = []
            
            for window_config in self.time_windows:
                window_name = window_config['name']
                
                # Create time window
                start_time = datetime.combine(target_date, datetime.min.time()).replace(
                    hour=window_config['start_hour'], minute=0, second=0
                )
                end_time = datetime.combine(target_date, datetime.min.time()).replace(
                    hour=window_config['end_hour'], minute=0, second=0
                )
                
                # Fetch data for this window
                stats = await self.fetch_time_window_data(api_type, start_time, end_time)
                if not stats:
                    continue
                
                # Process data with window tracking
                documents = await self.process_data_with_window_tracking(
                    stats, api_type, target_date, window_name
                )
                
                all_documents.extend(documents)
            
            return all_documents
        
        else:
            logging.error(f"❌ Unknown collection strategy: {strategy}")
            return []

    async def enhanced_upsert_data(self, documents: List[Dict]) -> bool:
        """Enhanced upsert with better duplicate detection"""
        if not documents:
            return True
        
        try:
            operations = []
            for doc in documents:
                filter_query = {
                    'station_id': doc['station_id'],
                    'time_point': doc['time_point'],
                    'api_type': doc['api_type'],
                    'collection_window': doc['collection_window']
                }
                
                update_doc = {'$set': doc}
                operations.append(UpdateOne(filter_query, update_doc, upsert=True))
            
            result = await self.db[self.collections['historical_data']].bulk_write(
                operations, ordered=False
            )
            
            logging.info(f"✅ Enhanced upsert: {result.upserted_count} new, {result.modified_count} updated")
            return True
            
        except Exception as e:
            logging.error(f"❌ Enhanced upsert failed: {e}")
            return False

    async def run_corrected_daily_collection(self, target_date: Optional[date] = None) -> bool:
        """
        Main collection method with adaptive API handling
        """
        if target_date is None:
            target_date = date.today()
        
        start_time = datetime.utcnow()
        logging.info(f"🚀 Starting CORRECTED daily collection for {target_date}")
        
        try:
            if not await self.initialize_database():
                return False
            
            # 1. Discover API capabilities
            await self.discover_api_capabilities()
            
            all_documents = []
            collection_details = {'total_records': 0}
            
            # 2. Collect stations for both APIs
            for api_type in ['nokttv', 'kttv']:
                stations = await self.fetch_stations(api_type)
                if stations:
                    self.create_station_mapping(stations, api_type)
            
            # 3. Adaptive data collection for each API
            for api_type in ['nokttv', 'kttv']:
                config = self.api_configs[api_type]
                logging.info(f"📊 {api_type.upper()} Strategy: {config['collection_strategy']} (Time Params: {config.get('supports_time_params', 'Unknown')})")
                
                documents = await self.collect_api_data(api_type, target_date)
                all_documents.extend(documents)
                collection_details[f'{api_type}_count'] = len(documents)
                collection_details[f'{api_type}_strategy'] = config['collection_strategy']
            
            # 4. Store data
            if all_documents:
                collection_details['total_records'] = len(all_documents)
                
                # Enhanced upsert
                historical_success = await self.enhanced_upsert_data(all_documents)
                
                # Update current data (for UI compatibility)
                current_success = await self._update_current_data(all_documents)
                
                if historical_success and current_success:
                    status = 'success'
                else:
                    status = 'partial'
            else:
                status = 'failed'
                collection_details['error'] = 'No data collected'
            
            # 5. Log results
            collection_details['execution_time'] = (datetime.utcnow() - start_time).total_seconds()
            await self._log_collection_result(target_date, status, collection_details)
            
            # 6. Summary
            logging.info(f"✅ CORRECTED daily collection: {status} - {len(all_documents)} records")
            logging.info("📊 Collection Summary:")
            for api_type in ['nokttv', 'kttv']:
                strategy = collection_details.get(f'{api_type}_strategy', 'Unknown')
                count = collection_details.get(f'{api_type}_count', 0)
                supports_time = self.api_configs[api_type].get('supports_time_params', 'Unknown')
                logging.info(f"   {api_type.upper()}: {count} records via {strategy} (time_params: {supports_time})")
            
            return status in ['success', 'partial']
            
        except Exception as e:
            logging.error(f"❌ CORRECTED daily collection failed: {e}")
            return False
            
        finally:
            if self.client:
                self.client.close()

    async def _update_current_data(self, documents: List[Dict]) -> bool:
        """Update current data collection (for UI compatibility)"""
        try:
            await self.db[self.collections['current_data']].delete_many({})
            
            if documents:
                batch_size = 1000
                for i in range(0, len(documents), batch_size):
                    batch = documents[i:i + batch_size]
                    await self.db[self.collections['current_data']].insert_many(batch)
            
            return True
        except Exception as e:
            logging.error(f"❌ Current data update failed: {e}")
            return False

    async def _log_collection_result(self, target_date: date, status: str, details: Dict):
        """Log collection results"""
        try:
            log_doc = {
                'collection_date': target_date,
                'execution_time': datetime.utcnow(),
                'status': status,
                'details': details,
                'strategy_used': 'ADAPTIVE_API_AWARE',
                'nokttv_strategy': details.get('nokttv_strategy', 'Unknown'),
                'kttv_strategy': details.get('kttv_strategy', 'Unknown'),
                'api_capabilities_discovered': {
                    api_type: {
                        'supports_time_params': config.get('supports_time_params'),
                        'collection_strategy': config.get('collection_strategy')
                    }
                    for api_type, config in self.api_configs.items()
                }
            }
            
            await self.db[self.collections['collection_logs']].insert_one(log_doc)
            
        except Exception as e:
            logging.error(f"❌ Logging failed: {e}")

if __name__ == "__main__":
    async def main():
        """Test corrected collector"""
        logging.info("🚀 Testing CORRECTED Daily Data Collector")
        
        collector = CorrectedDailyDataCollector()
        success = await collector.run_corrected_daily_collection()
        
        print(f"\nCORRECTED Collection Result: {'SUCCESS' if success else 'FAILED'}")
        
    asyncio.run(main())