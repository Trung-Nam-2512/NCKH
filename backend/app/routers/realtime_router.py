#!/usr/bin/env python3
"""
Enhanced Realtime Router with Visualization and QC Features
- Time-series visualization
- Quality control monitoring
- Multi-station aggregation
"""
from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import JSONResponse
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import json
import logging

from app.services.realtime_service import EnhancedRealtimeService
from app.services.real_api_service import RealAPIService
from app.models.data_models import RealTimeQuery, RealTimeResponse

router = APIRouter(prefix="/realtime", tags=["realtime"])

# Initialize enhanced service
realtime_service = EnhancedRealtimeService()

@router.on_event("startup")
async def startup_event():
    """Initialize the enhanced realtime service on startup"""
    await realtime_service.start()

@router.on_event("shutdown")
async def shutdown_event():
    """Stop the service on shutdown"""
    await realtime_service.stop()

@router.get("/water-level")
async def get_water_level(
    start_time: str = Query(..., description="Start time (YYYY-MM-DD HH:MM:SS)"),
    end_time: str = Query(..., description="End time (YYYY-MM-DD HH:MM:SS)"),
    station_id: Optional[str] = Query(None, description="Specific station ID"),
    agg_type: str = Query("raw", description="Aggregation type: raw, hourly, daily, max"),
    include_qc: bool = Query(True, description="Include quality control metrics")
) -> Dict[str, Any]:
    """
    Enhanced water level endpoint with aggregation and QC
    """
    try:
        # Fetch raw data
        raw_data = await realtime_service.fetch_water_level(start_time, end_time)
        
        # Process with QC and aggregation
        df = await realtime_service.process_and_store_data(
            raw_data, 
            downsample_interval=agg_type if agg_type in ['hourly', 'daily'] else 'daily'
        )
        
        # Filter by station if specified
        if station_id:
            df = df[df['station_id'] == station_id]
        
        # Apply additional aggregation if requested
        if agg_type == "max":
            df = df.groupby(['station_id', df['time_point'].dt.date])['depth'].max().reset_index()
            df['time_point'] = pd.to_datetime(df['time_point'])
        
        # Prepare response
        response = {
            "data": [],
            "metadata": {
                "start_time": start_time,
                "end_time": end_time,
                "station_id": station_id,
                "agg_type": agg_type,
                "total_records": len(df),
                "stations_count": df['station_id'].nunique() if not df.empty else 0
            }
        }
        
        # Group by station
        for station in df['station_id'].unique():
            station_data = df[df['station_id'] == station]
            station_records = []
            
            for _, row in station_data.iterrows():
                station_records.append({
                    "depth": float(row['depth']),
                    "time_point": row['time_point'].isoformat()
                })
            
            response["data"].append({
                "station_id": station,
                "value": station_records
            })
        
        # Add QC metrics if requested
        if include_qc:
            qc_stats = await realtime_service.get_station_statistics(
                station_id=station_id,
                start_time=datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S'),
                end_time=datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S')
            )
            response["qc_metrics"] = qc_stats
        
        return response
        
    except Exception as e:
        logging.error(f"❌ Water level fetch error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/visualize/depth")
