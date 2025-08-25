#!/usr/bin/env python3
"""
FINAL DAILY DATA COLLECTOR - Với hiểu biết chính thức về APIs

CONFIRMED API BEHAVIOR:
1. NOKTTV API: https://openapi.vrain.vn/v1/stations/stats?start_time=X&end_time=Y
2. KTTV API: start_time/end_time params với max 1-2h range
3. CẢ 2 APIs ĐỀU CÓ DUPLICATE RISK khi gọi cùng time range nhiều lần

STRATEGY:
- Time-window collection cho cả 2 APIs
- Non-overlapping windows để tránh duplicate  
- Enhanced deduplication với time-window tracking
- Proper time parameter formatting
"""

import asyncio
import httpx
import logging
import sys
import os
from datetime import datetime, timedelta, date
from typing import List, Dict, Optional
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import UpdateOne
from pymongo.errors import BulkWriteError
from urllib.parse import quote

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from config import *

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
    handlers=[
        logging.FileHandler('final_daily_collector.log'),
        logging.StreamHandler()
    ]
)

class FinalDailyDataCollector:
    """
    FINAL DATA COLLECTOR với confirmed API understanding
    
    CONFIRMED:
    - NOKTTV: Supports start_time/end_time parameters
    - KTTV: Supports start_time/end_time parameters (max 1-2h)
    - BOTH have DUPLICATE RISK → Need time-window strategy
    """
    
    def __init__(self):
        """Initialize with confirmed API configurations"""
        self.mongo_uri = MONGODB_URI
        self.client = None
        self.db = None
        
        # CONFIRMED API configurations
        self.api_configs = {
            'nokttv': {
                'stations_url': STATIONS_API_BASE_URL_NOKTTV,
                'stats_url': STATS_API_BASE_URL_NOKTTV,
                'api_key': API_KEY,
                'type': 'nokttv',
                'supports_time_params': True,           # CONFIRMED
                'max_range_hours': 24,                  # NOKTTV seems more flexible
                'collection_strategy': 'TIME_WINDOW',
                'duplicate_risk': 'HIGH'
            },
            'kttv': {
                'stations_url': STATIONS_API_BASE_URL_KTTV,
                'stats_url': STATS_API_BASE_URL_KTTV,
                'api_key': None,
                'type': 'kttv',
                'supports_time_params': True,           # CONFIRMED
                'max_range_hours': 2,                   # KTTV has stricter limits
                'collection_strategy': 'TIME_WINDOW',
                'duplicate_risk': 'HIGH'
            }
        }
        
        # Non-overlapping time windows for both APIs
        # Adjust for each API's capabilities
        self.time_windows = {
            'nokttv': [
                {'start_hour': 0, 'end_hour': 8, 'name': 'night'},      # 8h window
                {'start_hour': 8, 'end_hour': 16, 'name': 'day'},       # 8h window
                {'start_hour': 16, 'end_hour': 24, 'name': 'evening'}   # 8h window
            ],
            'kttv': [
                {'start_hour': 5, 'end_hour': 7, 'name': 'morning'},    # 2h window
                {'start_hour': 12, 'end_hour': 14, 'name': 'midday'},   # 2h window
                {'start_hour': 20, 'end_hour': 22, 'name': 'evening'}   # 2h window
            ]
        }
        
        self.station_mapping = {}
        
        # Collections
        self.collections = {
            'historical_data': 'historical_realtime_data',
            'current_data': 'realtime_depth',
            'collection_logs': 'data_collection_logs',
            'backup': 'historical_backup',
            'collection_windows': 'collection_time_windows'
        }

    async def initialize_database(self) -> bool:
        """Initialize database"""
        try:
            self.client = AsyncIOMotorClient(self.mongo_uri)
            self.db = self.client[DATABASE_NAME]
            
            # Enhanced unique index to prevent duplicates
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
            
            logging.info("✅ Database initialized")
            return True
            
        except Exception as e:
            logging.error(f"❌ Database initialization failed: {e}")
            return False

    async def fetch_stations(self, api_type: str) -> List[Dict]:
        """Fetch stations"""
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

    async def fetch_time_window_data(
        self, 
        api_type: str, 
        start_time: datetime, 
        end_time: datetime
    ) -> List[Dict]:
        """
        Fetch data for specific time window with confirmed API parameters
        """
        try:
            config = self.api_configs[api_type]
            url = config['stats_url']
            
            # Validate time range
            duration = (end_time - start_time).total_seconds() / 3600
            if duration > config['max_range_hours']:
                logging.warning(f"⚠️ {api_type.upper()}: Time range {duration:.1f}h exceeds max {config['max_range_hours']}h")
                return []
            
            # Format parameters according to confirmed API spec
            start_str = start_time.strftime('%Y-%m-%d %H:%M:%S')
            end_str = end_time.strftime('%Y-%m-%d %H:%M:%S')
            
            if api_type == 'nokttv':
                # NOKTTV confirmed format
                headers = {'x-api-key': config['api_key']} if config['api_key'] else {}
                params = {
                    'start_time': start_str,
                    'end_time': end_str
                }
            else:  # kttv
                # KTTV format
                headers = {'x-api-key': config['api_key']} if config['api_key'] else {}
                params = {
                    'start_time': start_str,
                    'end_time': end_str
                }
            
            logging.info(f"📡 {api_type.upper()} time window: {start_str} - {end_str}")
            
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
                    
                    logging.info(f"✅ {api_type.upper()}: {len(stats)} records for time window")
                    return stats
                else:
                    logging.warning(f"⚠️ {api_type.upper()}: Failed {response.status_code} - {response.text[:200]}")
                    return []
                    
        except Exception as e:
            logging.error(f"❌ {api_type.upper()} time window error: {e}")
            return []

    def create_station_mapping(self, stations: List[Dict], api_type: str):
        """Create station mapping"""
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
        time_window: str
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
                                'collection_window': time_window,
                                'created_at': datetime.utcnow()
                            }
                            documents.append(document)
                            processed_count += 1
                            
                except Exception as e:
                    logging.warning(f"⚠️ Error processing measurement: {e}")
                    continue
        
        logging.info(f"📊 {api_type.upper()}.{time_window}: {processed_count} processed, {skipped_count} skipped")
        return documents

    async def _parse_timestamp(self, timestamp_str: str) -> Optional[datetime]:
        """Parse timestamp"""
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

    async def check_window_completed(self, api_type: str, target_date: date, window_name: str) -> bool:
        """Check if time window was already collected"""
        try:
            existing = await self.db[self.collections['collection_windows']].find_one({
                'api_type': api_type,
                'collection_date': target_date,
                'time_window': window_name
            })
            return existing is not None
        except Exception as e:
            logging.warning(f"⚠️ Error checking window: {e}")
            return False

    async def mark_window_completed(
        self, 
        api_type: str, 
        target_date: date, 
        window_name: str, 
        records_count: int
    ):
        """Mark time window as completed"""
        try:
            await self.db[self.collections['collection_windows']].update_one(
                {
                    'api_type': api_type,
                    'collection_date': target_date,
                    'time_window': window_name
                },
                {
                    '$set': {
                        'api_type': api_type,
                        'collection_date': target_date,
                        'time_window': window_name,
                        'completed_at': datetime.utcnow(),
                        'records_collected': records_count
                    }
                },
                upsert=True
            )
            logging.info(f"✅ {api_type.upper()}.{window_name}: Marked completed ({records_count} records)")
        except Exception as e:
            logging.error(f"❌ Error marking window completed: {e}")

    async def collect_api_data(self, api_type: str, target_date: date) -> List[Dict]:
        """
        Collect data using time-window strategy for both APIs
        """
        logging.info(f"📡 {api_type.upper()}: Starting TIME_WINDOW collection")
        
        all_documents = []
        windows = self.time_windows[api_type]
        
        for window_config in windows:
            window_name = window_config['name']
            
            # Check if already collected
            if await self.check_window_completed(api_type, target_date, window_name):
                logging.info(f"✅ {api_type.upper()}.{window_name}: Already completed, skipping")
                continue
            
            # Create time window
            start_time = datetime.combine(target_date, datetime.min.time()).replace(
                hour=window_config['start_hour'], minute=0, second=0
            )
            
            if window_config['end_hour'] == 24:
                end_time = datetime.combine(target_date + timedelta(days=1), datetime.min.time())
            else:
                end_time = datetime.combine(target_date, datetime.min.time()).replace(
                    hour=window_config['end_hour'], minute=0, second=0
                )
            
            # Fetch data for window
            logging.info(f"📅 {api_type.upper()}.{window_name}: {start_time.strftime('%H:%M')}-{end_time.strftime('%H:%M')}")
            
            stats = await self.fetch_time_window_data(api_type, start_time, end_time)
            
            # Process data
            documents = await self.process_data_with_window_tracking(
                stats, api_type, target_date, window_name
            )
            
            all_documents.extend(documents)
            
            # Mark window completed
            await self.mark_window_completed(api_type, target_date, window_name, len(documents))
        
        logging.info(f"📊 {api_type.upper()}: Total {len(all_documents)} records from all windows")
        return all_documents

    async def enhanced_upsert_data(self, documents: List[Dict]) -> bool:
        """Enhanced upsert with duplicate prevention"""
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

    async def run_final_daily_collection(self, target_date: Optional[date] = None) -> bool:
        """
        Main collection method with confirmed API understanding
        """
        if target_date is None:
            target_date = date.today()
        
        start_time = datetime.utcnow()
        logging.info(f"🚀 Starting FINAL daily collection for {target_date}")
        logging.info("📋 CONFIRMED: Both NOKTTV and KTTV support start_time/end_time parameters")
        
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
            
            # 2. Time-window collection for both APIs
            for api_type in ['nokttv', 'kttv']:
                config = self.api_configs[api_type]
                logging.info(f"📊 {api_type.upper()}: TIME_WINDOW strategy (max {config['max_range_hours']}h windows)")
                
                documents = await self.collect_api_data(api_type, target_date)
                all_documents.extend(documents)
                collection_details[f'{api_type}_count'] = len(documents)
                collection_details[f'{api_type}_windows'] = len(self.time_windows[api_type])
            
            # 3. Store data
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
            
            # 5. Final summary
            logging.info(f"✅ FINAL daily collection: {status} - {len(all_documents)} records")
            logging.info("📊 Time-Window Collection Summary:")
            for api_type in ['nokttv', 'kttv']:
                count = collection_details.get(f'{api_type}_count', 0)
                windows = collection_details.get(f'{api_type}_windows', 0)
                max_hours = self.api_configs[api_type]['max_range_hours']
                logging.info(f"   {api_type.upper()}: {count} records from {windows} windows (max {max_hours}h each)")
            
            return status in ['success', 'partial']
            
        except Exception as e:
            logging.error(f"❌ FINAL daily collection failed: {e}")
            return False
            
        finally:
            if self.client:
                self.client.close()

    async def _update_current_data(self, documents: List[Dict]) -> bool:
        """Update current data collection"""
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
                'strategy_used': 'TIME_WINDOW_BOTH_APIS',
                'api_confirmed_behavior': {
                    'nokttv': 'start_time/end_time parameters CONFIRMED',
                    'kttv': 'start_time/end_time parameters CONFIRMED'
                },
                'duplicate_prevention': 'Enhanced with collection_window tracking'
            }
            
            await self.db[self.collections['collection_logs']].insert_one(log_doc)
            
        except Exception as e:
            logging.error(f"❌ Logging failed: {e}")

if __name__ == "__main__":
    async def main():
        """Test final collector with confirmed API understanding"""
        logging.info("🚀 Testing FINAL Daily Data Collector")
        logging.info("📋 CONFIRMED: NOKTTV API supports start_time/end_time parameters")
        
        collector = FinalDailyDataCollector()
        success = await collector.run_final_daily_collection()
        
        result = "SUCCESS" if success else "FAILED"
        print(f"\n🎯 FINAL Collection Result: {result}")
        print("📊 Both APIs now use TIME_WINDOW strategy to prevent duplicates")
        
    asyncio.run(main())