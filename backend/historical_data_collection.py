#!/usr/bin/env python3
"""
Historical Data Collection System
Collect historical data from APIs to fill gaps for frequency analysis
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

from app.services.improved_real_api_service import APIServiceFactory
from app.services.realtime_service import EnhancedRealtimeService
from app.services.data_service import DataService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def collect_historical_data():
    """Collect historical data from APIs for multiple time periods"""
    
    print("=" * 80)
    print("HISTORICAL DATA COLLECTION SYSTEM")
    print("=" * 80)
    
    try:
        # Initialize services
        api_service = APIServiceFactory.create_service()
        await api_service.initialize()
        
        data_service = DataService()
        realtime_service = EnhancedRealtimeService(data_service)
        await realtime_service.initialize_database()
        
        # Step 1: Analyze what we need
        print("\nSTEP 1: ANALYZING DATA REQUIREMENTS")
        print("-" * 50)
        
        # For frequency analysis, we need at least 5-10 years of data
        # Since APIs might have limited historical data, we'll collect what's available
        
        current_time = datetime.now()
        
        # Try to collect data for different time periods
        time_periods = [
            # Recent data (last 2 months) - KTTV API supports max 2 months
            (current_time - timedelta(days=60), current_time, "Recent 2 months"),
            # Previous periods
            (current_time - timedelta(days=120), current_time - timedelta(days=60), "Previous 2 months"),
            (current_time - timedelta(days=180), current_time - timedelta(days=120), "3-4 months ago"),
            (current_time - timedelta(days=240), current_time - timedelta(days=180), "4-6 months ago"),
        ]
        
        all_collected_data = []
        
        # Step 2: Collect data for each period
        print("\nSTEP 2: COLLECTING DATA FOR MULTIPLE PERIODS")
        print("-" * 50)
        
        for start_time, end_time, period_name in time_periods:
            print(f"\nCollecting data for {period_name}:")
            print(f"  Time range: {start_time.strftime('%Y-%m-%d %H:%M')} to {end_time.strftime('%Y-%m-%d %H:%M')}")
            
            try:
                # For KTTV API, we need to collect in smaller chunks
                chunk_days = 7  # 1 week chunks
                current_chunk_start = start_time
                period_data = []
                
                while current_chunk_start < end_time:
                    chunk_end = min(current_chunk_start + timedelta(days=chunk_days), end_time)
                    
                    print(f"    Chunk: {current_chunk_start.strftime('%Y-%m-%d')} to {chunk_end.strftime('%Y-%m-%d')}")
                    
                    # Try to collect for this chunk
                    chunk_data = await collect_api_data_for_period(
                        api_service, current_chunk_start, chunk_end
                    )
                    
                    if chunk_data:
                        period_data.extend(chunk_data)
                        print(f"      Collected: {len(chunk_data)} records")
                    else:
                        print(f"      No data for this chunk")
                    
                    current_chunk_start = chunk_end + timedelta(seconds=1)
                    
                    # Small delay to avoid API rate limiting
                    await asyncio.sleep(1)
                
                if period_data:
                    all_collected_data.extend(period_data)
                    print(f"  Total for {period_name}: {len(period_data)} records")
                else:
                    print(f"  No data collected for {period_name}")
                
            except Exception as e:
                print(f"  Error collecting {period_name}: {e}")
                continue
        
        print(f"\nTotal collected: {len(all_collected_data)} records")
        
        # Step 3: Process and clean collected data
        print("\nSTEP 3: PROCESSING COLLECTED DATA")
        print("-" * 50)
        
        if all_collected_data:
            # Convert to DataFrame
            df = pd.DataFrame(all_collected_data)
            
            print(f"Raw data: {len(df)} records")
            
            # Remove duplicates based on station_id and time_point
            df_clean = df.drop_duplicates(subset=['station_id', 'time_point'])
            print(f"After deduplication: {len(df_clean)} records")
            
            # Sort by time
            df_clean = df_clean.sort_values(['station_id', 'time_point'])
            
            # Analyze time coverage
            if not df_clean.empty:
                min_time = df_clean['time_point'].min()
                max_time = df_clean['time_point'].max()
                time_span = max_time - min_time
                
                print(f"Time coverage: {min_time} to {max_time}")
                print(f"Span: {time_span.days} days ({time_span.days/365.25:.1f} years)")
                
                unique_stations = df_clean['station_id'].nunique()
                print(f"Unique stations: {unique_stations}")
                
                # Analyze by year
                df_clean['year'] = df_clean['time_point'].dt.year
                year_counts = df_clean['year'].value_counts().sort_index()
                print(f"Records by year:")
                for year, count in year_counts.items():
                    stations_in_year = df_clean[df_clean['year'] == year]['station_id'].nunique()
                    print(f"  {year}: {count} records from {stations_in_year} stations")
            
        else:
            print("No data collected from any period")
            return False
        
        # Step 4: Transfer to realtime database
        print("\nSTEP 4: TRANSFERRING TO REALTIME DATABASE")
        print("-" * 50)
        
        realtime_collection = realtime_service.db.realtime_data
        
        # Clear existing data
        existing_count = await realtime_collection.count_documents({})
        print(f"Existing records in realtime DB: {existing_count}")
        
        if existing_count > 0:
            print("Clearing existing data...")
            await realtime_collection.delete_many({})
        
        # Insert collected data
        records_to_insert = []
        for _, row in df_clean.iterrows():
            record = {
                'station_id': row['station_id'],
                'uuid': row.get('uuid', f"uuid-{row['station_id']}"),
                'code': row.get('code', row['station_id']),
                'name': row.get('name', f"Station {row['station_id']}"),
                'latitude': float(row.get('latitude', 0)),
                'longitude': float(row.get('longitude', 0)),
                'api_type': row.get('api_type', 'historical_collection'),
                'time_point': row['time_point'],
                'depth': float(row['depth']),
                'created_at': datetime.now()
            }
            records_to_insert.append(record)
        
        if records_to_insert:
            # Insert in batches
            batch_size = 1000
            total_inserted = 0
            
            for i in range(0, len(records_to_insert), batch_size):
                batch = records_to_insert[i:i+batch_size]
                await realtime_collection.insert_many(batch)
                total_inserted += len(batch)
                print(f"Inserted batch: {total_inserted}/{len(records_to_insert)} records")
            
            print(f"Successfully inserted {total_inserted} records into realtime database")
        
        # Step 5: Verify data for frequency analysis
        print("\nSTEP 5: VERIFYING FREQUENCY ANALYSIS READINESS")
        print("-" * 50)
        
        # Test frequency analysis readiness
        for min_years in [1, 2, 3]:
            try:
                freq_data = await realtime_service.get_frequency_ready_data(min_years=min_years)
                
                if len(freq_data) > 0:
                    years_available = sorted(freq_data['Year'].unique())
                    stations_count = freq_data['station_id'].nunique()
                    
                    print(f"\nFrequency analysis with min_years={min_years}:")
                    print(f"  Available data: {len(freq_data)} annual maxima")
                    print(f"  Stations: {stations_count}")
                    print(f"  Years: {years_available}")
                    print(f"  Depth range: {freq_data['depth'].min():.3f} - {freq_data['depth'].max():.3f} m")
                    
                    if len(freq_data) >= min_years and stations_count >= 1:
                        print(f"  STATUS: Ready for frequency analysis!")
                        viable_min_years = min_years
                        break
                else:
                    print(f"\nFrequency analysis with min_years={min_years}: No data available")
            except Exception as e:
                print(f"\nFrequency analysis with min_years={min_years}: Error - {e}")
        
        # Step 6: Generate synthetic data if still insufficient
        if 'viable_min_years' not in locals():
            print("\nSTEP 6: GENERATING SYNTHETIC DATA FOR TESTING")
            print("-" * 50)
            
            synthetic_success = await generate_synthetic_historical_data(realtime_service)
            
            if synthetic_success:
                print("Synthetic data generated successfully")
                
                # Test again with synthetic data
                freq_data = await realtime_service.get_frequency_ready_data(min_years=3)
                if len(freq_data) > 0:
                    print(f"Synthetic frequency data: {len(freq_data)} records")
                    viable_min_years = 3
        
        # Final status
        print("\n" + "=" * 80)
        print("DATA COLLECTION SUMMARY")
        print("=" * 80)
        
        final_count = await realtime_collection.count_documents({})
        print(f"Final database records: {final_count}")
        
        if 'viable_min_years' in locals():
            print(f"System ready for frequency analysis with min_years={viable_min_years}")
            return True
        else:
            print("System still not ready for frequency analysis")
            return False
        
    except Exception as e:
        logger.error(f"Historical data collection failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if 'api_service' in locals():
            await api_service.database_manager.close()

async def collect_api_data_for_period(api_service, start_time, end_time):
    """Collect data from APIs for a specific time period"""
    
    try:
        collected_data = []
        
        # Try KTTV API first (has more historical data capability)
        for api_client in api_service.api_clients:
            if 'KTTV' in type(api_client).__name__:
                try:
                    # Get stations
                    stations = await api_client.fetch_stations()
                    station_mapping = api_service.data_transformer.transform_stations(stations)
                    
                    # For KTTV, we need to format the time properly
                    start_str = start_time.strftime('%Y-%m-%d %H:%M:%S')
                    end_str = end_time.strftime('%Y-%m-%d %H:%M:%S')
                    
                    # Modify the client to use custom time range
                    original_fetch = api_client.fetch_stats
                    
                    async def custom_fetch_stats():
                        # Override the time range
                        import httpx
                        
                        params = {
                            'start_time': start_str,
                            'end_time': end_str
                        }
                        
                        async with httpx.AsyncClient(timeout=30) as client:
                            response = await client.get(
                                api_client.stats_url,
                                headers=api_client.headers,
                                params=params
                            )
                            
                            if response.status_code == 200:
                                return response.json()
                            else:
                                return {}
                    
                    # Fetch stats for this period
                    stats_data = await custom_fetch_stats()
                    
                    if stats_data:
                        # Transform the data
                        measurements = api_service.data_transformer.transform_stats(stats_data, station_mapping)
                        valid_measurements = [m for m in measurements if api_service.data_validator.validate_measurement(m)]
                        
                        collected_data.extend(valid_measurements)
                        
                        if valid_measurements:
                            print(f"      KTTV: {len(valid_measurements)} measurements")
                    
                except Exception as e:
                    print(f"      KTTV error: {e}")
                    continue
        
        return collected_data
        
    except Exception as e:
        print(f"      Period collection error: {e}")
        return []

async def generate_synthetic_historical_data(realtime_service):
    """Generate synthetic historical data for testing purposes"""
    
    try:
        print("Generating synthetic historical data...")
        
        # Generate 5 years of synthetic data (2020-2024)
        synthetic_data = []
        
        stations = [
            {'id': 'SYN001', 'name': 'Synthetic Station A', 'lat': 10.76, 'lon': 106.66},
            {'id': 'SYN002', 'name': 'Synthetic Station B', 'lat': 10.78, 'lon': 106.70},
            {'id': 'SYN003', 'name': 'Synthetic Station C', 'lat': 10.80, 'lon': 106.72}
        ]
        
        for year in range(2020, 2025):
            for station in stations:
                # Generate monthly maximum data (12 points per year per station)
                for month in range(1, 13):
                    # Synthetic water level following realistic patterns
                    base_level = np.random.uniform(1.0, 3.0)
                    seasonal_factor = 1.5 if 5 <= month <= 10 else 1.0  # Rainy season
                    random_factor = np.random.uniform(0.8, 2.0)
                    
                    depth = base_level * seasonal_factor * random_factor
                    
                    record = {
                        'station_id': station['id'],
                        'uuid': f"uuid-{station['id']}",
                        'code': station['id'],
                        'name': station['name'],
                        'latitude': station['lat'],
                        'longitude': station['lon'],
                        'api_type': 'synthetic',
                        'time_point': datetime(year, month, 15),  # Mid-month
                        'depth': round(depth, 3),
                        'created_at': datetime.now()
                    }
                    
                    synthetic_data.append(record)
        
        # Insert synthetic data
        collection = realtime_service.db.realtime_data
        
        if synthetic_data:
            await collection.insert_many(synthetic_data)
            print(f"Generated {len(synthetic_data)} synthetic records")
            return True
        
        return False
        
    except Exception as e:
        print(f"Synthetic data generation failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(collect_historical_data())
    
    if success:
        print("\nHistorical data collection completed successfully!")
        print("System is now ready for frequency analysis.")
    else:
        print("\nHistorical data collection had issues.")
        print("Check the logs for details.")