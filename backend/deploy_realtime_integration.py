#!/usr/bin/env python3
"""
Script triển khai hệ thống tích hợp dữ liệu realtime vào MongoDB
và thiết lập auto-poll cho phân tích tần suất
"""

import asyncio
import logging
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('realtime_integration.log'),
        logging.StreamHandler()
    ]
)

class RealtimeIntegrationDeployer:
    def __init__(self):
        self.mongo_uri = os.getenv("MONGO_URI")
        self.stations_url = os.getenv("STATIONS_API_BASE_URL")
        self.stats_url = os.getenv("STATS_API_BASE_URL")
        self.api_key = os.getenv("API_KEY")
        
        logging.info("=== REALTIME INTEGRATION DEPLOYER ===")
        logging.info(f"MongoDB URI: {self.mongo_uri}")
        logging.info(f"Stations API: {self.stations_url}")
        logging.info(f"Stats API: {self.stats_url}")
        logging.info(f"API Key: {'Set' if self.api_key else 'Not set'}")

    async def test_connectivity(self):
        """Test kết nối đến MongoDB và API"""
        logging.info("\n=== TESTING CONNECTIVITY ===")
        
        # Test MongoDB
        try:
            from motor.motor_asyncio import AsyncIOMotorClient
            client = AsyncIOMotorClient(self.mongo_uri)
            await client.admin.command('ping')
            logging.info("✅ MongoDB connection successful")
            client.close()
        except Exception as e:
            logging.error(f"❌ MongoDB connection failed: {e}")
            return False
        
        # Test API
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                headers = {"X-API-Key": self.api_key} if self.api_key else {}
                response = await client.get(self.stations_url, headers=headers)
                if response.status_code == 200:
                    stations = response.json()
                    logging.info(f"✅ API connection successful - {len(stations)} stations available")
                else:
                    logging.error(f"❌ API connection failed: {response.status_code}")
                    return False
        except Exception as e:
            logging.error(f"❌ API connection failed: {e}")
            return False
        
        return True

    async def initialize_database(self):
        """Khởi tạo database và collections"""
        logging.info("\n=== INITIALIZING DATABASE ===")
        
        try:
            from motor.motor_asyncio import AsyncIOMotorClient
            client = AsyncIOMotorClient(self.mongo_uri)
            db = client["hydro_db"]
            collection = db["realtime_depth"]
            
            # Tạo indexes cho hiệu suất truy vấn
            await collection.create_index([("station_id", 1)])
            await collection.create_index([("time_point", 1)])
            await collection.create_index([("Year", 1)])
            await collection.create_index([("station_id", 1), ("Year", 1)])
            
            logging.info("✅ Database initialized with indexes")
            client.close()
        except Exception as e:
            logging.error(f"❌ Database initialization failed: {e}")
            return False
        
        return True

    async def fetch_initial_data(self, days: int = 30):
        """Fetch dữ liệu ban đầu (30 ngày gần nhất)"""
        logging.info(f"\n=== FETCHING INITIAL DATA ({days} days) ===")
        
        try:
            from app.services.realtime_service import RealTimeService
            from app.services.data_service import DataService
            
            data_service = DataService()
            realtime_service = RealTimeService(data_service)
            
            # Fetch dữ liệu tích lũy
            accumulated_data = await realtime_service.fetch_accumulated_data(days=days)
            
            total_records = 0
            for daily_data in accumulated_data:
                df = realtime_service.process_to_df(daily_data)
                await realtime_service.integrate_to_analysis(df)
                total_records += len(df)
                logging.info(f"Processed {len(df)} records for a day")
            
            logging.info(f"✅ Initial data fetch completed: {total_records} total records")
            return True
            
        except Exception as e:
            logging.error(f"❌ Initial data fetch failed: {e}")
            return False

    async def setup_auto_poll(self):
        """Thiết lập auto-poll scheduler"""
        logging.info("\n=== SETTING UP AUTO-POLL ===")
        
        try:
            from app.services.realtime_service import RealTimeService
            from app.services.data_service import DataService
            
            data_service = DataService()
            realtime_service = RealTimeService(data_service)
            
            # Thiết lập daily poll (23:30 mỗi ngày)
            realtime_service.setup_auto_poll()
            
            # Thiết lập weekly accumulation (Chủ nhật 02:00)
            realtime_service.setup_accumulation_poll()
            
            logging.info("✅ Auto-poll scheduler setup completed")
            logging.info("   - Daily poll: 23:30 every day")
            logging.info("   - Weekly accumulation: 02:00 every Sunday")
            return True
            
        except Exception as e:
            logging.error(f"❌ Auto-poll setup failed: {e}")
            return False

    async def test_frequency_analysis_integration(self):
        """Test tích hợp với phân tích tần suất"""
        logging.info("\n=== TESTING FREQUENCY ANALYSIS INTEGRATION ===")
        
        try:
            from app.services.realtime_service import RealTimeService
            from app.services.data_service import DataService
            
            data_service = DataService()
            realtime_service = RealTimeService(data_service)
            
            # Lấy dữ liệu sẵn sàng cho phân tích tần suất
            frequency_data = await realtime_service.get_frequency_ready_data(min_years=1)
            
            if not frequency_data.empty:
                logging.info(f"✅ Frequency analysis integration successful")
                logging.info(f"   - Available data: {len(frequency_data)} records")
                logging.info(f"   - Stations: {frequency_data['station_id'].nunique()}")
                logging.info(f"   - Years: {frequency_data['Year'].nunique()}")
            else:
                logging.warning("⚠️  No frequency-ready data available yet")
                logging.info("   - Need to accumulate more data over time")
            
            return True
            
        except Exception as e:
            logging.error(f"❌ Frequency analysis integration failed: {e}")
            return False

    async def deploy(self):
        """Triển khai toàn bộ hệ thống"""
        logging.info("\n=== STARTING DEPLOYMENT ===")
        
        # Test connectivity
        if not await self.test_connectivity():
            logging.error("❌ Deployment failed: Connectivity test failed")
            return False
        
        # Initialize database
        if not await self.initialize_database():
            logging.error("❌ Deployment failed: Database initialization failed")
            return False
        
        # Fetch initial data
        if not await self.fetch_initial_data(days=30):
            logging.warning("⚠️  Initial data fetch failed, but continuing...")
        
        # Setup auto-poll
        if not await self.setup_auto_poll():
            logging.error("❌ Deployment failed: Auto-poll setup failed")
            return False
        
        # Test frequency analysis integration
        await self.test_frequency_analysis_integration()
        
        logging.info("\n=== DEPLOYMENT COMPLETED SUCCESSFULLY ===")
        logging.info("🎉 Realtime integration system is now running!")
        logging.info("📊 Data will be automatically collected and stored in MongoDB")
        logging.info("📈 Frequency analysis will be available as data accumulates")
        
        return True

async def main():
    """Hàm chính để triển khai"""
    deployer = RealtimeIntegrationDeployer()
    success = await deployer.deploy()
    
    if success:
        print("\n🎉 Deployment completed successfully!")
        print("The realtime integration system is now running.")
        print("Check the logs for detailed information.")
    else:
        print("\n❌ Deployment failed!")
        print("Check the logs for error details.")

if __name__ == "__main__":
    asyncio.run(main()) 