async def visualize_depth(
    station_id: str = Query(..., description="Station ID to visualize"),
    start_time: str = Query(..., description="Start time (YYYY-MM-DD HH:MM:SS)"),
    end_time: str = Query(..., description="End time (YYYY-MM-DD HH:MM:SS)"),
    plot_type: str = Query("line", description="Plot type: line, scatter, heatmap"),
    include_qc: bool = Query(True, description="Include QC indicators")
) -> Dict[str, Any]:
    """
    Create interactive visualizations for depth data
    """
    try:
        # Fetch data
        raw_data = await realtime_service.fetch_water_level(start_time, end_time)
        df = await realtime_service.process_and_store_data(raw_data, 'raw')
        
        # Filter by station
        df = df[df['station_id'] == station_id]
        
        if df.empty:
            raise HTTPException(status_code=404, detail=f"No data found for station {station_id}")
        
        # Create visualization based on plot type
        if plot_type == "line":
            fig = create_line_plot(df, station_id, include_qc)
        elif plot_type == "scatter":
            fig = create_scatter_plot(df, station_id, include_qc)
        elif plot_type == "heatmap":
            fig = create_heatmap_plot(df, station_id)
        else:
            fig = create_line_plot(df, station_id, include_qc)
        
        # Convert to JSON for frontend
        plot_json = json.loads(fig.to_json())
        
        # Add metadata
        response = {
            "plot": plot_json,
            "metadata": {
                "station_id": station_id,
                "start_time": start_time,
                "end_time": end_time,
                "plot_type": plot_type,
                "data_points": len(df),
                "depth_range": {
                    "min": float(df['depth'].min()),
                    "max": float(df['depth'].max()),
                    "mean": float(df['depth'].mean())
                }
            }
        }
        
        return response
        
    except Exception as e:
        logging.error(f"❌ Visualization error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/visualize/multi-station")
async def visualize_multi_station(
    start_time: str = Query(..., description="Start time (YYYY-MM-DD HH:MM:SS)"),
    end_time: str = Query(..., description="End time (YYYY-MM-DD HH:MM:SS)"),
    plot_type: str = Query("heatmap", description="Plot type: heatmap, comparison"),
    max_stations: int = Query(10, description="Maximum number of stations to plot")
) -> Dict[str, Any]:
    """
    Create multi-station visualizations
    """
    try:
        # Fetch data
        raw_data = await realtime_service.fetch_water_level(start_time, end_time)
        df = await realtime_service.process_and_store_data(raw_data, 'daily')
        
        if df.empty:
            raise HTTPException(status_code=404, detail="No data found")
        
        # Limit stations if needed
        if len(df['station_id'].unique()) > max_stations:
            # Select stations with most data
            station_counts = df['station_id'].value_counts()
            top_stations = station_counts.head(max_stations).index
            df = df[df['station_id'].isin(top_stations)]
        
        # Create visualization
        if plot_type == "heatmap":
            fig = create_multi_station_heatmap(df)
        elif plot_type == "comparison":
            fig = create_multi_station_comparison(df)
        else:
            fig = create_multi_station_heatmap(df)
        
        # Convert to JSON
        plot_json = json.loads(fig.to_json())
        
        response = {
            "plot": plot_json,
            "metadata": {
                "start_time": start_time,
                "end_time": end_time,
                "plot_type": plot_type,
                "stations_count": df['station_id'].nunique(),
                "total_records": len(df)
            }
        }
        
        return response
        
    except Exception as e:
        logging.error(f"❌ Multi-station visualization error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/qc/status")
async def get_qc_status(
    station_id: Optional[str] = Query(None, description="Specific station ID")
) -> Dict[str, Any]:
    """
    Get quality control status and metrics
    """
    try:
        stats = await realtime_service.get_station_statistics(station_id=station_id)
        
        # Calculate overall QC health
        total_stations = len(stats['stations'])
        healthy_stations = 0
        issues = []
        
        for station in stats['stations']:
            is_healthy = True
            
            if station.get('outlier_percentage', 0) > 10:
                issues.append(f"Station {station['_id']}: High outlier rate ({station['outlier_percentage']:.1f}%)")
                is_healthy = False
            
            if station.get('data_completeness', 100) < 80:
                issues.append(f"Station {station['_id']}: Low completeness ({station['data_completeness']:.1f}%)")
                is_healthy = False
            
            if is_healthy:
                healthy_stations += 1
        
        qc_health = {
            "overall_status": "healthy" if healthy_stations == total_stations else "warning",
            "healthy_stations": healthy_stations,
            "total_stations": total_stations,
            "health_percentage": (healthy_stations / total_stations * 100) if total_stations > 0 else 0,
            "issues": issues
        }
        
        return {
            "qc_health": qc_health,
            "station_details": stats['stations'],
            "qc_thresholds": stats['qc_thresholds']
        }
        
    except Exception as e:
        logging.error(f"❌ QC status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats/enhanced")
