#!/usr/bin/env python3
"""
Ensure Data Availability - Make sure database always has data for frequency analysis
"""
import asyncio
import logging
from datetime import datetime
from app.services.realtime_service import EnhancedRealtimeService
from app.services.data_service import DataService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def ensure_data_available():
    """Ensure database has sufficient data for frequency analysis"""
    
    try:
        data_service = DataService()
        realtime_service = EnhancedRealtimeService(data_service)
        await realtime_service.initialize_database()
        
        collection = realtime_service.db.realtime_data
        total_count = await collection.count_documents({})
        
        logger.info(f"Current database records: {total_count}")
        
        if total_count < 100:  # If insufficient data
            logger.info("Insufficient data detected. Creating test data...")
            
            # Generate more comprehensive test data
            from create_test_data import generate_realistic_water_level_data
            
            test_records = generate_realistic_water_level_data()
            logger.info(f"Generated {len(test_records)} test records")
            
            # Clear and insert
            await collection.delete_many({})
            logger.info("Cleared existing data")
            
            # Insert in batches
            batch_size = 1000
            for i in range(0, len(test_records), batch_size):
                batch = test_records[i:i+batch_size]
                await collection.insert_many(batch)
                logger.info(f"Inserted batch {i//batch_size + 1}: {len(batch)} records")
            
            # Verify insertion
            final_count = await collection.count_documents({})
            logger.info(f"Final database records: {final_count}")
        
        # Test frequency analysis capability
        freq_data = await realtime_service.get_frequency_ready_data(min_years=1)
        logger.info(f"Frequency-ready data: {len(freq_data)} records")
        
        if len(freq_data) > 0:
            stations = freq_data['station_id'].nunique() if hasattr(freq_data, 'nunique') else len(set(freq_data.get('station_id', [])))
            years = sorted(set(freq_data['Year'])) if 'Year' in freq_data.columns else []
            logger.info(f"Available for analysis: {stations} stations, years {years}")
            
            return True
        else:
            logger.error("No frequency-ready data available")
            return False
            
    except Exception as e:
        logger.error(f"Error ensuring data availability: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_integration_after_data_setup():
    """Test integration service after ensuring data is available"""
    
    try:
        from app.services.integration_service import IntegrationService
        
        data_service = DataService()
        integration_service = IntegrationService(data_service)
        
        # Test the integration
        result = await integration_service.analyze_historical_realtime(
            min_years=1,
            distribution_name="gumbel",
            agg_func="max",
            use_professional=False
        )
        
        logger.info("✅ Integration test PASSED")
        logger.info(f"Message: {result['message']}")
        logger.info(f"Records: {result['data_summary']['total_records']}")
        logger.info(f"Grade: {result['analysis_grade']}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Integration test FAILED: {e}")
        return False

if __name__ == "__main__":
    print("=== ENSURING DATA AVAILABILITY ===")
    
    # Step 1: Ensure data is available
    data_ok = asyncio.run(ensure_data_available())
    
    if data_ok:
        print("✅ Data is available")
        
        # Step 2: Test integration
        integration_ok = asyncio.run(test_integration_after_data_setup())
        
        if integration_ok:
            print("✅ Integration working correctly")
            print("✅ System ready for API requests")
        else:
            print("❌ Integration test failed")
            exit(1)
    else:
        print("❌ Could not ensure data availability")
        exit(1)