#!/usr/bin/env python3
"""
Enhanced Realtime Service with Quality Control and High-Frequency Data Optimization
- QC: Outlier detection, missing data handling
- Aggregation: Downsampling for frequency analysis
- Multi-station optimization
"""
import asyncio
import logging
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import pandas as pd
import numpy as np
import httpx
from motor.motor_asyncio import AsyncIOMotorClient
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential

load_dotenv()

class EnhancedRealtimeService:
    def __init__(self, data_service=None):
        self.mongo_uri = os.getenv('MONGODB_URI', 'mongodb://localhost:27017')
        self.api_base_url = os.getenv('API_BASE_URL')
        self.api_key = os.getenv('API_KEY')
        self.client = None
        self.db = None
        self.scheduler = AsyncIOScheduler()
        
        # QC Parameters
        self.z_score_threshold = 3.0  # Outlier detection threshold
        self.max_depth_threshold = 10.0  # Maximum reasonable depth (m)
        self.min_depth_threshold = -1.0  # Minimum reasonable depth (m)
        
        # Aggregation parameters
        self.downsample_intervals = ['hourly', 'daily', 'monthly']
        
        # Initialize improved API service following SOLID principles  
        try:
            from .improved_real_api_service import APIServiceFactory
            self.improved_api_service = APIServiceFactory.create_service()
        except ImportError as e:
            logging.warning(f"⚠️ Could not import improved API service: {e}")
            self.improved_api_service = None
        
    async def initialize_database(self):
        """Initialize MongoDB connection with optimized indexes"""
        try:
            self.client = AsyncIOMotorClient(self.mongo_uri)
            self.db = self.client.water_level_db
            
            # Create optimized indexes for high-frequency data
            await self.db.realtime_data.create_index([
                ("station_id", 1),
                ("time_point", -1)
            ])
            
            # Note: Removed TTL index for frequency analysis
            # Historical data is crucial for hydrological frequency analysis
            # Data retention should be managed manually based on storage capacity
            logging.info("ℹ️ TTL index removed - preserving historical data for frequency analysis")
            
            # Index for aggregation queries
            await self.db.realtime_data.create_index([
                ("station_id", 1),
                ("time_point", 1),
                ("depth", 1)
            ])
            
            logging.info("✅ Database initialized with optimized indexes")
            
        except Exception as e:
            logging.error(f"❌ Database initialization failed: {e}")
            raise

    def apply_quality_control(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Apply Quality Control to real-time data
        - Remove outliers using Z-score
        - Handle missing values
        - Validate depth ranges
        """
        if df.empty:
            return df
            
        original_count = len(df)
        
        # 1. Remove extreme outliers (beyond reasonable range)
        df = df[
            (df['depth'] >= self.min_depth_threshold) & 
            (df['depth'] <= self.max_depth_threshold)
        ]
        
        # 2. Z-score outlier detection (for each station separately)
        df_clean = pd.DataFrame()
        
        for station_id in df['station_id'].unique():
            station_data = df[df['station_id'] == station_id].copy()
            
            if len(station_data) > 10:  # Need enough data for Z-score
                # Calculate Z-score for depth
                mean_depth = station_data['depth'].mean()
                std_depth = station_data['depth'].std()
                
                if std_depth > 0:
                    z_scores = np.abs((station_data['depth'] - mean_depth) / std_depth)
                    station_data = station_data[z_scores <= self.z_score_threshold]
            
            df_clean = pd.concat([df_clean, station_data], ignore_index=True)
        
        # 3. Handle missing time points by interpolation
        df_clean = self._interpolate_missing_times(df_clean)
        
        # 4. Final validation
        df_clean = df_clean.dropna(subset=['depth', 'time_point'])
        
        removed_count = original_count - len(df_clean)
        if removed_count > 0:
            logging.info(f"🧹 QC removed {removed_count} records ({removed_count/original_count*100:.1f}%)")
        
        return df_clean

    def _interpolate_missing_times(self, df: pd.DataFrame) -> pd.DataFrame:
        """Interpolate missing time points for each station"""
        if df.empty:
            return df
            
        df_interpolated = pd.DataFrame()
        
        for station_id in df['station_id'].unique():
            station_data = df[df['station_id'] == station_id].copy()
            
            if len(station_data) > 1:
                # Sort by time
                station_data = station_data.sort_values('time_point')
                
                # Create complete time series (every 10 minutes)
                start_time = station_data['time_point'].min()
                end_time = station_data['time_point'].max()
                
                complete_times = pd.date_range(
                    start=start_time, 
                    end=end_time, 
                    freq='10T'  # 10 minutes
                )
                
                # Reindex and interpolate
                station_data = station_data.set_index('time_point').reindex(complete_times)
                station_data['depth'] = station_data['depth'].interpolate(method='linear')
                station_data['station_id'] = station_id
                station_data = station_data.reset_index().rename(columns={'index': 'time_point'})
            
            df_interpolated = pd.concat([df_interpolated, station_data], ignore_index=True)
        
        return df_interpolated

    def downsample_for_frequency_analysis(self, df: pd.DataFrame, interval: str = 'daily') -> pd.DataFrame:
        """
        Downsample high-frequency data for frequency analysis
        - Reduces data size while preserving peak values
        - Optimizes for statistical analysis
        """
        if df.empty:
            return df
            
        df_downsampled = pd.DataFrame()
        
        for station_id in df['station_id'].unique():
            station_data = df[df['station_id'] == station_id].copy()
            
            if len(station_data) > 0:
                station_data = station_data.set_index('time_point')
                
                if interval == 'hourly':
                    # Aggregate to hourly max
                    resampled = station_data.resample('H').agg({
                        'depth': 'max',
                        'station_id': 'first'
                    })
                elif interval == 'daily':
                    # Aggregate to daily max
                    resampled = station_data.resample('D').agg({
                        'depth': 'max',
                        'station_id': 'first'
                    })
                elif interval == 'monthly':
                    # Aggregate to monthly max
                    resampled = station_data.resample('M').agg({
                        'depth': 'max',
                        'station_id': 'first'
                    })
                else:
                    resampled = station_data
                
                resampled = resampled.reset_index()
                df_downsampled = pd.concat([df_downsampled, resampled], ignore_index=True)
        
        logging.info(f"📊 Downsampled to {interval} intervals: {len(df)} → {len(df_downsampled)} records")
        return df_downsampled

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def fetch_water_level(self, start_time: str, end_time: str) -> dict:
        """
        Enhanced fetch with better error handling and QC
        """
        try:
            # Format time according to API rules (05:00-23:00 daily)
            start_dt = datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')
            end_dt = datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S')
            
            # Ensure time is within daily range
            start_time_formatted = start_dt.strftime('%Y-%m-%d 05:00:00')
            end_time_formatted = end_dt.strftime('%Y-%m-%d 23:00:00')
            
            url = f"{self.api_base_url}/stats"
            params = {
                'start_time': start_time_formatted,
                'end_time': end_time_formatted,
                'api_key': self.api_key
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                
                data = response.json()
                
                # Apply QC to raw data
                if 'data' in data:
                    for station in data['data']:
                        if 'value' in station:
                            df_station = pd.DataFrame(station['value'])
                            df_station['station_id'] = station['station_id']
                            
                            # Apply QC
                            df_clean = self.apply_quality_control(df_station)
                            
                            # Update the data with cleaned values
                            station['value'] = df_clean.to_dict('records')
                
                logging.info(f"✅ Fetched and QC'd data: {start_time} to {end_time}")
                return data
                
        except httpx.HTTPStatusError as e:
            logging.error(f"❌ HTTP error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logging.error(f"❌ Fetch error: {e}")
            raise

    async def process_and_store_data(self, raw_data: dict, downsample_interval: str = 'daily') -> pd.DataFrame:
        """
        Enhanced data processing with QC and downsampling
        """
        try:
            # Convert to DataFrame
            all_records = []
            for station in raw_data.get('data', []):
                station_id = station.get('station_id')
                for record in station.get('value', []):
                    record['station_id'] = station_id
                    all_records.append(record)
            
            if not all_records:
                logging.warning("⚠️ No data to process")
                return pd.DataFrame()
            
            df = pd.DataFrame(all_records)
            df['time_point'] = pd.to_datetime(df['time_point'])
            
            # Apply QC
            df_clean = self.apply_quality_control(df)
            
            # Downsample for frequency analysis
            df_downsampled = self.downsample_for_frequency_analysis(df_clean, downsample_interval)
            
            # Store in MongoDB with batch insert
            if not df_downsampled.empty:
                await self._batch_insert_to_mongodb(df_downsampled)
            
            logging.info(f"✅ Processed and stored {len(df_downsampled)} records")
            return df_downsampled
            
        except Exception as e:
            logging.error(f"❌ Processing error: {e}")
            raise

    async def _batch_insert_to_mongodb(self, df: pd.DataFrame):
        """Optimized batch insert to MongoDB"""
        try:
            # Convert DataFrame to documents
            documents = []
            for _, row in df.iterrows():
                doc = {
                    'station_id': row['station_id'],
                    'time_point': row['time_point'],
                    'depth': float(row['depth']),
                    'created_at': datetime.utcnow()
                }
                documents.append(doc)
            
            # Batch insert
            if documents:
                result = await self.db.realtime_data.insert_many(documents, ordered=False)
                logging.info(f"📥 Batch inserted {len(result.inserted_ids)} documents")
                
        except Exception as e:
            logging.error(f"❌ MongoDB insert error: {e}")
            raise

    async def get_station_statistics(self, station_id: str = None, 
                                   start_time: datetime = None, 
                                   end_time: datetime = None) -> dict:
        """
        Enhanced statistics with QC metrics
        """
        try:
            # Build aggregation pipeline
            match_conditions = {}
            if station_id:
                match_conditions['station_id'] = station_id
            if start_time:
                match_conditions['time_point'] = {'$gte': start_time}
            if end_time:
                if 'time_point' in match_conditions:
                    match_conditions['time_point']['$lte'] = end_time
                else:
                    match_conditions['time_point'] = {'$lte': end_time}
            
            pipeline = [
                {'$match': match_conditions} if match_conditions else {'$match': {}},
                {
                    '$group': {
                        '_id': '$station_id',
                        'count': {'$sum': 1},
                        'avg_depth': {'$avg': '$depth'},
                        'max_depth': {'$max': '$depth'},
                        'min_depth': {'$min': '$depth'},
                        'std_depth': {'$stdDevPop': '$depth'},
                        'first_time': {'$min': '$time_point'},
                        'last_time': {'$max': '$time_point'}
                    }
                }
            ]
            
            results = await self.db.realtime_data.aggregate(pipeline).to_list(None)
            
            # Calculate QC metrics
            for result in results:
                station_id = result['_id']
                
                # Get recent data for QC analysis
                recent_data = await self.db.realtime_data.find(
                    {'station_id': station_id},
                    {'depth': 1, 'time_point': 1}
                ).sort('time_point', -1).limit(100).to_list(None)
                
                if recent_data:
                    depths = [doc['depth'] for doc in recent_data]
                    
                    # Calculate Z-score outliers
                    mean_depth = np.mean(depths)
                    std_depth = np.std(depths)
                    if std_depth > 0:
                        z_scores = [abs((d - mean_depth) / std_depth) for d in depths]
                        outliers = sum(1 for z in z_scores if z > self.z_score_threshold)
                        result['outlier_percentage'] = (outliers / len(depths)) * 100
                    else:
                        result['outlier_percentage'] = 0
                    
                    # Data completeness
                    result['data_completeness'] = len(recent_data) / 100 * 100  # Assuming 100 is expected
                
            return {
                'stations': results,
                'total_stations': len(results),
                'qc_thresholds': {
                    'z_score_threshold': self.z_score_threshold,
                    'max_depth_threshold': self.max_depth_threshold,
                    'min_depth_threshold': self.min_depth_threshold
                }
            }
            
        except Exception as e:
            logging.error(f"❌ Statistics error: {e}")
            raise

    async def get_storage_statistics(self) -> dict:
        """
        Get storage statistics for data retention planning
        - Important for frequency analysis which requires decades of data
        """
        try:
            # Get total data size
            total_docs = await self.db.realtime_data.count_documents({})
            
            # Get data by year for retention analysis
            pipeline = [
                {
                    '$addFields': {
                        'year': {'$year': '$time_point'}
                    }
                },
                {
                    '$group': {
                        '_id': '$year',
                        'count': {'$sum': 1},
                        'stations': {'$addToSet': '$station_id'}
                    }
                },
                {
                    '$sort': {'_id': -1}
                }
            ]
            
            yearly_stats = await self.db.realtime_data.aggregate(pipeline).to_list(None)
            
            # Calculate storage requirements
            estimated_size_per_record = 0.001  # MB per record (approximate)
            total_size_mb = total_docs * estimated_size_per_record
            
            return {
                'total_records': total_docs,
                'total_size_mb': round(total_size_mb, 2),
                'total_size_gb': round(total_size_mb / 1024, 2),
                'yearly_breakdown': yearly_stats,
                'retention_recommendation': {
                    'minimum_years': 30,  # Minimum for reliable frequency analysis
                    'optimal_years': 50,   # Optimal for hydrological studies
                    'storage_requirement_gb': round(total_size_mb / 1024 * 50, 2)  # 50 years estimate
                }
            }
            
        except Exception as e:
            logging.error(f"❌ Storage statistics error: {e}")
            raise

    async def manual_data_cleanup(self, years_to_keep: int = 50, 
                                dry_run: bool = True) -> dict:
        """
        Manual data cleanup for storage management
        - CRITICAL: Only use after careful consideration
        - Frequency analysis requires decades of historical data
        - Recommended minimum: 30 years, optimal: 50+ years
        
        Args:
            years_to_keep: Number of years to preserve
            dry_run: If True, only show what would be deleted
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=years_to_keep * 365)
            
            if dry_run:
                # Count records that would be deleted
                count_to_delete = await self.db.realtime_data.count_documents({
                    'time_point': {'$lt': cutoff_date}
                })
                
                # Get sample of oldest records
                oldest_records = await self.db.realtime_data.find({
                    'time_point': {'$lt': cutoff_date}
                }).sort('time_point', 1).limit(5).to_list(None)
                
                return {
                    'action': 'dry_run',
                    'years_to_keep': years_to_keep,
                    'cutoff_date': cutoff_date.isoformat(),
                    'records_to_delete': count_to_delete,
                    'oldest_records_sample': oldest_records,
                    'warning': f'⚠️ This would delete {count_to_delete} records older than {years_to_keep} years',
                    'recommendation': 'Consider storage expansion instead of data deletion for frequency analysis'
                }
            else:
                # Actually delete the records
                result = await self.db.realtime_data.delete_many({
                    'time_point': {'$lt': cutoff_date}
                })
                
                logging.warning(f"🗑️ Manually deleted {result.deleted_count} records older than {years_to_keep} years")
                
                return {
                    'action': 'deleted',
                    'years_to_keep': years_to_keep,
                    'cutoff_date': cutoff_date.isoformat(),
                    'deleted_count': result.deleted_count,
                    'warning': '⚠️ Historical data has been permanently deleted'
                }
                
        except Exception as e:
            logging.error(f"❌ Manual cleanup error: {e}")
            raise

    async def backup_historical_data(self, backup_path: str = None) -> dict:
        """
        Backup historical data before any cleanup operations
        - Essential for preserving data for frequency analysis
        """
        try:
            if not backup_path:
                backup_path = f"historical_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            # Get all historical data
            all_data = await self.db.realtime_data.find({}).to_list(None)
            
            # Convert to JSON-serializable format
            backup_data = []
            for doc in all_data:
                backup_data.append({
                    'station_id': doc['station_id'],
                    'time_point': doc['time_point'].isoformat(),
                    'depth': doc['depth'],
                    'created_at': doc['created_at'].isoformat() if 'created_at' in doc else None
                })
            
            # Save to file
            import json
            with open(backup_path, 'w') as f:
                json.dump(backup_data, f, indent=2)
            
            logging.info(f"💾 Historical data backed up to {backup_path}")
            
            return {
                'backup_path': backup_path,
                'records_backed_up': len(backup_data),
                'file_size_mb': round(len(json.dumps(backup_data)) / 1024 / 1024, 2)
            }
            
        except Exception as e:
            logging.error(f"❌ Backup error: {e}")
            raise

    async def setup_auto_poll(self):
        """Enhanced auto-polling with QC monitoring"""
        try:
            # Daily data collection (05:00-23:00)
            self.scheduler.add_job(
                self._daily_data_collection,
                CronTrigger(hour=6, minute=0),  # Run at 6 AM to collect previous day
                id='daily_collection',
                name='Daily Water Level Collection'
            )
            
            # Weekly full history refresh
            self.scheduler.add_job(
                self._weekly_full_refresh,
                CronTrigger(day_of_week='sun', hour=2, minute=0),
                id='weekly_refresh',
                name='Weekly Full History Refresh'
            )
            
            # QC monitoring (every 6 hours)
            self.scheduler.add_job(
                self._qc_monitoring,
                CronTrigger(hour='*/6'),
                id='qc_monitoring',
                name='Quality Control Monitoring'
            )
            
            self.scheduler.start()
            logging.info("✅ Enhanced auto-polling scheduler started")
            
        except Exception as e:
            logging.error(f"❌ Scheduler setup error: {e}")
            raise

    async def _daily_data_collection(self):
        """Collect yesterday's data with QC"""
        try:
            yesterday = datetime.now() - timedelta(days=1)
            start_time = yesterday.strftime('%Y-%m-%d 05:00:00')
            end_time = yesterday.strftime('%Y-%m-%d 23:00:00')
            
            raw_data = await self.fetch_water_level(start_time, end_time)
            await self.process_and_store_data(raw_data, 'daily')
            
            logging.info(f"✅ Daily collection completed for {yesterday.date()}")
            
        except Exception as e:
            logging.error(f"❌ Daily collection error: {e}")

    async def _weekly_full_refresh(self):
        """Weekly full history refresh with QC"""
        try:
            # Collect last 2 months of data (for real-time monitoring)
            # Note: Historical data beyond 2 months should be preserved
            # and managed separately for long-term frequency analysis
            end_date = datetime.now()
            start_date = end_date - timedelta(days=60)
            
            current_date = start_date
            while current_date <= end_date:
                start_time = current_date.strftime('%Y-%m-%d 05:00:00')
                end_time = current_date.strftime('%Y-%m-%d 23:00:00')
                
                try:
                    raw_data = await self.fetch_water_level(start_time, end_time)
                    await self.process_and_store_data(raw_data, 'daily')
                    logging.info(f"✅ Refreshed data for {current_date.date()}")
                except Exception as e:
                    logging.error(f"❌ Failed to refresh {current_date.date()}: {e}")
                
                current_date += timedelta(days=1)
                await asyncio.sleep(1)  # Rate limiting
            
            logging.info("✅ Weekly full refresh completed")
            
        except Exception as e:
            logging.error(f"❌ Weekly refresh error: {e}")

    async def _qc_monitoring(self):
        """Monitor data quality and alert on issues"""
        try:
            stats = await self.get_station_statistics()
            
            # Check for quality issues
            issues = []
            for station in stats['stations']:
                if station.get('outlier_percentage', 0) > 10:  # More than 10% outliers
                    issues.append(f"Station {station['_id']}: {station['outlier_percentage']:.1f}% outliers")
                
                if station.get('data_completeness', 100) < 80:  # Less than 80% complete
                    issues.append(f"Station {station['_id']}: {station['data_completeness']:.1f}% complete")
            
            if issues:
                logging.warning(f"⚠️ QC Issues detected: {', '.join(issues)}")
            else:
                logging.info("✅ QC monitoring: All stations healthy")
                
        except Exception as e:
            logging.error(f"❌ QC monitoring error: {e}")

    async def start(self):
        """Start the enhanced realtime service"""
        await self.initialize_database()
        await self.setup_auto_poll()
        logging.info("🚀 Enhanced Realtime Service started")

    async def stop(self):
        """Stop the service"""
        if self.scheduler.running:
            self.scheduler.shutdown()
        if self.client:
            self.client.close()
        logging.info("🛑 Enhanced Realtime Service stopped")
    
    async def get_frequency_ready_data(self, station_id: Optional[str] = None, min_years: int = 5) -> pd.DataFrame:
        """Get data ready for frequency analysis with adaptive minimum years logic"""
        try:
            # Ensure database connection
            if not self.client:
                await self.initialize_database()
            
            # Build query
            match_conditions = {}
            if station_id:
                match_conditions['station_id'] = station_id
            
            # Try adaptive approach: start with min_years, then reduce if no data found
            for attempt_years in [min_years, max(1, min_years // 2), 1]:
                cutoff_date = datetime.now() - timedelta(days=attempt_years * 365)
                match_conditions['time_point'] = {'$gte': cutoff_date}
                
                # Aggregation pipeline for annual maxima
                pipeline = [
                    {'$match': match_conditions},
                    {
                        '$addFields': {
                            'year': {'$year': '$time_point'}
                        }
                    },
                    {
                        '$group': {
                            '_id': {
                                'station_id': '$station_id',
                                'year': '$year'
                            },
                            'max_depth': {'$max': '$depth'},
                            'station_name': {'$first': '$name'},
                            'latitude': {'$first': '$latitude'},
                            'longitude': {'$first': '$longitude'}
                        }
                    },
                    {
                        '$group': {
                            '_id': '$_id.station_id',
                            'station_name': {'$first': '$station_name'},
                            'latitude': {'$first': '$latitude'},
                            'longitude': {'$first': '$longitude'},
                            'annual_maxima': {
                                '$push': {
                                    'year': '$_id.year',
                                    'max_depth': '$max_depth'
                                }
                            },
                            'years_count': {'$sum': 1}
                        }
                    },
                    {
                        '$match': {
                            'years_count': {'$gte': max(1, attempt_years)}
                        }
                    }
                ]
                
                # Use the correct collection name
                collection = self.db.realtime_data
                results = await collection.aggregate(pipeline).to_list(None)
                
                if results:
                    logging.info(f"✅ Found data with {attempt_years} year(s) threshold")
                    break
                else:
                    logging.warning(f"⚠️ No data with {attempt_years} year(s) threshold, trying lower...")
            
            # Convert to frequency analysis format
            rows = []
            for station_result in results:
                station_id_result = station_result['_id']
                station_name = station_result.get('station_name', f'Station {station_id_result}')
                latitude = station_result.get('latitude', 0)
                longitude = station_result.get('longitude', 0)
                
                for annual_data in station_result['annual_maxima']:
                    rows.append({
                        'station_id': station_id_result,
                        'station_name': station_name,
                        'latitude': latitude,
                        'longitude': longitude,
                        'Year': annual_data['year'],
                        'depth': annual_data['max_depth']
                    })
            
            df = pd.DataFrame(rows)
            
            if not df.empty:
                years_span = df['Year'].max() - df['Year'].min() + 1
                logging.info(f"📊 Frequency-ready data: {len(df)} annual maxima from {df['station_id'].nunique()} stations")
                logging.info(f"📅 Year range: {df['Year'].min()} - {df['Year'].max()} ({years_span} years)")
                
                # Add quality warning for short time series
                if years_span < 10:
                    logging.warning(f"⚠️ Short time series ({years_span} years) - results may have higher uncertainty")
                elif years_span < 30:
                    logging.info(f"ℹ️ Moderate time series ({years_span} years) - acceptable for preliminary analysis")
                else:
                    logging.info(f"✅ Long time series ({years_span} years) - excellent for robust analysis")
            else:
                logging.warning(f"⚠️ No annual maxima data found, attempting alternative approach...")
                # Final fallback: get any available data and create pseudo-annual maxima
                alt_df = await self._get_alternative_data_for_analysis(station_id)
                if not alt_df.empty:
                    logging.info(f"📊 Using alternative data: {len(alt_df)} records")
                    return alt_df
            
            return df
            
        except Exception as e:
            logging.error(f"❌ Error getting frequency-ready data: {e}")
            return pd.DataFrame()
    
    async def _get_recent_data_for_analysis(self, station_id: Optional[str] = None) -> pd.DataFrame:
        """Get recent data when historical data is insufficient"""
        try:
            match_conditions = {}
            if station_id:
                match_conditions['station_id'] = station_id
            
            # Get last 30 days of data
            cutoff_date = datetime.now() - timedelta(days=30)
            match_conditions['time_point'] = {'$gte': cutoff_date}
            
            collection = self.db.realtime_data
            cursor = collection.find(match_conditions).sort('time_point', -1).limit(1000)
            results = await cursor.to_list(None)
            
            rows = []
            for doc in results:
                rows.append({
                    'station_id': doc['station_id'],
                    'station_name': doc.get('name', 'Unknown'),
                    'latitude': doc.get('latitude', 0),
                    'longitude': doc.get('longitude', 0),
                    'Year': doc['time_point'].year,
                    'depth': doc['depth']
                })
            
            return pd.DataFrame(rows)
            
        except Exception as e:
            logging.error(f"❌ Error getting recent data: {e}")
            return pd.DataFrame()
    
    async def _get_alternative_data_for_analysis(self, station_id: Optional[str] = None) -> pd.DataFrame:
        """Get any available data and convert to pseudo-annual maxima format"""
        try:
            match_conditions = {}
            if station_id:
                match_conditions['station_id'] = station_id
            
            collection = self.db.realtime_data
            
            # Get all available data, ordered by time
            cursor = collection.find(match_conditions).sort('time_point', 1)
            results = await cursor.to_list(None)
            
            if not results:
                logging.warning("❌ No data found in database at all")
                return pd.DataFrame()
            
            # Group by station and create pseudo-annual maxima
            stations_data = {}
            for doc in results:
                station = doc['station_id']
                year = doc['time_point'].year
                depth = doc['depth']
                
                if station not in stations_data:
                    stations_data[station] = {}
                
                if year not in stations_data[station]:
                    stations_data[station][year] = {
                        'max_depth': depth,
                        'station_name': doc.get('name', f'Station {station}'),
                        'latitude': doc.get('latitude', 0),
                        'longitude': doc.get('longitude', 0)
                    }
                else:
                    # Keep maximum depth for this year
                    stations_data[station][year]['max_depth'] = max(
                        stations_data[station][year]['max_depth'], depth
                    )
            
            # Convert to DataFrame format
            rows = []
            for station_id, year_data in stations_data.items():
                for year, data in year_data.items():
                    rows.append({
                        'station_id': station_id,
                        'station_name': data['station_name'],
                        'latitude': data['latitude'],
                        'longitude': data['longitude'],
                        'Year': year,
                        'depth': data['max_depth']
                    })
            
            df = pd.DataFrame(rows)
            
            if not df.empty:
                logging.info(f"📊 Alternative data created: {len(df)} pseudo-annual maxima")
                logging.info(f"📅 Coverage: {df['Year'].min()} - {df['Year'].max()}")
                logging.info(f"🏢 Stations: {df['station_id'].nunique()}")
            
            return df
            
        except Exception as e:
            logging.error(f"❌ Error getting alternative data: {e}")
            return pd.DataFrame()
    
    async def get_realtime_stats(self) -> Dict[str, Any]:
        """Get statistics about realtime data"""
        try:
            if not self.client:
                await self.initialize_database()
            
            collection = self.db.realtime_data
            
            # Basic stats
            total_records = await collection.count_documents({})
            
            if total_records == 0:
                return {
                    'total_records': 0,
                    'stations_count': 0,
                    'date_range': None,
                    'latest_update': None
                }
            
            # Get latest record
            latest_record = await collection.find_one({}, sort=[('time_point', -1)])
            
            # Get oldest record  
            oldest_record = await collection.find_one({}, sort=[('time_point', 1)])
            
            # Count unique stations
            stations_count = len(await collection.distinct('station_id'))
            
            return {
                'total_records': total_records,
                'stations_count': stations_count,
                'date_range': {
                    'start': oldest_record['time_point'].isoformat() if oldest_record else None,
                    'end': latest_record['time_point'].isoformat() if latest_record else None
                },
                'latest_update': latest_record['created_at'].isoformat() if latest_record and 'created_at' in latest_record else None,
                'sample_stations': await collection.distinct('station_id', {}, limit=5)
            }
            
        except Exception as e:
            logging.error(f"❌ Error getting realtime stats: {e}")
            return {'error': str(e)}
    
    def process_to_df(self, api_data: dict) -> pd.DataFrame:
        """Convert API data to DataFrame format for analysis"""
        try:
            if not api_data or not api_data.get('success'):
                return pd.DataFrame()
            
            # For now, return empty DataFrame as data is already in MongoDB
            # This method is kept for backward compatibility
            return pd.DataFrame()
            
        except Exception as e:
            logging.error(f"❌ Error processing to DataFrame: {e}")
            return pd.DataFrame()
    
    async def integrate_to_analysis(self, df: pd.DataFrame):
        """Integrate DataFrame data to analysis system"""
        try:
            if self.data_service:
                self.data_service.data = df
                self.data_service.main_column = 'depth'
                logging.info(f"✅ Integrated {len(df)} records to analysis system")
            else:
                logging.warning("⚠️ No data service available for integration")
            
        except Exception as e:
            logging.error(f"❌ Error integrating to analysis: {e}")
    
    async def fetch_water_level_improved(self) -> dict:
        """Enhanced fetch using improved API service with better error handling and QC"""
        try:
            logging.info("🔄 Fetching water level data using improved API service...")
            
            if self.improved_api_service:
                result = await self.improved_api_service.collect_and_process_data()
            else:
                logging.error("❌ Improved API service not available")
                return {'success': False, 'error': 'API service not initialized'}
            
            if result['success']:
                logging.info(f"✅ Successfully fetched data: {result['total_measurements']} measurements from {result['total_stations']} stations")
                return {
                    'success': True,
                    'data': result,
                    'measurements_count': result['total_measurements'],
                    'stations_count': result['total_stations']
                }
            else:
                logging.error(f"❌ Failed to fetch data: {result.get('error', 'Unknown error')}")
                return {
                    'success': False,
                    'error': result.get('error', 'Unknown error')
                }
                
        except Exception as e:
            logging.error(f"❌ Fetch error: {e}")
            return {
                'success': False,
                'error': str(e)
            }

# Backward compatibility
class RealtimeService(EnhancedRealtimeService):
    """Backward compatibility wrapper"""
    pass