async def get_enhanced_stats(
    station_id: Optional[str] = Query(None, description="Specific station ID"),
    days: int = Query(30, description="Number of days to analyze")
) -> Dict[str, Any]:
    """
    Enhanced statistics with trends and patterns
    """
    try:
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)
        
        stats = await realtime_service.get_station_statistics(
            station_id=station_id,
            start_time=start_time,
            end_time=end_time
        )
        
        # Add trend analysis
        enhanced_stats = {
            "basic_stats": stats,
            "trends": await analyze_trends(station_id, start_time, end_time),
            "patterns": await analyze_patterns(station_id, start_time, end_time)
        }
        
        return enhanced_stats
        
    except Exception as e:
        logging.error(f"❌ Enhanced stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/storage/statistics")
async def get_storage_statistics() -> Dict[str, Any]:
    """
    Get storage statistics for data retention planning
    - Critical for frequency analysis which requires decades of data
    """
    try:
        stats = await realtime_service.get_storage_statistics()
        return stats
        
    except Exception as e:
        logging.error(f"❌ Storage statistics error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/storage/cleanup")
async def manual_data_cleanup(
    years_to_keep: int = Query(50, description="Years of data to preserve (minimum 30 for frequency analysis)"),
    dry_run: bool = Query(True, description="Dry run mode - only show what would be deleted"),
    confirm_deletion: bool = Query(False, description="Must be True to actually delete data")
) -> Dict[str, Any]:
    """
    Manual data cleanup for storage management
    ⚠️ CRITICAL: Only use after careful consideration
    - Frequency analysis requires decades of historical data
    - Recommended minimum: 30 years, optimal: 50+ years
    - Always backup before deletion
    """
    try:
        if years_to_keep < 30:
            raise HTTPException(
                status_code=400, 
                detail="Minimum 30 years required for reliable frequency analysis"
            )
        
        if not dry_run and not confirm_deletion:
            raise HTTPException(
                status_code=400,
                detail="confirm_deletion must be True to actually delete data"
            )
        
        result = await realtime_service.manual_data_cleanup(years_to_keep, dry_run)
        return result
        
    except Exception as e:
        logging.error(f"❌ Manual cleanup error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/storage/backup")
async def backup_historical_data(
    backup_path: Optional[str] = Query(None, description="Custom backup file path")
) -> Dict[str, Any]:
    """
    Backup historical data before any cleanup operations
    - Essential for preserving data for frequency analysis
    """
    try:
        result = await realtime_service.backup_historical_data(backup_path)
        return result
        
    except Exception as e:
        logging.error(f"❌ Backup error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/frequency/data-requirements")
async def get_frequency_analysis_requirements() -> Dict[str, Any]:
    """
    Get data requirements for reliable frequency analysis
    - Based on hydrological standards and best practices
    """
    return {
        "minimum_requirements": {
            "years_of_data": 30,
            "stations": "At least 1 station with continuous data",
            "data_quality": "QC passed, no major gaps",
            "explanation": "Minimum for basic frequency analysis reliability"
        },
        "optimal_requirements": {
            "years_of_data": 50,
            "stations": "Multiple stations for regional analysis",
            "data_quality": "High quality, well-distributed data",
            "explanation": "Optimal for hydrological studies and extreme event analysis"
        },
        "advanced_requirements": {
            "years_of_data": 100,
            "stations": "Dense network for spatial analysis",
            "data_quality": "Excellent quality, multiple parameters",
            "explanation": "For climate change studies and long-term trend analysis"
        },
        "storage_considerations": {
            "data_preservation": "CRITICAL - Never auto-delete historical data",
            "backup_strategy": "Regular backups to multiple locations",
            "storage_planning": "Plan for decades of data accumulation",
            "cost_benefit": "Storage cost vs. scientific value of historical data"
        },
        "frequency_analysis_standards": {
            "source": "USGS Bulletin 17C, WMO Guidelines",
            "minimum_sample_size": "30 years for basic analysis",
            "recommended_sample_size": "50+ years for reliable results",
            "extreme_event_analysis": "Requires maximum possible historical data"
        }
    }

