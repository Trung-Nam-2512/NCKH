#!/usr/bin/env python3
"""
Fix Database Integration - Ensure both services use the same data source
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

async def fix_database_integration():
    """Fix the database integration between API service and Realtime service"""
    
    logger.info("🔧 FIXING DATABASE INTEGRATION")
    logger.info("=" * 50)
    
    try:
        # Step 1: Collect and verify API data
        logger.info("\n📡 Step 1: Collecting and verifying API data...")
        api_service = APIServiceFactory.create_service()
        await api_service.initialize()
        
        # Get API data from correct database/collection
        api_db = api_service.database_manager.db
        api_collection = api_db.realtime_depth
        
        # Count documents
        api_count = await api_collection.count_documents({})
        logger.info(f"API collection documents: {api_count}")
        
        if api_count == 0:
            # Collect fresh data first
            logger.info("No API data found, collecting fresh data...")
            result = await api_service.collect_and_process_data()
            logger.info(f"Fresh data collection: {result.get('total_measurements', 0)} measurements")
            api_count = await api_collection.count_documents({})
        
        if api_count == 0:
            logger.error("❌ No data available from APIs")
            return False
        
        # Step 2: Initialize Realtime Service
        logger.info("\n🔄 Step 2: Initializing Realtime Service...")
        data_service = DataService()
        realtime_service = EnhancedRealtimeService(data_service)
        await realtime_service.initialize_database()
        
        realtime_db = realtime_service.db
        realtime_collection = realtime_db.realtime_data
        
        # Step 3: Transfer data from API collection to Realtime collection
        logger.info("\n🔄 Step 3: Transferring data between collections...")
        
        # Get all API data
        cursor = api_collection.find({})
        api_documents = await cursor.to_list(length=None)
        logger.info(f"Retrieved {len(api_documents)} documents from API collection")
        
        if api_documents:
            # Transform data format if needed
            transformed_docs = []
            for doc in api_documents:
                # Remove MongoDB _id to let realtime collection generate new ones
                if '_id' in doc:
                    del doc['_id']
                
                # Ensure required fields exist
                if all(field in doc for field in ['station_id', 'time_point', 'depth']):
                    transformed_docs.append(doc)
            
            logger.info(f"Transformed {len(transformed_docs)} documents for realtime collection")
            
            # Clear existing realtime data and insert new data
            await realtime_collection.delete_many({})
            
            if transformed_docs:
                await realtime_collection.insert_many(transformed_docs)
                logger.info(f"✅ Inserted {len(transformed_docs)} documents into realtime collection")
            
            # Step 4: Verify the data transfer
            logger.info("\n✅ Step 4: Verifying data transfer...")
            
            realtime_count = await realtime_collection.count_documents({})
            logger.info(f"Realtime collection now has: {realtime_count} documents")
            
            # Check realtime service stats
            stats = await realtime_service.get_realtime_stats()
            logger.info(f"Realtime service stats: {stats}")
            
            # Test frequency analysis capability
            logger.info("\n🧪 Step 5: Testing frequency analysis...")
            
            # Try with minimal requirements
            for min_years in [0, 1]:
                try:
                    freq_data = await realtime_service.get_frequency_ready_data(min_years=min_years)
                    logger.info(f"Frequency data (min_years={min_years}): {len(freq_data)} records")
                    
                    if len(freq_data) > 0:
                        logger.info(f"  Years available: {sorted(freq_data['Year'].unique())}")
                        logger.info(f"  Stations: {freq_data['station_id'].nunique()}")
                        logger.info(f"  Depth range: {freq_data['depth'].min():.3f} - {freq_data['depth'].max():.3f}")
                        
                        # Step 6: Test actual analysis
                        logger.info("\n🎯 Step 6: Testing historical analysis...")
                        from app.services.integration_service import IntegrationService
                        
                        integration_service = IntegrationService(data_service)
                        
                        try:
                            result = await integration_service.analyze_historical_realtime(
                                min_years=min_years,
                                distribution_name="gumbel",
                                agg_func="max",
                                use_professional=False
                            )
                            
                            logger.info("🎉 SUCCESS! Historical analysis working:")
                            logger.info(f"  Message: {result['message']}")
                            logger.info(f"  Records processed: {result['data_summary']['total_records']}")
                            logger.info(f"  Analysis grade: {result['analysis_grade']}")
                            
                            return True
                            
                        except Exception as e:
                            logger.warning(f"Analysis test failed: {e}")
                            continue
                        
                except Exception as e:
                    logger.warning(f"Error getting frequency data (min_years={min_years}): {e}")
                    continue
            
            logger.error("❌ All frequency analysis attempts failed")
            return False
            
        else:
            logger.error("❌ No documents retrieved from API collection")
            return False
            
    except Exception as e:
        logger.error(f"❌ Database integration fix failed: {e}")
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
    success = asyncio.run(fix_database_integration())
    
    if success:
        print("\n🎉 Database integration fixed successfully!")
        print("The /integration/analyze-historical endpoint should now work with proper data.")
    else:
        print("\n❌ Database integration fix failed.")
        print("Please check the logs for details.")
        sys.exit(1)