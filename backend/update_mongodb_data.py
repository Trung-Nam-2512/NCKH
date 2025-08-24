#!/usr/bin/env python3
"""
Update MongoDB data with more recent timestamps
"""
import asyncio
import random
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
import logging

logging.basicConfig(level=logging.INFO)

async def update_mongodb_data():
    """Update MongoDB data with recent timestamps"""
    
    # Connect to MongoDB
    client = AsyncIOMotorClient('mongodb://localhost:27017')
    db = client.hydro_db
    collection = db.realtime_depth
    
    # Generate recent data (last 7 days)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    
    # Station IDs from existing data
    station_ids = [
        "056882", "056883", "056884", "056885", "056886",
        "056887", "056888", "056889", "056890", "056891",
        "056892", "056893", "056894", "056895", "056896",
        "056897", "056898", "056899", "056900", "056901",
        "056902", "056903", "056904", "056905", "056906",
        "056907", "056908", "056909", "056910", "056911",
        "056912", "056913", "056914", "056915"
    ]
    
    # Generate data for each station
    documents = []
    current_date = start_date
    
    while current_date <= end_date:
        # Generate data for each hour between 05:00 and 23:00
        for hour in range(5, 24):
            for minute in range(0, 60, 10):  # Every 10 minutes
                time_point = current_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
                
                for station_id in station_ids:
                    # Generate realistic water level data
                    base_depth = random.uniform(0.1, 2.0)
                    # Add some variation based on time of day
                    time_variation = 0.1 * abs(hour - 14)  # Peak around 14:00
                    depth = max(0.05, base_depth + random.uniform(-0.2, 0.2) - time_variation)
                    
                    doc = {
                        'station_id': station_id,
                        'time_point': time_point,
                        'depth': round(depth, 3),
                        'created_at': datetime.utcnow()
                    }
                    documents.append(doc)
        
        current_date += timedelta(days=1)
    
    # Clear existing data and insert new data
    try:
        await collection.delete_many({})
        logging.info(f"✅ Cleared existing data")
        
        # Insert in batches
        batch_size = 1000
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            await collection.insert_many(batch)
            logging.info(f"✅ Inserted batch {i//batch_size + 1}/{(len(documents) + batch_size - 1)//batch_size}")
        
        logging.info(f"✅ Successfully updated {len(documents)} records")
        
        # Verify the update
        count = await collection.count_documents({})
        latest_record = await collection.find_one({}, sort=[('time_point', -1)])
        
        logging.info(f"📊 Total records in database: {count}")
        if latest_record:
            logging.info(f"🕐 Latest data timestamp: {latest_record['time_point']}")
        
    except Exception as e:
        logging.error(f"❌ Error updating data: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(update_mongodb_data()) 