@router.get("/stations")
async def get_stations():
    """Get all stations with their latest data"""
    try:
        # Use RealAPIService to get stations with proper mapping
        real_api_service = RealAPIService()
        await real_api_service.initialize_database()
        
        collection = real_api_service.db.realtime_depth
        
        # Aggregate to get station information with latest data
        pipeline = [
            {
                "$group": {
                    "_id": "$station_id",
                    "station_id": {"$first": "$station_id"},
                    "code": {"$first": "$code"},
                    "name": {"$first": "$name"},
                    "latitude": {"$first": "$latitude"},
                    "longitude": {"$first": "$longitude"},
                    "api_type": {"$first": "$api_type"},
                    "last_measurement": {"$last": "$depth"},
                    "last_updated": {"$last": "$time_point"},
                    "total_measurements": {"$sum": 1},
                    "avg_depth": {"$avg": "$depth"},
                    "min_depth": {"$min": "$depth"},
                    "max_depth": {"$max": "$depth"}
                }
            },
            {
                "$project": {
                    "_id": 1,
                    "station_id": 1,
                    "code": 1,
                    "name": 1,
                    "latitude": 1,
                    "longitude": 1,
                    "api_type": 1,
                    "last_measurement": 1,
                    "last_updated": 1,
                    "total_measurements": 1,
                    "avg_depth": 1,
                    "min_depth": 1,
                    "max_depth": 1,
                    "current_depth": "$last_measurement"
                }
            },
            {"$sort": {"station_id": 1}}
        ]
        
        stations = await collection.aggregate(pipeline).to_list(None)
        
        # Add status based on total_measurements
        for station in stations:
            station["status"] = "active" if station.get("total_measurements", 0) > 0 else "inactive"
        
        # Count active and inactive stations
        active_stations = sum(1 for station in stations if station.get("status") == "active")
        inactive_stations = len(stations) - active_stations
        
        return {
            "stations": stations,
            "total_stations": len(stations),
            "active_stations": active_stations,
            "inactive_stations": inactive_stations
        }
        
    except Exception as e:
        logging.error(f"Error getting stations: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving stations: {str(e)}")

# Visualization helper functions
def create_line_plot(df: pd.DataFrame, station_id: str, include_qc: bool) -> go.Figure:
    """Create line plot with QC indicators"""
    fig = go.Figure()
    
    # Main line plot
    fig.add_trace(go.Scatter(
        x=df['time_point'],
        y=df['depth'],
        mode='lines+markers',
        name=f'Station {station_id}',
        line=dict(color='blue', width=2),
        marker=dict(size=4)
    ))
    
    # Add QC indicators if requested
    if include_qc:
        # Calculate moving average for trend
        df_sorted = df.sort_values('time_point')
        df_sorted['ma_7'] = df_sorted['depth'].rolling(window=7).mean()
        
        fig.add_trace(go.Scatter(
            x=df_sorted['time_point'],
            y=df_sorted['ma_7'],
            mode='lines',
            name='7-point Moving Average',
            line=dict(color='red', width=1, dash='dash')
        ))
    
    fig.update_layout(
        title=f'Water Level Time Series - Station {station_id}',
        xaxis_title='Time',
        yaxis_title='Depth (m)',
        hovermode='x unified'
    )
    
    return fig

