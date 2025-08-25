#!/usr/bin/env python3
"""
DAILY DATA COLLECTOR SERVICE - Script chạy ngầm thu thập dữ liệu API hàng ngày

Chức năng chính:
- Thu thập dữ liệu từ các API theo ngày (vì API chỉ cung cấp dữ liệu ngày hiện tại)
- Tránh ghi đè dữ liệu và trùng lặp bản ghi
- Lưu trữ dữ liệu lịch sử để phục vụ phân tích tần suất
- Tự động chạy hàng ngày qua scheduler
- Log chi tiết để monitoring và debugging

Thiết kế:
- Sử dụng upsert operations thay vì delete_all + insert
- Tạo unique index để tránh duplicate
- Backup dữ liệu trước khi cập nhật  
- Graceful error handling và recovery
- Comprehensive logging cho audit trail
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
import json

# Add parent directory to path để import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from config import *

# Cấu hình logging chi tiết với timestamp và level
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
    handlers=[
        logging.FileHandler('daily_collector.log'),
        logging.StreamHandler()
    ]
)

class DailyDataCollector:
    """
    SERVICE THU THẬP DỮ LIỆU HÀNG NGÀY
    
    Thiết kế để tránh các vấn đề của hệ thống hiện tại:
    1. Không xóa toàn bộ dữ liệu (delete_many)
    2. Sử dụng upsert để tránh duplicate
    3. Giữ lại dữ liệu lịch sử cho phân tích tần suất
    4. Kiểm tra data integrity trước khi commit
    """
    
    def __init__(self):
        """Khởi tạo collector với cấu hình an toàn"""
        self.mongo_uri = MONGODB_URI
        self.client = None
        self.db = None
        
        # Cấu hình API endpoints
        self.api_configs = {
            'nokttv': {
                'stations_url': STATIONS_API_BASE_URL_NOKTTV,
                'stats_url': STATS_API_BASE_URL_NOKTTV,
                'api_key': API_KEY,
                'type': 'nokttv'
            },
            'kttv': {
                'stations_url': STATIONS_API_BASE_URL_KTTV,
                'stats_url': STATS_API_BASE_URL_KTTV,
                'api_key': None,
                'type': 'kttv'
            }
        }
        
        # Cache cho station mapping
        self.station_mapping = {}
        
        # Collection names
        self.collections = {
            'historical_data': 'historical_realtime_data',  # Dữ liệu lịch sử cho phân tích tần suất
            'current_data': 'realtime_depth',              # Dữ liệu hiện tại cho real-time display
            'collection_logs': 'data_collection_logs',     # Logs cho audit trail
            'backup': 'historical_backup'                  # Backup trước khi update
        }

    async def initialize_database(self) -> bool:
        """
        Khởi tạo kết nối database và tạo indexes cần thiết
        
        Returns:
            bool: True nếu kết nối thành công
        """
        try:
            if not self.mongo_uri:
                logging.error("❌ No MongoDB URI provided")
                return False
                
            self.client = AsyncIOMotorClient(self.mongo_uri)
            self.db = self.client[DATABASE_NAME]
            
            # Test connection
            await self.client.admin.command('ping')
            
            # Tạo unique indexes để tránh duplicate data
            await self._create_indexes()
            
            logging.info("✅ Database initialized successfully")
            return True
            
        except Exception as e:
            logging.error(f"❌ Database initialization failed: {e}")
            self.client = None
            self.db = None
            return False
    
    async def _create_indexes(self):
        """Tạo các indexes cần thiết để tránh duplicate và tối ưu query"""
        try:
            # Index cho historical_data: unique combination để tránh duplicate
            await self.db[self.collections['historical_data']].create_index([
                ('station_id', 1),
                ('time_point', 1),
                ('api_type', 1)
            ], unique=True, background=True)
            
            # Index cho current_data (giữ nguyên structure hiện tại)
            await self.db[self.collections['current_data']].create_index([
                ('station_id', 1),
                ('time_point', -1)
            ], background=True)
            
            # Index cho logs
            await self.db[self.collections['collection_logs']].create_index([
                ('collection_date', -1),
                ('status', 1)
            ], background=True)
            
            logging.info("✅ Database indexes created successfully")
            
        except Exception as e:
            logging.warning(f"⚠️ Index creation warning (may already exist): {e}")

    async def fetch_stations(self, api_type: str) -> List[Dict]:
        """
        Fetch stations từ API với proper error handling
        
        Args:
            api_type: 'nokttv' hoặc 'kttv'
            
        Returns:
            List[Dict]: Danh sách stations
        """
        try:
            config = self.api_configs[api_type]
            url = config['stations_url']
            headers = {}
            
            if api_type == 'nokttv' and config['api_key']:
                headers['x-api-key'] = config['api_key']
            
            logging.info(f"🔍 Fetching {api_type.upper()} stations from {url}")
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Handle different response formats
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
                    logging.warning(f"⚠️ {api_type.upper()} stations API failed: {response.status_code}")
                    return []
                    
        except Exception as e:
            logging.error(f"❌ Error fetching {api_type} stations: {e}")
            return []

    async def fetch_daily_stats(self, api_type: str) -> List[Dict]:
        """
        Fetch daily stats từ API
        
        Args:
            api_type: 'nokttv' hoặc 'kttv'
            
        Returns:
            List[Dict]: Dữ liệu stats của ngày hiện tại
        """
        try:
            config = self.api_configs[api_type]
            url = config['stats_url']
            headers = {}
            
            if api_type == 'nokttv' and config['api_key']:
                headers['x-api-key'] = config['api_key']
            
            logging.info(f"📥 Fetching {api_type.upper()} daily stats from {url}")
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Handle different response formats
                    stats = []
                    if isinstance(data, list):
                        stats = data
                    elif isinstance(data, dict):
                        stats = data.get('data', data.get('stats', data.get('results', [])))
                    
                    if not isinstance(stats, list):
                        stats = []
                    
                    logging.info(f"✅ Fetched {len(stats)} {api_type.upper()} daily stats")
                    return stats
                    
                else:
                    logging.warning(f"⚠️ {api_type.upper()} stats API failed: {response.status_code}")
                    return []
                    
        except Exception as e:
            logging.error(f"❌ Error fetching {api_type} daily stats: {e}")
            return []

    def create_station_mapping(self, stations: List[Dict], api_type: str):
        """
        Tạo mapping giữa station ID và thông tin station
        
        Args:
            stations: Danh sách stations từ API
            api_type: Type của API
        """
        mapped_count = 0
        
        for station in stations:
            # Handle different station ID key names
            station_id = None
            station_code = None
            
            for id_key in ['code', 'uuid', 'station_id', 'id', 'stationId']:
                if id_key in station and station[id_key]:
                    station_id = str(station[id_key])
                    station_code = station.get('code', station_id)  # Prefer 'code' for station_code
                    break
            
            # Extract coordinates và name
            lat = station.get('latitude', station.get('lat', None))
            lon = station.get('longitude', station.get('lon', station.get('lng', None)))
            name = station.get('name', station.get('station_name', f'Trạm {station_code}' if station_code else 'Unknown'))
            
            if station_id and lat is not None and lon is not None:
                mapping_entry = {
                    'code': station_code,
                    'name': name,
                    'latitude': float(lat),
                    'longitude': float(lon),
                    'api_type': api_type,
                    'last_updated': datetime.utcnow()
                }
                
                self.station_mapping[station_id] = mapping_entry
                mapped_count += 1
        
        logging.info(f"✅ Mapped {mapped_count}/{len(stations)} {api_type.upper()} stations")

    async def process_daily_data(self, stats: List[Dict], api_type: str, target_date: date) -> List[Dict]:
        """
        Xử lý dữ liệu daily và chuẩn bị cho database update
        
        Args:
            stats: Raw data từ API
            api_type: Type của API
            target_date: Ngày thu thập dữ liệu
            
        Returns:
            List[Dict]: Documents ready để insert vào database
        """
        documents = []
        processed_count = 0
        skipped_count = 0
        
        for stat in stats:
            # Extract station ID
            station_id = None
            for id_key in ['station_id', 'code', 'uuid', 'stationId', 'id']:
                if id_key in stat and stat[id_key]:
                    station_id = str(stat[id_key])
                    break
            
            if not station_id:
                skipped_count += 1
                continue
            
            # Check station mapping
            station_info = self.station_mapping.get(station_id)
            if not station_info:
                skipped_count += 1
                continue
            
            # Process measurements
            values = stat.get('value', stat.get('values', stat.get('data', [])))
            if not isinstance(values, list):
                values = [values] if values else []
            
            for value in values:
                try:
                    # Parse timestamp
                    time_point_str = value.get('time_point', value.get('timestamp', value.get('time', '')))
                    depth = value.get('depth', value.get('water_level', value.get('level', 0)))
                    
                    if time_point_str and depth is not None:
                        time_point = await self._parse_timestamp(time_point_str)
                        
                        if time_point and time_point.date() == target_date:
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
        """
        Parse timestamp string với multiple format support
        
        Args:
            timestamp_str: String timestamp từ API
            
        Returns:
            datetime object hoặc None nếu parsing failed
        """
        try:
            if 'T' in str(timestamp_str):
                return datetime.fromisoformat(str(timestamp_str).replace('Z', '+00:00'))
            else:
                # Try multiple formats
                formats = ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M', '%Y/%m/%d %H:%M:%S']
                for fmt in formats:
                    try:
                        return datetime.strptime(str(timestamp_str), fmt)
                    except ValueError:
                        continue
        except Exception:
            pass
        
        return None

    async def backup_existing_data(self, target_date: date) -> bool:
        """
        Backup dữ liệu hiện có trước khi update (safety measure)
        
        Args:
            target_date: Ngày cần backup
            
        Returns:
            bool: True nếu backup thành công
        """
        try:
            # Query dữ liệu của ngày target
            existing_data = await self.db[self.collections['historical_data']].find({
                'collection_date': target_date
            }).to_list(None)
            
            if existing_data:
                # Create backup document
                backup_doc = {
                    'backup_date': datetime.utcnow(),
                    'target_date': target_date,
                    'data_count': len(existing_data),
                    'data': existing_data
                }
                
                await self.db[self.collections['backup']].insert_one(backup_doc)
                logging.info(f"✅ Backed up {len(existing_data)} records for {target_date}")
            
            return True
            
        except Exception as e:
            logging.error(f"❌ Backup failed: {e}")
            return False

    async def upsert_historical_data(self, documents: List[Dict]) -> bool:
        """
        Upsert dữ liệu vào historical collection với deduplication
        
        Args:
            documents: Danh sách documents để upsert
            
        Returns:
            bool: True nếu thành công
        """
        if not documents:
            logging.warning("⚠️ No documents to upsert")
            return True
        
        try:
            # Prepare upsert operations
            operations = []
            for doc in documents:
                filter_query = {
                    'station_id': doc['station_id'],
                    'time_point': doc['time_point'],
                    'api_type': doc['api_type']
                }
                
                update_doc = {'$set': doc}
                operations.append(UpdateOne(filter_query, update_doc, upsert=True))
            
            # Execute bulk upsert
            result = await self.db[self.collections['historical_data']].bulk_write(
                operations, 
                ordered=False
            )
            
            logging.info(f"✅ Upserted: {result.upserted_count} new, {result.modified_count} updated")
            return True
            
        except BulkWriteError as e:
            logging.error(f"❌ Bulk write error: {e.details}")
            return False
        except Exception as e:
            logging.error(f"❌ Upsert failed: {e}")
            return False

    async def update_current_data(self, documents: List[Dict]) -> bool:
        """
        Update current data collection (giữ nguyên behavior hiện tại cho real-time display)
        
        Args:
            documents: Documents để update
            
        Returns:
            bool: True nếu thành công
        """
        if not documents:
            return True
        
        try:
            # Clear và insert (giữ nguyên logic hiện tại)
            await self.db[self.collections['current_data']].delete_many({})
            
            # Insert new data
            batch_size = 1000
            for i in range(0, len(documents), batch_size):
                batch = documents[i:i + batch_size]
                await self.db[self.collections['current_data']].insert_many(batch)
            
            logging.info(f"✅ Updated current data: {len(documents)} records")
            return True
            
        except Exception as e:
            logging.error(f"❌ Current data update failed: {e}")
            return False

    async def log_collection_result(self, target_date: date, status: str, details: Dict):
        """
        Ghi log kết quả collection để audit và monitoring
        
        Args:
            target_date: Ngày collection
            status: 'success', 'partial', 'failed'
            details: Chi tiết về kết quả
        """
        try:
            log_doc = {
                'collection_date': target_date.isoformat() if isinstance(target_date, date) else target_date,
                'execution_time': datetime.utcnow(),
                'status': status,
                'details': details,
                'api_responses': {
                    api_type: details.get(f'{api_type}_count', 0) 
                    for api_type in ['nokttv', 'kttv']
                },
                'total_records': details.get('total_records', 0)
            }
            
            await self.db[self.collections['collection_logs']].insert_one(log_doc)
            logging.info(f"📝 Logged collection result: {status}")
            
        except Exception as e:
            logging.error(f"❌ Logging failed: {e}")

    async def run_daily_collection(self, target_date: Optional[date] = None) -> bool:
        """
        Main method để chạy daily collection
        
        Args:
            target_date: Ngày cần collect (default: hôm nay)
            
        Returns:
            bool: True nếu collection thành công
        """
        if target_date is None:
            target_date = date.today()
        
        start_time = datetime.utcnow()
        logging.info(f"🚀 Starting daily collection for {target_date}")
        
        try:
            # Initialize database
            if not await self.initialize_database():
                return False
            
            # Backup existing data
            await self.backup_existing_data(target_date)
            
            all_documents = []
            collection_details = {'total_records': 0}
            
            # Process both API types
            for api_type in ['nokttv', 'kttv']:
                try:
                    logging.info(f"📡 Processing {api_type.upper()} API...")
                    
                    # Fetch stations và tạo mapping
                    stations = await self.fetch_stations(api_type)
                    if stations:
                        self.create_station_mapping(stations, api_type)
                    
                    # Fetch daily stats
                    stats = await self.fetch_daily_stats(api_type)
                    if stats:
                        documents = await self.process_daily_data(stats, api_type, target_date)
                        all_documents.extend(documents)
                        collection_details[f'{api_type}_count'] = len(documents)
                    else:
                        collection_details[f'{api_type}_count'] = 0
                        
                except Exception as e:
                    logging.error(f"❌ Error processing {api_type}: {e}")
                    collection_details[f'{api_type}_error'] = str(e)
            
            # Update databases
            if all_documents:
                collection_details['total_records'] = len(all_documents)
                
                # Update historical data (với deduplication)
                historical_success = await self.upsert_historical_data(all_documents)
                
                # Update current data (cho real-time display)
                current_success = await self.update_current_data(all_documents)
                
                if historical_success and current_success:
                    status = 'success'
                elif historical_success or current_success:
                    status = 'partial'
                else:
                    status = 'failed'
            else:
                status = 'failed'
                collection_details['error'] = 'No data collected from any API'
            
            # Log kết quả
            collection_details['execution_time'] = (datetime.utcnow() - start_time).total_seconds()
            await self.log_collection_result(target_date, status, collection_details)
            
            logging.info(f"✅ Daily collection completed: {status} - {len(all_documents)} records")
            return status in ['success', 'partial']
            
        except Exception as e:
            logging.error(f"❌ Daily collection failed: {e}")
            await self.log_collection_result(target_date, 'failed', {'error': str(e)})
            return False
            
        finally:
            if hasattr(self, 'client') and self.client:
                try:
                    await self.client.close()
                except Exception:
                    pass  # Ignore close errors
                finally:
                    self.client = None

    async def cleanup_old_logs(self, days_to_keep: int = 30):
        """
        Cleanup logs cũ để tránh database bloat
        
        Args:
            days_to_keep: Số ngày logs cần giữ
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
            
            result = await self.db[self.collections['collection_logs']].delete_many({
                'execution_time': {'$lt': cutoff_date}
            })
            
            logging.info(f"🧹 Cleaned up {result.deleted_count} old log entries")
            
        except Exception as e:
            logging.error(f"❌ Log cleanup failed: {e}")

if __name__ == "__main__":
    async def main():
        """Main entry point cho script chạy độc lập"""
        collector = DailyDataCollector()
        
        # Option to collect cho ngày khác (for testing/backfill)
        target_date = None
        if len(sys.argv) > 1:
            try:
                target_date = datetime.strptime(sys.argv[1], '%Y-%m-%d').date()
                logging.info(f"🎯 Collecting data for specified date: {target_date}")
            except ValueError:
                logging.error("❌ Invalid date format. Use YYYY-MM-DD")
                sys.exit(1)
        
        success = await collector.run_daily_collection(target_date)
        
        if success:
            logging.info("✅ Script completed successfully")
            sys.exit(0)
        else:
            logging.error("❌ Script completed with errors")
            sys.exit(1)
    
    asyncio.run(main())