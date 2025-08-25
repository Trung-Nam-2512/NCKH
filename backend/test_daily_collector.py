#!/usr/bin/env python3
"""
TEST SCRIPT CHO DAILY DATA COLLECTOR

Script này test toàn diện functionality của daily data collector:
1. Database connection và index creation
2. API data fetching từ nokttv và kttv
3. Data processing và deduplication
4. Historical data storage
5. Error handling và recovery
6. Logging và monitoring
"""

import asyncio
import logging
import sys
import os
from datetime import datetime, date, timedelta
import json

# Add path để import
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# Import services để test
from app.services.daily_data_collector import DailyDataCollector
from app.services.scheduler_service import SchedulerService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
)

async def test_database_connection():
    """Test database connection và index creation"""
    print("\n" + "="*50)
    print("🔍 TESTING DATABASE CONNECTION")
    print("="*50)
    
    collector = DailyDataCollector()
    
    try:
        success = await collector.initialize_database()
        if success:
            print("✅ Database connection: SUCCESS")
            print(f"✅ Database name: {collector.db.name}")
            
            # Test collection access
            collections = await collector.db.list_collection_names()
            print(f"✅ Available collections: {len(collections)}")
            
            return True
        else:
            print("❌ Database connection: FAILED")
            return False
            
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return False
    finally:
        if collector.client:
            collector.client.close()

async def test_api_connectivity():
    """Test kết nối đến các API endpoints"""
    print("\n" + "="*50)
    print("🌐 TESTING API CONNECTIVITY")
    print("="*50)
    
    collector = DailyDataCollector()
    
    results = {}
    
    for api_type in ['nokttv', 'kttv']:
        print(f"\n🔍 Testing {api_type.upper()} API...")
        
        try:
            # Test stations API
            stations = await collector.fetch_stations(api_type)
            print(f"   📊 Stations fetched: {len(stations)}")
            results[f'{api_type}_stations'] = len(stations)
            
            # Test stats API
            stats = await collector.fetch_daily_stats(api_type)
            print(f"   📈 Stats fetched: {len(stats)}")
            results[f'{api_type}_stats'] = len(stats)
            
            if stations:
                collector.create_station_mapping(stations, api_type)
                print(f"   🗺️ Station mapping created: {len(collector.station_mapping)} total stations")
            
        except Exception as e:
            print(f"   ❌ {api_type.upper()} API error: {e}")
            results[f'{api_type}_error'] = str(e)
    
    print(f"\n📊 API Test Summary:")
    print(json.dumps(results, indent=2))
    
    return results

async def test_data_processing():
    """Test data processing và deduplication logic"""
    print("\n" + "="*50)
    print("🔄 TESTING DATA PROCESSING")
    print("="*50)
    
    collector = DailyDataCollector()
    
    try:
        await collector.initialize_database()
        
        target_date = date.today()
        print(f"🎯 Processing data for: {target_date}")
        
        total_documents = 0
        
        for api_type in ['nokttv', 'kttv']:
            print(f"\n🔍 Processing {api_type.upper()}...")
            
            # Fetch và process data
            stations = await collector.fetch_stations(api_type)
            if stations:
                collector.create_station_mapping(stations, api_type)
                
                stats = await collector.fetch_daily_stats(api_type)
                if stats:
                    documents = await collector.process_daily_data(stats, api_type, target_date)
                    total_documents += len(documents)
                    print(f"   📝 Documents processed: {len(documents)}")
                    
                    # Show sample document
                    if documents:
                        sample = documents[0]
                        print(f"   📋 Sample document keys: {list(sample.keys())}")
                        print(f"   📍 Sample station: {sample.get('name', 'Unknown')}")
        
        print(f"\n✅ Total documents processed: {total_documents}")
        return total_documents > 0
        
    except Exception as e:
        print(f"❌ Data processing error: {e}")
        return False
    finally:
        if collector.client:
            collector.client.close()

async def test_full_collection():
    """Test complete daily collection process"""
    print("\n" + "="*50)
    print("🚀 TESTING FULL COLLECTION PROCESS")
    print("="*50)
    
    collector = DailyDataCollector()
    
    try:
        # Test với hôm nay
        target_date = date.today()
        print(f"🎯 Running full collection for: {target_date}")
        
        success = await collector.run_daily_collection(target_date)
        
        if success:
            print("✅ Full collection: SUCCESS")
            
            # Verify data was saved
            if await collector.initialize_database():
                historical_count = await collector.db[collector.collections['historical_data']].count_documents({
                    'collection_date': target_date
                })
                current_count = await collector.db[collector.collections['current_data']].count_documents({})
                
                print(f"📊 Historical data saved: {historical_count} records")
                print(f"📊 Current data saved: {current_count} records")
                
                # Check latest log
                latest_log = await collector.db[collector.collections['collection_logs']].find_one(
                    {'collection_date': target_date},
                    sort=[('execution_time', -1)]
                )
                
                if latest_log:
                    print(f"📝 Collection logged: {latest_log['status']}")
                    print(f"📈 Total records in log: {latest_log.get('details', {}).get('total_records', 0)}")
            
            return True
        else:
            print("❌ Full collection: FAILED")
            return False
            
    except Exception as e:
        print(f"❌ Full collection error: {e}")
        return False