def create_scatter_plot(df: pd.DataFrame, station_id: str, include_qc: bool) -> go.Figure:
    """Create scatter plot with QC indicators"""
    fig = go.Figure()
    
    # Main scatter plot
    fig.add_trace(go.Scatter(
        x=df['time_point'],
        y=df['depth'],
        mode='markers',
        name=f'Station {station_id}',
        marker=dict(
            size=6,
            color=df['depth'],
            colorscale='Viridis',
            showscale=True,
            colorbar=dict(title="Depth (m)")
        )
    ))
    
    if include_qc:
        # Add outlier indicators
        mean_depth = df['depth'].mean()
        std_depth = df['depth'].std()
        outliers = df[abs(df['depth'] - mean_depth) > 2 * std_depth]
        
        if not outliers.empty:
            fig.add_trace(go.Scatter(
                x=outliers['time_point'],
                y=outliers['depth'],
                mode='markers',
                name='Potential Outliers',
                marker=dict(size=8, color='red', symbol='x')
            ))
    
    fig.update_layout(
        title=f'Water Level Scatter Plot - Station {station_id}',
        xaxis_title='Time',
        yaxis_title='Depth (m)'
    )
    
    return fig

def create_heatmap_plot(df: pd.DataFrame, station_id: str) -> go.Figure:
    """Create heatmap for daily patterns"""
    # Prepare data for heatmap
    df['hour'] = df['time_point'].dt.hour
    df['day'] = df['time_point'].dt.day_name()
    
    pivot_data = df.pivot_table(
        values='depth',
        index='day',
        columns='hour',
        aggfunc='mean'
    )
    
    fig = go.Figure(data=go.Heatmap(
        z=pivot_data.values,
        x=pivot_data.columns,
        y=pivot_data.index,
        colorscale='Viridis',
        colorbar=dict(title="Depth (m)")
    ))
    
    fig.update_layout(
        title=f'Daily Water Level Patterns - Station {station_id}',
        xaxis_title='Hour of Day',
        yaxis_title='Day of Week'
    )
    
    return fig

def create_multi_station_heatmap(df: pd.DataFrame) -> go.Figure:
    """Create heatmap comparing multiple stations"""
    # Aggregate to daily max for each station
    df['date'] = df['time_point'].dt.date
    pivot_data = df.groupby(['station_id', 'date'])['depth'].max().reset_index()
    pivot_data = pivot_data.pivot(index='date', columns='station_id', values='depth')
    
    fig = go.Figure(data=go.Heatmap(
        z=pivot_data.values,
        x=pivot_data.columns,
        y=pivot_data.index,
        colorscale='Viridis',
        colorbar=dict(title="Max Depth (m)")
    ))
    
    fig.update_layout(
        title='Multi-Station Water Level Comparison',
        xaxis_title='Station ID',
        yaxis_title='Date'
    )
    
    return fig

def create_multi_station_comparison(df: pd.DataFrame) -> go.Figure:
    """Create comparison plot for multiple stations"""
    fig = go.Figure()
    
    for station_id in df['station_id'].unique():
        station_data = df[df['station_id'] == station_id]
        fig.add_trace(go.Scatter(
            x=station_data['time_point'],
            y=station_data['depth'],
            mode='lines',
            name=f'Station {station_id}'
        ))
    
    fig.update_layout(
        title='Multi-Station Water Level Comparison',
        xaxis_title='Time',
        yaxis_title='Depth (m)',
        hovermode='x unified'
    )
    
    return fig

# Analysis helper functions
async def analyze_trends(station_id: Optional[str], start_time: datetime, end_time: datetime) -> Dict[str, Any]:
    """Analyze trends in the data"""
    # This would implement trend analysis
    # For now, return placeholder
    return {
        "trend_direction": "stable",
        "trend_magnitude": 0.0,
        "seasonality_detected": False
    }

async def analyze_patterns(station_id: Optional[str], start_time: datetime, end_time: datetime) -> Dict[str, Any]:
    """Analyze patterns in the data"""
    # This would implement pattern analysis
    # For now, return placeholder
    return {
        "daily_pattern": "consistent",
        "weekly_pattern": "none",
        "anomalies_detected": 0
    } 