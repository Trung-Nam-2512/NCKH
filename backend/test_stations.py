#!/usr/bin/env python3
"""
Test script to check MongoDB collections and stations data
"""
import asyncio
import logging
from app.services.realtime_service import EnhancedRealtimeService

async def test_stations():
    try:
        service = EnhancedRealtimeService()
        await service.initialize_database()
        
        # List databases
        databases = await service.client.list_database_names()
        print(f"Databases found: {databases}")
        
        # List collections in current database
        collections = await service.db.list_collection_names()
        print(f"Collections in current database: {collections}")
        
        # Check water_level_db database
        water_db = service.client.water_level_db
        water_collections = await water_db.list_collection_names()
        print(f"Collections in water_level_db: {water_collections}")
        
        # Check hydro_db database
        hydro_db = service.client.hydro_db
        hydro_collections = await hydro_db.list_collection_names()
        print(f"Collections in hydro_db: {hydro_collections}")
        
        # Check all collections in hydro_db
        for collection_name in hydro_collections:
            count = await hydro_db[collection_name].count_documents({})
            print(f"Collection '{collection_name}' in hydro_db has {count} documents")
            
            if count > 0:
                sample = await hydro_db[collection_name].find_one()
                print(f"Sample from '{collection_name}': {sample}")
        
        # Check all collections in water_level_db
        for collection_name in water_collections:
            count = await water_db[collection_name].count_documents({})
            print(f"Collection '{collection_name}' in water_level_db has {count} documents")
            
            if count > 0:
                sample = await water_db[collection_name].find_one()
                print(f"Sample from '{collection_name}': {sample}")
        
        # Check all collections in current database
        for collection_name in collections:
            count = await service.db[collection_name].count_documents({})
            print(f"Collection '{collection_name}' has {count} documents")
            
            if count > 0:
                sample = await service.db[collection_name].find_one()
                print(f"Sample from '{collection_name}': {sample}")
        
        # Check realtime_data collection specifically
        if 'realtime_data' in collections:
            count = await service.db.realtime_data.count_documents({})
            print(f"realtime_data collection has {count} documents")
            
            # Get sample data
            sample = await service.db.realtime_data.find_one()
            if sample:
                print(f"Sample document: {sample}")
            else:
                print("No documents found in realtime_data")
        else:
            print("realtime_data collection not found")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_stations()) 