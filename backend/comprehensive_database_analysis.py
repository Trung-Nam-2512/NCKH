#!/usr/bin/env python3
"""
Comprehensive Database Analysis
Detailed analysis of current data availability and gaps
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

async def comprehensive_database_analysis():
    """Comprehensive analysis of database content and gaps"""
    
    print("=" * 80)
    print("COMPREHENSIVE DATABASE ANALYSIS")
    print("=" * 80)
    
    try:
        # Step 1: Check API Service Database
        print("\nSTEP 1: API SERVICE DATABASE ANALYSIS")
        print("-" * 60)
        
        api_service = APIServiceFactory.create_service()
        await api_service.initialize()
        
        # Check API database
        api_db = api_service.database_manager.db
        api_collection = api_db.realtime_depth
        
        api_total = await api_collection.count_documents({})
        print(f"API Database (realtime_depth): {api_total} records")
        
        if api_total > 0:
            # Analyze time range
            oldest_api = await api_collection.find().sort("time_point", 1).limit(1).to_list(1)
            newest_api = await api_collection.find().sort("time_point", -1).limit(1).to_list(1)
            
            oldest_time = oldest_api[0]['time_point']
            newest_time = newest_api[0]['time_point'] 
            time_span = newest_time - oldest_time
            
            print(f"Time range: {oldest_time} to {newest_time}")
            print(f"Time span: {time_span.days} days ({time_span.days/365.25:.1f} years)")
            
            # Analyze by year
            pipeline_api = [
                {
                    "$group": {
                        "_id": {"$year": "$time_point"},
                        "count": {"$sum": 1},
                        "stations": {"$addToSet": "$station_id"}
                    }
                },
                {"$sort": {"_id": 1}}
            ]
            
            year_stats_api = await api_collection.aggregate(pipeline_api).to_list(None)
            print("\nAPI Data by Year:")
            for stat in year_stats_api:
                year = stat['_id']
                count = stat['count']
                stations = len(stat['stations'])
                print(f"  {year}: {count} records from {stations} stations")
            
            # Check unique stations
            unique_stations_api = await api_collection.distinct("station_id")
            print(f"\nUnique stations in API DB: {len(unique_stations_api)}")
        else:
            print("❌ No data in API database")
        
        # Step 2: Check Realtime Service Database  
        print("\nSTEP 2: REALTIME SERVICE DATABASE ANALYSIS")
        print("-" * 60)
        
        data_service = DataService()
        realtime_service = EnhancedRealtimeService(data_service)
        await realtime_service.initialize_database()
        
        realtime_db = realtime_service.db
        realtime_collection = realtime_db.realtime_data
        
        realtime_total = await realtime_collection.count_documents({})
        print(f"Realtime Database (realtime_data): {realtime_total} records")
        
        if realtime_total > 0:
            # Analyze time range
            oldest_rt = await realtime_collection.find().sort("time_point", 1).limit(1).to_list(1)
            newest_rt = await realtime_collection.find().sort("time_point", -1).limit(1).to_list(1)
            
            oldest_time_rt = oldest_rt[0]['time_point']
            newest_time_rt = newest_rt[0]['time_point']
            time_span_rt = newest_time_rt - oldest_time_rt
            
            print(f"Time range: {oldest_time_rt} to {newest_time_rt}")
            print(f"Time span: {time_span_rt.days} days ({time_span_rt.days/365.25:.1f} years)")
            
            # Analyze by year
            pipeline_rt = [
                {
                    "$group": {
                        "_id": {"$year": "$time_point"},
                        "count": {"$sum": 1},
                        "stations": {"$addToSet": "$station_id"}
                    }
                },
                {"$sort": {"_id": 1}}
            ]
            
            year_stats_rt = await realtime_collection.aggregate(pipeline_rt).to_list(None)
            print("\nRealtime Data by Year:")
            for stat in year_stats_rt:
                year = stat['_id']
                count = stat['count']
                stations = len(stat['stations'])
                print(f"  {year}: {count} records from {stations} stations")
            
            # Check unique stations
            unique_stations_rt = await realtime_collection.distinct("station_id")
            print(f"\nUnique stations in Realtime DB: {len(unique_stations_rt)}")
            
            # Detailed station analysis
            print("\nDetailed Station Analysis:")
            for station_id in unique_stations_rt[:5]:  # Top 5 stations
                station_count = await realtime_collection.count_documents({"station_id": station_id})
                
                # Get time range for this station
                station_oldest = await realtime_collection.find({"station_id": station_id}).sort("time_point", 1).limit(1).to_list(1)
                station_newest = await realtime_collection.find({"station_id": station_id}).sort("time_point", -1).limit(1).to_list(1)
                
                if station_oldest and station_newest:
                    station_start = station_oldest[0]['time_point']
                    station_end = station_newest[0]['time_point']
                    station_span = station_end - station_start
                    
                    print(f"  {station_id}: {station_count} records, span {station_span.days} days ({station_span.days/365.25:.1f} years)")
                    
        else:
            print("❌ No data in realtime database")
        
        # Step 3: Data Gap Analysis
        print("\nSTEP 3: DATA GAP ANALYSIS")
        print("-" * 60)
        
        current_year = datetime.now().year
        years_needed_for_analysis = [5, 10, 20, 30]  # Different analysis requirements
        
        available_years = set()
        if realtime_total > 0:
            for stat in year_stats_rt:
                available_years.add(stat['_id'])
        
        print(f"Available years: {sorted(available_years)}")
        print(f"Current year: {current_year}")
        
        for years_needed in years_needed_for_analysis:
            required_start_year = current_year - years_needed + 1
            required_years = set(range(required_start_year, current_year + 1))
            
            missing_years = required_years - available_years
            coverage_percentage = (1 - len(missing_years) / years_needed) * 100
            
            print(f"\nFor {years_needed}-year analysis:")
            print(f"  Required years: {required_start_year}-{current_year}")
            print(f"  Missing years: {sorted(missing_years) if missing_years else 'None'}")
            print(f"  Coverage: {coverage_percentage:.1f}%")
            
            if coverage_percentage < 80:
                print(f"  ❌ Insufficient data for reliable {years_needed}-year analysis")
            elif coverage_percentage < 90:
                print(f"  ⚠️ Marginal data for {years_needed}-year analysis")  
            else:
                print(f"  ✅ Sufficient data for {years_needed}-year analysis")
        
        # Step 4: Frequency Analysis Readiness Check
        print("\nSTEP 4: FREQUENCY ANALYSIS READINESS")
        print("-" * 60)
        
        # Test with different minimum year requirements
        test_scenarios = [1, 2, 3, 5, 10]
        
        for min_years in test_scenarios:
            try:
                freq_data = await realtime_service.get_frequency_ready_data(min_years=min_years)
                
                if len(freq_data) > 0:
                    years_in_data = sorted(freq_data['Year'].unique())
                    stations_count = freq_data['station_id'].nunique()
                    records_count = len(freq_data)
                    
                    print(f"\nMin {min_years} years requirement:")
                    print(f"  ✅ {records_count} annual maxima from {stations_count} stations")
                    print(f"  Years available: {years_in_data}")
                    print(f"  Depth range: {freq_data['depth'].min():.3f} - {freq_data['depth'].max():.3f} m")
                    
                    # This is our viable analysis option
                    viable_min_years = min_years
                    viable_data = freq_data
                    break
                else:
                    print(f"\nMin {min_years} years requirement: ❌ No data available")
            except Exception as e:
                print(f"\nMin {min_years} years requirement: ❌ Error - {e}")
        
        # Step 5: Recommendations
        print("\nSTEP 5: RECOMMENDATIONS")
        print("-" * 60)
        
        recommendations = []
        
        if realtime_total == 0:
            recommendations.append("CRITICAL: No data in realtime database - need data transfer from API")
        elif 'viable_data' not in locals():
            recommendations.append("CRITICAL: No viable data for frequency analysis - need longer time series")
        else:
            total_years_span = len(available_years)
            if total_years_span < 5:
                recommendations.append(f"SHORT-TERM DATA: Only {total_years_span} years available - need historical data collection")
            
            if len(unique_stations_rt) < 3:
                recommendations.append(f"LIMITED SPATIAL COVERAGE: Only {len(unique_stations_rt)} stations - need more stations")
        
        # Check for recent data collection
        if realtime_total > 0 and newest_time_rt:
            days_since_last_update = (datetime.now() - newest_time_rt).days
            if days_since_last_update > 7:
                recommendations.append(f"OUTDATED DATA: Last update {days_since_last_update} days ago - need fresh API collection")
        
        # Data quality recommendations
        if api_total > 0 and realtime_total == 0:
            recommendations.append("DATA INTEGRATION: API has data but realtime DB is empty - need data transfer")
        elif api_total > realtime_total:
            recommendations.append("DATA SYNC: API has more data than realtime DB - need synchronization")
        
        print("Actionable Recommendations:")
        for i, rec in enumerate(recommendations, 1):
            print(f"  {i}. {rec}")
        
        if not recommendations:
            print("  ✅ System appears to be in good condition for frequency analysis")
        
        # Step 6: Action Plan
        print("\nSTEP 6: IMMEDIATE ACTION PLAN")
        print("-" * 60)
        
        if api_total > 0 and realtime_total == 0:
            print("ACTION 1: Transfer data from API database to realtime database")
        elif realtime_total > 0 and 'viable_data' in locals():
            print(f"ACTION 1: Proceed with frequency analysis using {len(viable_data)} records")
            print(f"ACTION 2: Adjust minimum year requirement to {viable_min_years} years")
        
        if api_total > 0:
            print("ACTION 2: Collect additional historical data via API calls")
        
        print("ACTION 3: Implement adaptive minimum year requirements based on data availability")
        print("ACTION 4: Set up continuous data collection to build longer time series")
        
        return {
            'api_total': api_total,
            'realtime_total': realtime_total,
            'available_years': available_years,
            'recommendations': recommendations,
            'viable_analysis': 'viable_data' in locals()
        }
        
    except Exception as e:
        logger.error(f"❌ Database analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        if 'api_service' in locals():
            await api_service.database_manager.close()

if __name__ == "__main__":
    result = asyncio.run(comprehensive_database_analysis())
    
    if result:
        print("\n" + "=" * 80)
        print("ANALYSIS SUMMARY")
        print("=" * 80)
        print(f"API Database: {result['api_total']} records")
        print(f"Realtime Database: {result['realtime_total']} records")
        print(f"Years with data: {len(result['available_years'])}")
        print(f"Viable for analysis: {'Yes' if result['viable_analysis'] else 'No'}")
        print(f"Recommendations: {len(result['recommendations'])}")
        print("=" * 80)
    else:
        print("\n❌ Analysis failed - check logs for details")