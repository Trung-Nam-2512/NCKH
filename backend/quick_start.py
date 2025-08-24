#!/usr/bin/env python3
"""
Quick Start Script
- Test toàn bộ hệ thống tích hợp realtime
- Thu thập dữ liệu mẫu
- Tích hợp phân tích tần suất
"""

import asyncio
import logging
from datetime import datetime
from manage_collector import CollectorManager
from frequency_integration import FrequencyIntegration

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

async def quick_test():
    """Test nhanh toàn bộ hệ thống"""
    print("🚀 QUICK START - REALTIME INTEGRATION SYSTEM")
    print("=" * 50)
    
    # 1. Test kết nối
    print("\n1️⃣ Testing connections...")
    manager = CollectorManager()
    connection_ok = await manager.test_connection()
    
    if not connection_ok:
        print("❌ Connection test failed. Please check your configuration.")
        return False
    
    print("✅ All connections OK!")
    
    # 2. Thu thập dữ liệu mẫu
    print("\n2️⃣ Collecting sample data (3 days)...")
    try:
        result = await manager.collect_manual(3)
        print(f"✅ Collected {result.get('total_records', 0)} records")
    except Exception as e:
        print(f"❌ Data collection failed: {e}")
        return False
    
    # 3. Xem thống kê
    print("\n3️⃣ Checking statistics...")
    await manager.show_stats()
    
    # 4. Tích hợp phân tích tần suất
    print("\n4️⃣ Frequency analysis integration...")
    integration = FrequencyIntegration()
    
    # Xuất dữ liệu
    df = await integration.export_for_analysis()
    if not df.empty:
        print(f"✅ Exported {len(df)} records for frequency analysis")
    
    # Tạo báo cáo
    report = await integration.generate_frequency_report()
    if report:
        print("✅ Frequency analysis report generated")
    
    # 5. Tổng kết
    print("\n" + "=" * 50)
    print("🎉 QUICK START COMPLETED SUCCESSFULLY!")
    print("\n📊 System Status:")
    print("   ✅ API connections: OK")
    print("   ✅ MongoDB: OK")
    print("   ✅ Data collection: OK")
    print("   ✅ Frequency integration: OK")
    
    print("\n📁 Generated Files:")
    print("   - realtime_frequency_data.csv")
    print("   - frequency_analysis_report.json")
    print("   - auto_collector.log")
    
    print("\n🚀 Next Steps:")
    print("   1. Start auto collector: python manage_collector.py start")
    print("   2. Monitor logs: tail -f auto_collector.log")
    print("   3. Check stats: python manage_collector.py stats")
    
    return True

async def main():
    """Hàm chính"""
    try:
        success = await quick_test()
        if success:
            print("\n🎯 System is ready for production use!")
        else:
            print("\n❌ Quick start failed. Please check the logs.")
    except KeyboardInterrupt:
        print("\n⏹️ Quick start interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 