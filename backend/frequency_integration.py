#!/usr/bin/env python3
"""
Frequency Analysis Integration
- Tích hợp dữ liệu realtime từ MongoDB với phân tích tần suất
- Tạo dữ liệu sẵn sàng cho analysis service
"""

import asyncio
import logging
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class FrequencyIntegration:
    def __init__(self):
        self.mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
        self.mongo_client = AsyncIOMotorClient(self.mongo_uri)
        self.db = self.mongo_client["hydro_db"]
        self.collection = self.db["realtime_depth"]
        
        logging.info("=== FREQUENCY INTEGRATION INITIALIZED ===")

    async def get_frequency_ready_data(self, station_id: Optional[str] = None, 
                                     min_years: int = 1) -> pd.DataFrame:
        """
        Lấy dữ liệu sẵn sàng cho phân tích tần suất
        - Tạo cấu trúc dữ liệu phù hợp với analysis service
        - Tính toán giá trị max theo năm cho mỗi trạm
        """
        try:
            logging.info(f"Getting frequency-ready data (min_years={min_years})")
            
            # Pipeline để lấy dữ liệu theo năm và trạm
            pipeline = [
                {"$addFields": {"Year": {"$year": "$time_point"}}},
                {"$group": {
                    "_id": {"station_id": "$station_id", "Year": "$Year"},
                    "max_depth": {"$max": "$depth"},
                    "min_depth": {"$min": "$depth"},
                    "avg_depth": {"$avg": "$depth"},
                    "count": {"$sum": 1},
                    "measurements": {"$push": "$depth"}
                }},
                {"$group": {
                    "_id": "$_id.station_id",
                    "years_count": {"$sum": 1},
                    "yearly_data": {"$push": {
                        "Year": "$_id.Year",
                        "max_depth": "$max_depth",
                        "min_depth": "$min_depth",
                        "avg_depth": "$avg_depth",
                        "count": "$count",
                        "measurements": "$measurements"
                    }}
                }},
                {"$match": {"years_count": {"$gte": min_years}}}
            ]
            
            if station_id:
                pipeline.insert(0, {"$match": {"station_id": station_id}})
            
            result = await self.collection.aggregate(pipeline).to_list(None)
            
            # Chuyển đổi thành DataFrame
            all_data = []
            for station_data in result:
                station_id = station_data["_id"]
                for year_data in station_data["yearly_data"]:
                    all_data.append({
                        "station_id": station_id,
                        "Year": year_data["Year"],
                        "depth": year_data["max_depth"],  # Sử dụng max cho phân tích tần suất
                        "min_depth": year_data["min_depth"],
                        "avg_depth": year_data["avg_depth"],
                        "measurements_count": year_data["count"],
                        "data_source": "realtime"
                    })
            
            df = pd.DataFrame(all_data)
            if not df.empty:
                df = df.sort_values(['station_id', 'Year'])
                logging.info(f"Frequency-ready data: {len(df)} records from {df['station_id'].nunique()} stations")
            
            return df
            
        except Exception as e:
            logging.error(f"Error getting frequency-ready data: {e}")
            return pd.DataFrame()

    async def get_station_summary(self) -> Dict[str, Any]:
        """Lấy tổng quan về các trạm có dữ liệu"""
        try:
            pipeline = [
                {"$addFields": {"Year": {"$year": "$time_point"}}},
                {"$group": {
                    "_id": {"station_id": "$station_id", "Year": "$Year"},
                    "max_depth": {"$max": "$depth"},
                    "count": {"$sum": 1}
                }},
                {"$group": {
                    "_id": "$_id.station_id",
                    "years_count": {"$sum": 1},
                    "total_measurements": {"$sum": "$count"},
                    "max_depth_overall": {"$max": "$max_depth"},
                    "avg_max_depth": {"$avg": "$max_depth"}
                }},
                {"$sort": {"years_count": -1}}
            ]
            
            result = await self.collection.aggregate(pipeline).to_list(None)
            
            return {
                "stations": result,
                "total_stations": len(result),
                "stations_with_multiple_years": len([s for s in result if s["years_count"] > 1])
            }
            
        except Exception as e:
            logging.error(f"Error getting station summary: {e}")
            return {}

    async def export_for_analysis(self, output_file: str = "realtime_frequency_data.csv"):
        """Xuất dữ liệu cho phân tích tần suất"""
        try:
            logging.info("Exporting data for frequency analysis...")
            
            # Lấy dữ liệu sẵn sàng
            df = await self.get_frequency_ready_data(min_years=1)
            
            if not df.empty:
                # Xuất ra file CSV
                df.to_csv(output_file, index=False)
                logging.info(f"✅ Exported {len(df)} records to {output_file}")
                
                # Thống kê
                print(f"\n📊 Export Summary:")
                print(f"Total records: {len(df)}")
                print(f"Stations: {df['station_id'].nunique()}")
                print(f"Years: {df['Year'].nunique()}")
                print(f"Date range: {df['Year'].min()} - {df['Year'].max()}")
                
                # Phân tích theo trạm
                station_stats = df.groupby('station_id').agg({
                    'depth': ['count', 'mean', 'max'],
                    'Year': 'nunique'
                }).round(3)
                
                print(f"\nTop stations by data count:")
                top_stations = station_stats.sort_values(('depth', 'count'), ascending=False).head(5)
                for station_id in top_stations.index:
                    count = top_stations.loc[station_id, ('depth', 'count')]
                    years = top_stations.loc[station_id, ('Year', 'nunique')]
                    max_depth = top_stations.loc[station_id, ('depth', 'max')]
                    print(f"  {station_id}: {count} records, {years} years, max depth: {max_depth}m")
                
                return df
            else:
                logging.warning("No data to export")
                return pd.DataFrame()
                
        except Exception as e:
            logging.error(f"Error exporting data: {e}")
            return pd.DataFrame()

    async def compare_with_historical(self, historical_file: str = "test_data.csv"):
        """So sánh dữ liệu realtime với dữ liệu lịch sử"""
        try:
            logging.info("Comparing realtime data with historical data...")
            
            # Lấy dữ liệu realtime
            realtime_df = await self.get_frequency_ready_data(min_years=1)
            
            if realtime_df.empty:
                logging.warning("No realtime data available")
                return
            
            # Đọc dữ liệu lịch sử
            try:
                historical_df = pd.read_csv(historical_file)
                logging.info(f"Loaded historical data: {len(historical_df)} records")
            except FileNotFoundError:
                logging.warning(f"Historical file {historical_file} not found")
                return
            
            # So sánh
            print(f"\n📈 COMPARISON ANALYSIS:")
            print(f"Realtime data: {len(realtime_df)} records, {realtime_df['station_id'].nunique()} stations")
            print(f"Historical data: {len(historical_df)} records, {historical_df['station_id'].nunique() if 'station_id' in historical_df.columns else 'N/A'} stations")
            
            # Phân tích độ sâu
            if 'depth' in historical_df.columns:
                print(f"\nDepth Analysis:")
                print(f"Realtime - Max depth: {realtime_df['depth'].max():.3f}m, Mean: {realtime_df['depth'].mean():.3f}m")
                print(f"Historical - Max depth: {historical_df['depth'].max():.3f}m, Mean: {historical_df['depth'].mean():.3f}m")
            
            # Phân tích theo năm
            if 'Year' in historical_df.columns:
                print(f"\nYear Analysis:")
                realtime_years = realtime_df['Year'].unique()
                historical_years = historical_df['Year'].unique()
                print(f"Realtime years: {sorted(realtime_years)}")
                print(f"Historical years: {sorted(historical_years)}")
                
                # Tìm năm chung
                common_years = set(realtime_years) & set(historical_years)
                if common_years:
                    print(f"Common years: {sorted(common_years)}")
                else:
                    print("No common years between datasets")
            
        except Exception as e:
            logging.error(f"Error comparing data: {e}")

    async def generate_frequency_report(self):
        """Tạo báo cáo phân tích tần suất"""
        try:
            logging.info("Generating frequency analysis report...")
            
            # Lấy dữ liệu
            df = await self.get_frequency_ready_data(min_years=1)
            
            if df.empty:
                logging.warning("No data available for frequency analysis")
                return
            
            # Tạo báo cáo
            report = {
                "generated_at": datetime.now().isoformat(),
                "total_records": len(df),
                "stations_count": df['station_id'].nunique(),
                "years_count": df['Year'].nunique(),
                "date_range": {
                    "start": int(df['Year'].min()),
                    "end": int(df['Year'].max())
                },
                "depth_statistics": {
                    "min": float(df['depth'].min()),
                    "max": float(df['depth'].max()),
                    "mean": float(df['depth'].mean()),
                    "std": float(df['depth'].std())
                },
                "station_analysis": {}
            }
            
            # Phân tích theo trạm
            for station_id in df['station_id'].unique():
                station_data = df[df['station_id'] == station_id]
                report["station_analysis"][station_id] = {
                    "records_count": len(station_data),
                    "years_count": station_data['Year'].nunique(),
                    "depth_range": {
                        "min": float(station_data['depth'].min()),
                        "max": float(station_data['depth'].max()),
                        "mean": float(station_data['depth'].mean())
                    }
                }
            
            # Lưu báo cáo
            import json
            with open("frequency_analysis_report.json", "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            logging.info("✅ Frequency analysis report generated")
            
            # In tóm tắt
            print(f"\n📋 FREQUENCY ANALYSIS REPORT:")
            print(f"Total records: {report['total_records']}")
            print(f"Stations: {report['stations_count']}")
            print(f"Years: {report['years_count']}")
            print(f"Date range: {report['date_range']['start']} - {report['date_range']['end']}")
            print(f"Depth range: {report['depth_statistics']['min']:.3f}m - {report['depth_statistics']['max']:.3f}m")
            
            return report
            
        except Exception as e:
            logging.error(f"Error generating frequency report: {e}")
            return None

async def main():
    """Hàm chính"""
    integration = FrequencyIntegration()
    
    # Xuất dữ liệu cho phân tích
    df = await integration.export_for_analysis()
    
    # Tạo báo cáo
    await integration.generate_frequency_report()
    
    # So sánh với dữ liệu lịch sử
    await integration.compare_with_historical()
    
    # Hiển thị tổng quan trạm
    summary = await integration.get_station_summary()
    if summary:
        print(f"\n🏢 STATION SUMMARY:")
        print(f"Total stations: {summary['total_stations']}")
        print(f"Stations with multiple years: {summary['stations_with_multiple_years']}")

if __name__ == "__main__":
    asyncio.run(main()) 