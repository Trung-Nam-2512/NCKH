#!/usr/bin/env python3
"""
Fix Data Integration - Transfer API data to Realtime Service format
"""
import asyncio
import sys
import os
import logging
from datetime import datetime
import pandas as pd

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
sys.path.append(os.path.dirname(__file__))

from app.services.improved_real_api_service import APIServiceFactory
from app.services.realtime_service import EnhancedRealtimeService
from app.services.data_service import DataService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def fix_data_integration():
    """Fix the data integration between API service and Realtime service"""
    
    logger.info("🔧 FIXING DATA INTEGRATION")
    logger.info("=" * 50)
    
    try:
        # Step 1: Collect fresh data from APIs
        logger.info("\n📡 Step 1: Collecting data from APIs...")
        api_service = APIServiceFactory.create_service()
        
        # Initialize the API service but keep connection open
        await api_service.initialize()
        
        # Collect data without closing connection
        api_result = {
            'success': True,
            'total_measurements': 0,
            'total_stations': 0,
            'api_summary': {}
        }
        
        all_measurements = []
        
        # Process each API client
        for api_client in api_service.api_clients:
            try:
                logger.info(f"Processing {type(api_client).__name__}...")
                
                stations = await api_client.fetch_stations()
                station_mapping = api_service.data_transformer.transform_stations(stations)
                api_service.station_mapping.update(station_mapping)
                
                stats = await api_client.fetch_stats()
                measurements = api_service.data_transformer.transform_stats(stats, station_mapping)
                
                valid_measurements = [m for m in measurements if api_service.data_validator.validate_measurement(m)]
                all_measurements.extend(valid_measurements)
                
                api_result['api_summary'][type(api_client).__name__] = {
                    'success': True,
                    'stations': len(station_mapping),
                    'valid_measurements': len(valid_measurements)
                }
                
            except Exception as e:
                logger.error(f"Error processing {type(api_client).__name__}: {e}")
                api_result['api_summary'][type(api_client).__name__] = {
                    'success': False,
                    'error': str(e)
                }
        
        # Store measurements
        if all_measurements:
            await api_service.database_manager.store_measurements(all_measurements)
            api_result.update({
                'total_measurements': len(all_measurements),
                'total_stations': len(api_service.station_mapping)
            })
        
        logger.info(f"✅ API Collection completed:")
        logger.info(f"   Success: {api_result['success']}")
        logger.info(f"   Total measurements: {api_result.get('total_measurements', 0)}")
        logger.info(f"   Total stations: {api_result.get('total_stations', 0)}")
        
        if not api_result['success'] or api_result.get('total_measurements', 0) == 0:
            logger.warning("⚠️ No data collected from APIs")
            return False
        
        # Step 2: Initialize realtime service
        logger.info("\n🔄 Step 2: Initializing Realtime Service...")
        data_service = DataService()
        realtime_service = EnhancedRealtimeService(data_service)
        await realtime_service.initialize_database()
        
        # Step 3: Get the API data and transform it for realtime service
        logger.info("\n🔄 Step 3: Transforming data for Realtime Service...")
        
        # Access the API service's database directly
        api_db = api_service.database_manager.db.realtime_depth  # Correct collection name
        
        # Get all the recent data
        cursor = api_db.find({}).sort('time_point', -1).limit(1000)
        api_documents = await cursor.to_list(length=1000)
        
        if api_documents:
            logger.info(f"📊 Found {len(api_documents)} documents in API collection")
            
            # Convert to DataFrame for easier manipulation
            df = pd.DataFrame(api_documents)
            
            # Add Year column if not present
            if 'time_point' in df.columns:
                df['time_point'] = pd.to_datetime(df['time_point'])
                df['Year'] = df['time_point'].dt.year
                
            logger.info(f"📅 Data spans years: {df['Year'].min()} to {df['Year'].max()}")
            logger.info(f"📍 Stations: {df['station_id'].nunique()}")
            logger.info(f"📏 Depth range: {df['depth'].min():.3f} to {df['depth'].max():.3f}")
            
            # Step 4: Integrate data into realtime service
            logger.info("\n🔗 Step 4: Integrating data into Realtime Service...")
            await realtime_service.integrate_to_analysis(df)
            
            # Step 5: Verify the integration
            logger.info("\n✅ Step 5: Verifying integration...")
            stats = await realtime_service.get_realtime_stats()
            
            logger.info(f"🔍 Realtime Service Stats after integration:")
            logger.info(f"   Total records: {stats.get('total_records', 0)}")
            logger.info(f"   Active stations: {stats.get('stations_count', 0)}")
            logger.info(f"   Date range: {stats.get('date_range', {})}")
            
            # Test frequency analysis capability
            freq_data = await realtime_service.get_frequency_ready_data(min_years=1)
            logger.info(f"   Frequency-ready records: {len(freq_data)}")
            
            if len(freq_data) > 0:
                logger.info(f"   Years available for analysis: {sorted(freq_data['Year'].unique())}")
                
                # Step 6: Test the historical analysis
                logger.info("\n🧪 Step 6: Testing Historical Analysis...")
                from app.services.integration_service import IntegrationService
                
                integration_service = IntegrationService(data_service)
                
                try:
                    result = await integration_service.analyze_historical_realtime(
                        min_years=1,
                        distribution_name="gumbel",
                        agg_func="max",
                        use_professional=False  # Use standard due to limited data
                    )
                    
                    logger.info("🎉 SUCCESS! Historical analysis working:")
                    logger.info(f"   Message: {result['message']}")
                    logger.info(f"   Total records: {result['data_summary']['total_records']}")
                    logger.info(f"   Analysis grade: {result['analysis_grade']}")
                    return True
                    
                except Exception as e:
                    logger.error(f"❌ Historical analysis still failing: {e}")
                    return False
            else:
                logger.warning("⚠️ No frequency-ready data after integration")
                return False
        else:
            logger.warning("⚠️ No documents found in API collection")
            return False
            
    except Exception as e:
        logger.error(f"❌ Data integration fix failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Cleanup connections
        try:
            if 'api_service' in locals():
                await api_service.database_manager.close()
        except:
            pass

if __name__ == "__main__":
    success = asyncio.run(fix_data_integration())
    
    if success:
        print("\n🎉 Data integration fixed successfully!")
        print("The /integration/analyze-historical endpoint should now work.")
    else:
        print("\n❌ Data integration fix failed.")
        print("Please check the logs for details.")
        sys.exit(1)