#!/usr/bin/env python3
"""
Auto Data Collection Bot
- Gom dữ liệu tối đa 2 tháng từ API
- Tự động cập nhật dữ liệu mới nhất
- Lưu trữ vào MongoDB cho phân tích tần suất
"""

import asyncio
import logging
import os
import sys
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import pandas as pd
import httpx
from motor.motor_asyncio import AsyncIOMotorClient
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('auto_collector.log'),
        logging.StreamHandler()
    ]
)

class AutoDataCollector:
    def __init__(self):
        self.mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
        self.stations_url = os.getenv("STATIONS_API_BASE_URL")
        self.stats_url = os.getenv("STATS_API_BASE_URL")
        self.api_key = os.getenv("API_KEY")
        self.headers = {"X-API-Key": self.api_key} if self.api_key else {}
        
        # MongoDB setup
        self.mongo_client = AsyncIOMotorClient(self.mongo_uri)
        self.db = self.mongo_client["hydro_db"]
        self.collection = self.db["realtime_depth"]
        
        # Scheduler setup
        self.scheduler = AsyncIOScheduler()
        
        # Configuration
        self.max_days = 60  # Tối đa 2 tháng
        self.delay_between_calls = 0.5  # Delay giữa các API call
        self.last_collection_date = None
        
        logging.info("=== AUTO DATA COLLECTOR INITIALIZED ===")
        logging.info(f"MongoDB: {self.mongo_uri}")
        logging.info(f"API: {self.stats_url}")
        logging.info(f"Max days: {self.max_days}")
        logging.info(f"Delay: {self.delay_between_calls}s")

    async def initialize_database(self):
        """Khởi tạo database và indexes"""
        try:
            # Tạo indexes cho hiệu suất truy vấn
            await self.collection.create_index([("station_id", 1)])
            await self.collection.create_index([("time_point", 1)])
            await self.collection.create_index([("Year", 1)])
            await self.collection.create_index([("station_id", 1), ("Year", 1)])
            await self.collection.create_index([("collection_date", 1)])
            
            logging.info("✅ Database initialized with indexes")
            return True
        except Exception as e:
            logging.error(f"❌ Database initialization failed: {e}")
            return False

    async def fetch_daily_data(self, date: str) -> Optional[Dict[str, Any]]:
        """Fetch dữ liệu cho một ngày cụ thể"""
        start_time = f"{date} 05:00:00"
        end_time = f"{date} 23:00:00"
        
        params = {
            "start_time": start_time,
            "end_time": end_time
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(self.stats_url, params=params, headers=self.headers)
                if response.status_code == 200:
                    data = response.json()
                    if 'Data' in data and len(data['Data']) > 0:
                        return data
                else:
                    logging.warning(f"API returned {response.status_code} for {date}")
                return None
        except Exception as e:
            logging.error(f"Error fetching data for {date}: {e}")
            return None

    def process_daily_data(self, api_data: Dict[str, Any], collection_date: str) -> pd.DataFrame:
        """Xử lý dữ liệu từ API thành DataFrame"""
        all_measurements = []
        
        for station_data in api_data.get('Data', []):
            station_id = station_data.get('station_id', 'Unknown')
            for meas in station_data.get('value', []):
                meas_dict = meas.copy()
                meas_dict['station_id'] = station_id
                meas_dict['collection_date'] = collection_date
                all_measurements.append(meas_dict)
        
        if not all_measurements:
            return pd.DataFrame()
        
        df = pd.DataFrame(all_measurements)
        df['time_point'] = pd.to_datetime(df['time_point'])
        df['Year'] = df['time_point'].dt.year
        df['Month'] = df['time_point'].dt.month
        df['Day'] = df['time_point'].dt.day
        
        return df

    async def save_to_mongodb(self, df: pd.DataFrame):
        """Lưu dữ liệu vào MongoDB"""
        if df.empty:
            return 0
        
        try:
            # Kiểm tra dữ liệu đã tồn tại
            existing_count = await self.collection.count_documents({
                "collection_date": df['collection_date'].iloc[0]
            })
            
            if existing_count > 0:
                logging.info(f"Data for {df['collection_date'].iloc[0]} already exists, skipping...")
                return 0
            
            # Lưu dữ liệu mới
            records = df.to_dict('records')
            result = await self.collection.insert_many(records)
            
            logging.info(f"✅ Saved {len(result.inserted_ids)} records for {df['collection_date'].iloc[0]}")
            return len(result.inserted_ids)
            
        except Exception as e:
            logging.error(f"Error saving to MongoDB: {e}")
            return 0

    async def collect_full_history(self):
        """Thu thập toàn bộ lịch sử 2 tháng"""
        logging.info("=== STARTING FULL HISTORY COLLECTION ===")
        
        end_date = datetime.now()
        total_records = 0
        successful_days = 0
        failed_days = 0
        
        for i in range(self.max_days):
            target_date = (end_date - timedelta(days=i)).strftime("%Y-%m-%d")
            logging.info(f"Collecting data for {target_date}...")
            
            # Fetch data
            api_data = await self.fetch_daily_data(target_date)
            
            if api_data:
                # Process data
                df = self.process_daily_data(api_data, target_date)
                
                if not df.empty:
                    # Save to MongoDB
                    saved_count = await self.save_to_mongodb(df)
                    total_records += saved_count
                    successful_days += 1
                    logging.info(f"✅ {target_date}: {saved_count} records")
                else:
                    failed_days += 1
                    logging.warning(f"⚠️ {target_date}: No data")
            else:
                failed_days += 1
                logging.error(f"❌ {target_date}: Failed to fetch")
            
            # Delay between calls
            await asyncio.sleep(self.delay_between_calls)
        
        logging.info(f"=== FULL HISTORY COLLECTION COMPLETED ===")
        logging.info(f"Successful days: {successful_days}")
        logging.info(f"Failed days: {failed_days}")
        logging.info(f"Total records: {total_records}")
        
        return {
            "successful_days": successful_days,
            "failed_days": failed_days,
            "total_records": total_records
        }

    async def collect_today_data(self):
        """Thu thập dữ liệu ngày hôm nay"""
        today = datetime.now().strftime("%Y-%m-%d")
        logging.info(f"=== COLLECTING TODAY'S DATA ({today}) ===")
        
        # Fetch today's data
        api_data = await self.fetch_daily_data(today)
        
        if api_data:
            # Process data
            df = self.process_daily_data(api_data, today)
            
            if not df.empty:
                # Save to MongoDB
                saved_count = await self.save_to_mongodb(df)
                logging.info(f"✅ Today's data: {saved_count} records")
                self.last_collection_date = today
                return saved_count
            else:
                logging.warning(f"⚠️ Today's data: No records")
                return 0
        else:
            logging.error(f"❌ Today's data: Failed to fetch")
            return 0

    async def cleanup_old_data(self, days_to_keep: int = 60):
        """Dọn dẹp dữ liệu cũ (giữ lại 2 tháng)"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            result = await self.collection.delete_many({
                "collection_date": {"$lt": cutoff_date.strftime("%Y-%m-%d")}
            })
            logging.info(f"🧹 Cleaned up {result.deleted_count} old records")
            return result.deleted_count
        except Exception as e:
            logging.error(f"Error cleaning up old data: {e}")
            return 0

    async def get_collection_stats(self) -> Dict[str, Any]:
        """Lấy thống kê về dữ liệu đã thu thập"""
        try:
            # Tổng số records
            total_records = await self.collection.count_documents({})
            
            # Số ngày có dữ liệu
            pipeline = [
                {"$group": {"_id": "$collection_date", "count": {"$sum": 1}}},
                {"$sort": {"_id": -1}}
            ]
            daily_stats = await self.collection.aggregate(pipeline).to_list(None)
            
            # Số trạm
            station_count = await self.collection.distinct("station_id")
            
            # Khoảng thời gian
            first_record = await self.collection.find_one({}, sort=[("time_point", 1)])
            last_record = await self.collection.find_one({}, sort=[("time_point", -1)])
            
            return {
                "total_records": total_records,
                "days_with_data": len(daily_stats),
                "stations_count": len(station_count),
                "date_range": {
                    "first": first_record["time_point"] if first_record else None,
                    "last": last_record["time_point"] if last_record else None
                },
                "daily_stats": daily_stats[:10]  # 10 ngày gần nhất
            }
        except Exception as e:
            logging.error(f"Error getting collection stats: {e}")
            return {}

    def setup_scheduler(self):
        """Thiết lập lịch trình tự động"""
        # Thu thập dữ liệu hàng ngày lúc 23:30
        self.scheduler.add_job(
            self.collect_today_data,
            CronTrigger(hour=23, minute=30),
            id='daily_collection',
            name='Daily Data Collection'
        )
        
        # Thu thập toàn bộ lịch sử hàng tuần (Chủ nhật 02:00)
        self.scheduler.add_job(
            self.collect_full_history,
            CronTrigger(day_of_week='sun', hour=2),
            id='weekly_full_collection',
            name='Weekly Full History Collection'
        )
        
        # Dọn dẹp dữ liệu cũ hàng tuần (Chủ nhật 03:00)
        self.scheduler.add_job(
            self.cleanup_old_data,
            CronTrigger(day_of_week='sun', hour=3),
            id='weekly_cleanup',
            name='Weekly Data Cleanup'
        )
        
        logging.info("✅ Scheduler setup completed")
        logging.info("   - Daily collection: 23:30 every day")
        logging.info("   - Weekly full collection: 02:00 every Sunday")
        logging.info("   - Weekly cleanup: 03:00 every Sunday")

    async def start(self):
        """Khởi động bot"""
        logging.info("=== STARTING AUTO DATA COLLECTOR ===")
        
        # Initialize database
        if not await self.initialize_database():
            logging.error("❌ Failed to initialize database")
            return False
        
        # Setup scheduler
        self.setup_scheduler()
        
        # Start scheduler
        self.scheduler.start()
        logging.info("✅ Scheduler started")
        
        # Collect initial data
        logging.info("Starting initial data collection...")
        await self.collect_full_history()
        
        # Show stats
        stats = await self.get_collection_stats()
        logging.info("=== INITIAL STATS ===")
        logging.info(f"Total records: {stats.get('total_records', 0)}")
        logging.info(f"Days with data: {stats.get('days_with_data', 0)}")
        logging.info(f"Stations: {stats.get('stations_count', 0)}")
        
        logging.info("🎉 Auto Data Collector is now running!")
        return True

    async def stop(self):
        """Dừng bot"""
        logging.info("=== STOPPING AUTO DATA COLLECTOR ===")
        self.scheduler.shutdown()
        self.mongo_client.close()
        logging.info("✅ Auto Data Collector stopped")

async def main():
    """Hàm chính"""
    collector = AutoDataCollector()
    
    try:
        await collector.start()
        
        # Keep running
        while True:
            await asyncio.sleep(60)  # Check every minute
            
    except KeyboardInterrupt:
        logging.info("Received interrupt signal")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
    finally:
        await collector.stop()

if __name__ == "__main__":
    asyncio.run(main()) 