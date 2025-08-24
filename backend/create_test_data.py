#!/usr/bin/env python3
"""
Create Test Data for Frequency Analysis
Generate realistic hydrological data for testing
"""
import asyncio
import sys
import os
import logging
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
sys.path.append(os.path.dirname(__file__))

from app.services.realtime_service import EnhancedRealtimeService
from app.services.data_service import DataService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_realistic_water_level_data():
    """Generate realistic water level data for multiple years"""
    
    # Station data
    stations = [
        {'id': 'STN001', 'name': 'Station A', 'lat': 10.762622, 'lon': 106.660172},
        {'id': 'STN002', 'name': 'Station B', 'lat': 10.775699, 'lon': 106.700806}, 
        {'id': 'STN003', 'name': 'Station C', 'lat': 10.799890, 'lon': 106.721298},
        {'id': 'STN004', 'name': 'Station D', 'lat': 10.800170, 'lon': 106.650000},
        {'id': 'STN005', 'name': 'Station E', 'lat': 10.850000, 'lon': 106.680000}
    ]
    
    # Generate 10 years of data (2015-2024)
    years = range(2015, 2025)
    all_records = []
    
    for station in stations:
        station_id = station['id']
        station_name = station['name']
        lat = station['lat']
        lon = station['lon']
        
        # Base water level for this station (varies by location)
        base_level = np.random.uniform(0.5, 3.0)
        
        for year in years:
            # Generate daily data for this year
            start_date = datetime(year, 1, 1)
            end_date = datetime(year, 12, 31)
            
            current_date = start_date
            while current_date <= end_date:
                # Seasonal variation (higher in rainy season May-October)
                month = current_date.month
                if 5 <= month <= 10:  # Rainy season
                    seasonal_factor = 1.0 + np.random.uniform(0.2, 1.5)
                else:  # Dry season
                    seasonal_factor = 1.0 + np.random.uniform(-0.3, 0.2)
                
                # Daily variation
                daily_variation = np.random.normal(0, 0.1)
                
                # Extreme events (floods) - rare but significant
                extreme_prob = 0.02  # 2% chance per day
                if np.random.random() < extreme_prob:
                    extreme_factor = np.random.uniform(2.0, 5.0)
                else:
                    extreme_factor = 1.0
                
                # Calculate final water level
                water_level = base_level * seasonal_factor * extreme_factor + daily_variation
                water_level = max(0.01, water_level)  # Minimum 1cm
                
                # Create record
                record = {
                    'station_id': station_id,
                    'uuid': f'uuid-{station_id}',
                    'code': station_id,
                    'name': station_name,
                    'latitude': lat,
                    'longitude': lon,
                    'api_type': 'test_data',
                    'time_point': current_date,
                    'depth': round(water_level, 3),
                    'created_at': datetime.now()
                }
                
                all_records.append(record)
                current_date += timedelta(days=1)
    
    return all_records

async def create_test_data():
    """Create test data for frequency analysis"""
    
    logger.info("🧪 CREATING TEST DATA FOR FREQUENCY ANALYSIS")
    logger.info("=" * 50)
    
    try:
        # Generate realistic data
        logger.info("📊 Generating realistic water level data...")
        test_records = generate_realistic_water_level_data()
        logger.info(f"Generated {len(test_records)} records")
        
        # Initialize realtime service
        logger.info("🔄 Initializing Realtime Service...")
        data_service = DataService()
        realtime_service = EnhancedRealtimeService(data_service)
        await realtime_service.initialize_database()
        
        # Clear existing data and insert test data
        logger.info("🗄️ Inserting test data...")
        collection = realtime_service.db.realtime_data
        
        # Clear existing data
        await collection.delete_many({})
        
        # Insert test data in batches
        batch_size = 1000
        for i in range(0, len(test_records), batch_size):
            batch = test_records[i:i+batch_size]
            await collection.insert_many(batch)
            logger.info(f"Inserted batch {i//batch_size + 1}: {len(batch)} records")
        
        # Verify insertion
        total_count = await collection.count_documents({})
        logger.info(f"✅ Total records in database: {total_count}")
        
        # Test frequency analysis capability
        logger.info("🧪 Testing frequency analysis capability...")
        
        for min_years in [5, 3, 1]:
            freq_data = await realtime_service.get_frequency_ready_data(min_years=min_years)
            logger.info(f"Frequency data (min_years={min_years}): {len(freq_data)} records")
            
            if len(freq_data) > min_years:
                logger.info(f"  ✅ Sufficient data for {min_years}-year analysis")
                logger.info(f"  Stations: {freq_data['station_id'].nunique()}")
                logger.info(f"  Years: {sorted(freq_data['Year'].unique())}")
                logger.info(f"  Depth range: {freq_data['depth'].min():.3f} - {freq_data['depth'].max():.3f}")
                break
        
        # Test actual analysis
        logger.info("🎯 Testing actual frequency analysis...")
        from app.services.integration_service import IntegrationService
        
        integration_service = IntegrationService(data_service)
        
        try:
            result = await integration_service.analyze_historical_realtime(
                min_years=3,
                distribution_name="gumbel",
                agg_func="max",
                use_professional=False
            )
            
            logger.info("🎉 SUCCESS! Frequency analysis working with test data:")
            logger.info(f"  Message: {result['message']}")
            logger.info(f"  Records processed: {result['data_summary']['total_records']}")
            logger.info(f"  Stations: {result['data_summary']['stations_count']}")
            logger.info(f"  Years range: {result['data_summary']['years_range']}")
            logger.info(f"  Analysis grade: {result['analysis_grade']}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Frequency analysis failed: {e}")
            import traceback
            traceback.print_exc()
            return False
            
    except Exception as e:
        logger.error(f"❌ Test data creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(create_test_data())
    
    if success:
        print("\n🎉 Test data created successfully!")
        print("The frequency analysis system is now ready for testing.")
    else:
        print("\n❌ Test data creation failed.")
        sys.exit(1)