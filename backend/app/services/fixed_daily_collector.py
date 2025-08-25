#!/usr/bin/env python3
"""
FIXED DAILY DATA COLLECTOR - Xử lý đúng API behavior để tránh trùng lặp

FIXES ĐÃ ÁP DỤNG:
1. API-specific collection strategies
2. Time-window based collection cho KTTV API  
3. Current-data only collection cho NOKTTV API
4. Enhanced deduplication logic
5. Non-overlapping time windows
6. Proper backfill mechanism

API BEHAVIOR UNDERSTANDING:
- KTTV: start_time/end_time params, max 1-2h range, DUPLICATE RISK HIGH
- NOKTTV: no time params, current data only, DUPLICATE RISK LOW
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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
    handlers=[
        logging.FileHandler('fixed_daily_collector.log'),
        logging.StreamHandler()
    ]
)

class FixedDailyDataCollector:
    """
    FIXED DATA COLLECTOR với API-specific handling
    
    Key Improvements:
    1. Separate strategies for KTTV vs NOKTTV APIs
    2. Time-window collection cho KTTV to avoid duplicates
    3. Enhanced deduplication with time-aware logic
    4. Proper backfill for missed time windows
    """
    
    def __init__(self):
        """Initialize với improved configuration"""
        self.mongo_uri = MONGODB_URI
        self.client = None
        self.db = None
        
        # API configurations with behavior flags
        self.api_configs = {
            'nokttv': {
                'stations_url': STATIONS_API_BASE_URL_NOKTTV,
                'stats_url': STATS_API_BASE_URL_NOKTTV,
                'api_key': API_KEY,
                'type': 'nokttv',
                'uses_time_params': False,      # NOKTTV không dùng time params
                'duplicate_risk': 'LOW',
                'collection_strategy': 'CURRENT_DATA'
            },
            'kttv': {
                'stations_url': STATIONS_API_BASE_URL_KTTV,
                'stats_url': STATS_API_BASE_URL_KTTV,
                'api_key': None,
                'type': 'kttv',
                'uses_time_params': True,       # KTTV dùng start_time/end_time
                'duplicate_risk': 'HIGH',
                'max_range_hours': 2,
                'collection_strategy': 'TIME_WINDOW'
            }
        }
        
        # Time windows for KTTV API (non-overlapping)
        self.kttv_time_windows = [
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
            'collection_windows': 'collection_time_windows'  # Track collected windows
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
                ('collection_window', 1)  # Add collection window tracking
            ], unique=True, background=True)
            
            # Index để track collected time windows
            await self.db[self.collections['collection_windows']].create_index([
                ('api_type', 1),
                ('collection_date', 1),
                ('time_window', 1)
            ], unique=True, background=True)
            
            logging.info("✅ Enhanced database indexes created")
            return True
            
        except Exception as e:
            logging.error(f"❌ Database initialization failed: {e}")
            return False

    async def fetch_stations(self, api_type: str) -> List[Dict]:
        """Fetch stations - same as before"""
        try:
            config = self.api_configs[api_type]
            url = config['stations_url']
            headers = {}
            
            if api_type == 'nokttv' and config['api_key']:
                headers['x-api-key'] = config['api_key']
            
            logging.info(f"Fetching {api_type.upper()} stations...")
            
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

    async def fetch_nokttv_current_data(self) -> List[Dict]:
        """
        Fetch NOKTTV current data (no time parameters)
        Strategy: CURRENT_DATA - chỉ lấy dữ liệu hiện tại
        """
        try:
            config = self.api_configs['nokttv']
            url = config['stats_url']
            headers = {'x-api-key': config['api_key']} if config['api_key'] else {}
            
            logging.info("📡 Fetching NOKTTV current data (no time params)...")
            
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
                    
                    logging.info(f"✅ NOKTTV current data: {len(stats)} records")
                    return stats
                else:
                    logging.warning(f"⚠️ NOKTTV current data failed: {response.status_code}")
                    return []
                    
        except Exception as e:
            logging.error(f"❌ NOKTTV current data error: {e}")
            return []

    async def fetch_kttv_time_window(self, start_time: datetime, end_time: datetime) -> List[Dict]:
        """
        Fetch KTTV data for specific time window
        Strategy: TIME_WINDOW - sử dụng start_time/end_time parameters
        """
        try:
            config = self.api_configs['kttv']
            url = config['stats_url']
            
            # Validate time range (max 2 hours)
            duration = (end_time - start_time).total_seconds() / 3600
            if duration > config['max_range_hours']:
                logging.warning(f"⚠️ Time range too wide: {duration:.1f}h > {config['max_range_hours']}h")
                return []
            
            params = {
                'start_time': start_time.strftime('%Y-%m-%d %H:%M:%S'),
                'end_time': end_time.strftime('%Y-%m-%d %H:%M:%S')
            }
            
            logging.info(f"📡 Fetching KTTV time window: {params['start_time']} - {params['end_time']}")
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    stats = []
                    if isinstance(data, list):
                        stats = data
                    elif isinstance(data, dict):
                        stats = data.get('data', data.get('stats', data.get('results', [])))
                    
                    if not isinstance(stats, list):
                        stats = []
                    
                    logging.info(f"✅ KTTV time window: {len(stats)} records")
                    return stats
                else:
                    logging.warning(f"⚠️ KTTV time window failed: {response.status_code} - {response.text[:200]}")
                    return []
                    
        except Exception as e:
            logging.error(f"❌ KTTV time window error: {e}")
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
        """
        Process data với time window tracking để tránh duplicate
        """
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
                            # Enhanced document với window tracking
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
                                'collection_window': time_window or 'default',  # Track collection window
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

    async def check_collection_window_completed(
        self, 
        api_type: str, 
        target_date: date, 
        time_window: str
    ) -> bool:
        """
        Check xem time window đã được collect chưa
        Tránh collect duplicate data cho cùng time window
        """
        try:
            existing = await self.db[self.collections['collection_windows']].find_one({
                'api_type': api_type,
                'collection_date': target_date,
                'time_window': time_window
            })
            
            return existing is not None
            
        except Exception as e:
            logging.warning(f"⚠️ Error checking collection window: {e}")
            return False

    async def mark_collection_window_completed(
        self, 
        api_type: str, 
        target_date: date, 
        time_window: str,
        records_collected: int
    ):
        """
        Mark time window as completed để tránh re-collection
        """
        try:
            window_doc = {
                'api_type': api_type,
                'collection_date': target_date,
                'time_window': time_window,
                'completed_at': datetime.utcnow(),
                'records_collected': records_collected
            }
            
            await self.db[self.collections['collection_windows']].update_one(
                {
                    'api_type': api_type,
                    'collection_date': target_date,
                    'time_window': time_window
                },
                {'$set': window_doc},
                upsert=True
            )
            
            logging.info(f"✅ Marked {api_type}.{time_window} completed: {records_collected} records")
            
        except Exception as e:
            logging.error(f"❌ Error marking collection window: {e}")

    async def collect_nokttv_data(self, target_date: date) -> List[Dict]:
        """
        NOKTTV collection strategy: CURRENT_DATA only
        """
        logging.info("📡 NOKTTV Collection Strategy: CURRENT_DATA")
        
        # Check if already collected today
        window_completed = await self.check_collection_window_completed('nokttv', target_date, 'current')
        if window_completed:
            logging.info("✅ NOKTTV current data already collected today, skipping")
            return []
        
        # Fetch current data
        stats = await self.fetch_nokttv_current_data()
        if not stats:
            return []
        
        # Process data
        documents = await self.process_data_with_window_tracking(
            stats, 'nokttv', target_date, 'current'
        )
        
        # Mark collection completed
        await self.mark_collection_window_completed('nokttv', target_date, 'current', len(documents))
        
        return documents

    async def collect_kttv_data(self, target_date: date) -> List[Dict]:
        """
        KTTV collection strategy: TIME_WINDOW based
        """
        logging.info("📡 KTTV Collection Strategy: TIME_WINDOW")
        
        all_documents = []
        
        for window_config in self.kttv_time_windows:
            window_name = window_config['name']
            
            # Check if window already collected
            window_completed = await self.check_collection_window_completed(
                'kttv', target_date, window_name
            )
            if window_completed:
                logging.info(f"✅ KTTV {window_name} window already collected, skipping")
                continue
            
            # Create time window
            start_time = datetime.combine(target_date, datetime.min.time()).replace(
                hour=window_config['start_hour'], minute=0, second=0
            )
            end_time = datetime.combine(target_date, datetime.min.time()).replace(
                hour=window_config['end_hour'], minute=0, second=0
            )
            
            # Fetch data for this window
            logging.info(f"📅 Collecting KTTV {window_name} window: {start_time.strftime('%H:%M')}-{end_time.strftime('%H:%M')}")
            
            stats = await self.fetch_kttv_time_window(start_time, end_time)
            if not stats:
                await self.mark_collection_window_completed('kttv', target_date, window_name, 0)
                continue
            
            # Process data với window tracking
            documents = await self.process_data_with_window_tracking(
                stats, 'kttv', target_date, window_name
            )
            
            all_documents.extend(documents)
            
            # Mark window completed
            await self.mark_collection_window_completed('kttv', target_date, window_name, len(documents))
        
        return all_documents

    async def enhanced_upsert_data(self, documents: List[Dict]) -> bool:
        """
        Enhanced upsert với better duplicate detection
        """
        if not documents:
            return True
        
        try:
            operations = []
            for doc in documents:
                # Enhanced filter để tránh duplicate
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

    async def run_fixed_daily_collection(self, target_date: Optional[date] = None) -> bool:
        """
        Main collection method với API-specific strategies
        """
        if target_date is None:
            target_date = date.today()
        
        start_time = datetime.utcnow()
        logging.info(f"🚀 Starting FIXED daily collection for {target_date}")
        
        try:
            if not await self.initialize_database():
                return False
            
            all_documents = []
            collection_details = {'total_records': 0}
            
            # 1. Collect stations for both APIs
            for api_type in ['nokttv', 'kttv']:
                stations = await self.fetch_stations(api_type)
                if stations:
                    self.create_station_mapping(stations, api_type)
            
            # 2. API-specific data collection
            # NOKTTV: Current data strategy
            nokttv_documents = await self.collect_nokttv_data(target_date)
            all_documents.extend(nokttv_documents)
            collection_details['nokttv_count'] = len(nokttv_documents)
            
            # KTTV: Time window strategy  
            kttv_documents = await self.collect_kttv_data(target_date)
            all_documents.extend(kttv_documents)
            collection_details['kttv_count'] = len(kttv_documents)
            
            # 3. Enhanced data storage
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
            
            # 4. Log results
            collection_details['execution_time'] = (datetime.utcnow() - start_time).total_seconds()
            await self._log_collection_result(target_date, status, collection_details)
            
            logging.info(f"✅ FIXED daily collection: {status} - {len(all_documents)} records")
            
            # 5. Summary by API strategy
            logging.info("📊 Collection Summary by Strategy:")
            logging.info(f"   NOKTTV (CURRENT_DATA): {collection_details['nokttv_count']} records")
            logging.info(f"   KTTV (TIME_WINDOW): {collection_details['kttv_count']} records")
            
            return status in ['success', 'partial']
            
        except Exception as e:
            logging.error(f"❌ FIXED daily collection failed: {e}")
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
                'strategy_used': 'API_SPECIFIC_FIXED',
                'nokttv_strategy': 'CURRENT_DATA',
                'kttv_strategy': 'TIME_WINDOW'
            }
            
            await self.db[self.collections['collection_logs']].insert_one(log_doc)
            
        except Exception as e:
            logging.error(f"❌ Logging failed: {e}")

if __name__ == "__main__":
    async def main():
        """Test fixed collector"""
        collector = FixedDailyDataCollector()
        success = await collector.run_fixed_daily_collection()
        
        print(f"Fixed collection result: {'SUCCESS' if success else 'FAILED'}")
        
    asyncio.run(main())