async def test_deduplication():
    """Test deduplication logic bằng cách chạy collection 2 lần"""
    print("\n" + "="*50)
    print("🔄 TESTING DEDUPLICATION LOGIC")
    print("="*50)
    
    collector = DailyDataCollector()
    
    try:
        await collector.initialize_database()
        target_date = date.today()
        
        print("📅 Running first collection...")
        success1 = await collector.run_daily_collection(target_date)
        
        if success1:
            # Count records after first run
            count1 = await collector.db[collector.collections['historical_data']].count_documents({
                'collection_date': target_date
            })
            print(f"📊 Records after first run: {count1}")
            
            # Run second time
            print("📅 Running second collection (should deduplicate)...")
            success2 = await collector.run_daily_collection(target_date)
            
            if success2:
                count2 = await collector.db[collector.collections['historical_data']].count_documents({
                    'collection_date': target_date
                })
                print(f"📊 Records after second run: {count2}")
                
                if count1 == count2:
                    print("✅ Deduplication: SUCCESS (no duplicate records created)")
                    return True
                else:
                    print(f"⚠️ Deduplication: ISSUE (count changed from {count1} to {count2})")
                    return False
            else:
                print("❌ Second collection failed")
                return False
        else:
            print("❌ First collection failed")
            return False
            
    except Exception as e:
        print(f"❌ Deduplication test error: {e}")
        return False
    finally:
        if collector.client:
            collector.client.close()

async def test_scheduler_service():
    """Test scheduler service functionality"""
    print("\n" + "="*50)
    print("⏰ TESTING SCHEDULER SERVICE")
    print("="*50)
    
    try:
        scheduler = SchedulerService()
        
        # Test configuration
        print("🔧 Testing scheduler configuration...")
        status = scheduler.get_status()
        print(f"✅ Scheduler status: {json.dumps(status, indent=2)}")
        
        # Test manual collection
        print("🔧 Testing manual collection trigger...")
        success = await scheduler.run_manual_collection()
        
        if success:
            print("✅ Manual collection via scheduler: SUCCESS")
            return True
        else:
            print("❌ Manual collection via scheduler: FAILED")
            return False
            
    except Exception as e:
        print(f"❌ Scheduler service test error: {e}")
        return False

async def test_historical_data_query():
    """Test querying historical data để đảm bảo có thể dùng cho frequency analysis"""
    print("\n" + "="*50)
    print("📈 TESTING HISTORICAL DATA QUERIES")
    print("="*50)
    
    collector = DailyDataCollector()
    
    try:
        await collector.initialize_database()
        
        # Query data by date range
        end_date = date.today()
        start_date = end_date - timedelta(days=7)
        
        count = await collector.db[collector.collections['historical_data']].count_documents({
            'collection_date': {
                '$gte': start_date,
                '$lte': end_date
            }
        })
        
        print(f"📊 Historical records (last 7 days): {count}")
        
        # Query by station
        station_pipeline = [
            {'$group': {'_id': '$station_id', 'count': {'$sum': 1}}},
            {'$sort': {'count': -1}},
            {'$limit': 5}
        ]
        
        station_cursor = collector.db[collector.collections['historical_data']].aggregate(station_pipeline)
        stations = [doc async for doc in station_cursor]
        
        print("📍 Top 5 stations by data count:")
        for station in stations:
            print(f"   {station['_id']}: {station['count']} records")
        
        # Query by API type
        api_pipeline = [
            {'$group': {'_id': '$api_type', 'count': {'$sum': 1}, 'avg_depth': {'$avg': '$depth'}}},
            {'$sort': {'count': -1}}
        ]
        
        api_cursor = collector.db[collector.collections['historical_data']].aggregate(api_pipeline)
        api_stats = [doc async for doc in api_cursor]
        
        print("🔌 Data by API type:")
        for stat in api_stats:
            print(f"   {stat['_id']}: {stat['count']} records, avg depth: {stat['avg_depth']:.3f}m")
        
        return count > 0
        
    except Exception as e:
        print(f"❌ Historical data query error: {e}")
        return False
    finally:
        if collector.client:
            collector.client.close()

async def run_comprehensive_test():
    """Chạy tất cả tests một cách comprehensive"""
    print("DAILY DATA COLLECTOR - COMPREHENSIVE TEST SUITE")
    print("="*70)
    
    start_time = datetime.utcnow()
    test_results = {}
    
    # Danh sách tests
    tests = [
        ("Database Connection", test_database_connection),
        ("API Connectivity", test_api_connectivity),
        ("Data Processing", test_data_processing),
        ("Full Collection", test_full_collection),
        ("Deduplication Logic", test_deduplication),
        ("Historical Data Queries", test_historical_data_query),
        ("Scheduler Service", test_scheduler_service)
    ]
    
    # Chạy từng test
    for test_name, test_func in tests:
        print(f"\n⏳ Running: {test_name}...")
        try:
            result = await test_func()
            test_results[test_name] = "PASS" if result else "FAIL"
        except Exception as e:
            test_results[test_name] = f"ERROR: {str(e)}"
            print(f"❌ {test_name} threw exception: {e}")
    
    # Summary
    duration = (datetime.utcnow() - start_time).total_seconds()
    
    print("\n" + "="*70)
    print("📊 TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for result in test_results.values() if result == "PASS")
    failed = len(test_results) - passed
    
    for test_name, result in test_results.items():
        status_icon = "✅" if result == "PASS" else "❌"
        print(f"{status_icon} {test_name}: {result}")
    
    print(f"\n📈 Results: {passed} PASSED, {failed} FAILED")
    print(f"⏱️ Total duration: {duration:.2f} seconds")
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED! Daily collector is ready for production.")
        return True
    else:
        print(f"\n⚠️ {failed} TESTS FAILED! Please review and fix issues.")
        return False

if __name__ == "__main__":
    success = asyncio.run(run_comprehensive_test())
    sys.exit(0 if success else 1)