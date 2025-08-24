#!/usr/bin/env python3
"""
Script quản lý Auto Data Collector Bot
- Khởi động/dừng bot
- Xem thống kê
- Thu thập dữ liệu thủ công
"""

import asyncio
import argparse
import json
from datetime import datetime, timedelta
from auto_data_collector import AutoDataCollector

class CollectorManager:
    def __init__(self):
        self.collector = AutoDataCollector()

    async def start_bot(self):
        """Khởi động bot"""
        print("🚀 Starting Auto Data Collector Bot...")
        success = await self.collector.start()
        if success:
            print("✅ Bot started successfully!")
            print("📊 Bot will now:")
            print("   - Collect data daily at 23:30")
            print("   - Collect full history weekly on Sundays at 02:00")
            print("   - Clean up old data weekly on Sundays at 03:00")
            print("\nPress Ctrl+C to stop the bot")
            
            # Keep running
            try:
                while True:
                    await asyncio.sleep(60)
            except KeyboardInterrupt:
                print("\n⏹️ Stopping bot...")
                await self.collector.stop()
        else:
            print("❌ Failed to start bot")

    async def collect_manual(self, days: int = 7):
        """Thu thập dữ liệu thủ công"""
        print(f"📥 Manually collecting data for {days} days...")
        
        # Initialize database
        await self.collector.initialize_database()
        
        # Collect data
        if days == 60:
            result = await self.collector.collect_full_history()
        else:
            # Collect specific number of days
            end_date = datetime.now()
            total_records = 0
            
            for i in range(days):
                target_date = (end_date - timedelta(days=i)).strftime("%Y-%m-%d")
                print(f"Collecting {target_date}...")
                
                api_data = await self.collector.fetch_daily_data(target_date)
                if api_data:
                    df = self.collector.process_daily_data(api_data, target_date)
                    if not df.empty:
                        saved_count = await self.collector.save_to_mongodb(df)
                        total_records += saved_count
                        print(f"✅ {target_date}: {saved_count} records")
                    else:
                        print(f"⚠️ {target_date}: No data")
                else:
                    print(f"❌ {target_date}: Failed")
                
                await asyncio.sleep(0.5)
            
            result = {"total_records": total_records}
        
        print(f"✅ Manual collection completed: {result.get('total_records', 0)} records")
        return result

    async def show_stats(self):
        """Hiển thị thống kê"""
        print("📊 Collection Statistics:")
        
        stats = await self.collector.get_collection_stats()
        
        if stats:
            print(f"Total records: {stats.get('total_records', 0):,}")
            print(f"Days with data: {stats.get('days_with_data', 0)}")
            print(f"Stations: {stats.get('stations_count', 0)}")
            
            date_range = stats.get('date_range', {})
            if date_range.get('first') and date_range.get('last'):
                print(f"Date range: {date_range['first']} to {date_range['last']}")
            
            print("\nRecent daily stats:")
            for day_stat in stats.get('daily_stats', [])[:5]:
                print(f"  {day_stat['_id']}: {day_stat['count']:,} records")
        else:
            print("❌ No data available")

    async def cleanup_data(self, days_to_keep: int = 60):
        """Dọn dẹp dữ liệu cũ"""
        print(f"🧹 Cleaning up data older than {days_to_keep} days...")
        deleted_count = await self.collector.cleanup_old_data(days_to_keep)
        print(f"✅ Cleaned up {deleted_count} records")

    async def test_connection(self):
        """Test kết nối"""
        print("🔍 Testing connections...")
        
        # Test MongoDB
        try:
            await self.collector.mongo_client.admin.command('ping')
            print("✅ MongoDB connection: OK")
        except Exception as e:
            print(f"❌ MongoDB connection failed: {e}")
            return False
        
        # Test API
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            api_data = await self.collector.fetch_daily_data(today)
            if api_data:
                print("✅ API connection: OK")
            else:
                print("⚠️ API connection: No data returned")
        except Exception as e:
            print(f"❌ API connection failed: {e}")
            return False
        
        return True

async def main():
    parser = argparse.ArgumentParser(description='Auto Data Collector Manager')
    parser.add_argument('command', choices=['start', 'collect', 'stats', 'cleanup', 'test'], 
                       help='Command to execute')
    parser.add_argument('--days', type=int, default=7, 
                       help='Number of days to collect (default: 7)')
    parser.add_argument('--keep-days', type=int, default=60, 
                       help='Days to keep when cleaning up (default: 60)')
    
    args = parser.parse_args()
    
    manager = CollectorManager()
    
    if args.command == 'start':
        await manager.start_bot()
    elif args.command == 'collect':
        await manager.collect_manual(args.days)
    elif args.command == 'stats':
        await manager.show_stats()
    elif args.command == 'cleanup':
        await manager.cleanup_data(args.keep_days)
    elif args.command == 'test':
        await manager.test_connection()

if __name__ == "__main__":
    asyncio.run(main()) 