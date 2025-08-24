#!/usr/bin/env python3
"""
Script test để hiểu rõ cấu trúc API realtime và phân tích tính khả thi
cho việc tích hợp vào mô hình phân tích tần suất
"""

import asyncio
import httpx
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any
import json
import os

# Load environment variables manually
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception as e:
    print(f"Warning: Could not load .env file: {e}")

class RealtimeAPITester:
    def __init__(self):
        self.stations_url = os.getenv("STATIONS_API_BASE_URL")
        self.stats_url = os.getenv("STATS_API_BASE_URL")
        self.api_key = os.getenv("API_KEY")
        self.headers = {"X-API-Key": self.api_key} if self.api_key else {}
        
        print(f"Debug - Stations URL: {self.stations_url}")
        print(f"Debug - Stats URL: {self.stats_url}")
        print(f"Debug - API Key: {'Set' if self.api_key else 'Not set'}")
        
    async def test_stations_api(self):
        """Test API lấy danh sách trạm đo"""
        print("=== TEST STATIONS API ===")
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(self.stations_url, headers=self.headers)
                print(f"Status: {response.status_code}")
                if response.status_code == 200:
                    stations = response.json()
                    print(f"Số lượng trạm: {len(stations)}")
                    print("Mẫu trạm đầu tiên:")
                    print(json.dumps(stations[0], indent=2, ensure_ascii=False))
                    return stations
                else:
                    print(f"Error: {response.text}")
                    return []
        except Exception as e:
            print(f"Exception: {e}")
            return []

    async def test_stats_api(self, station_id: str = None, test_date: str = None):
        """Test API lấy dữ liệu thống kê theo ngày"""
        print("\n=== TEST STATS API ===")
        
        # Sử dụng ngày hiện tại nếu không có test_date
        if test_date is None:
            test_date = datetime.now().strftime("%Y-%m-%d")
        
        # Quy tắc: 05:00:00 đến 23:00:00 trong ngày
        start_time = f"{test_date} 05:00:00"
        end_time = f"{test_date} 23:00:00"
        
        params = {
            "start_time": start_time,
            "end_time": end_time
        }
        if station_id:
            params["station_id"] = station_id
            
        print(f"Test date: {test_date}")
        print(f"Params: {params}")
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(self.stats_url, params=params, headers=self.headers)
                print(f"Status: {response.status_code}")
                if response.status_code == 200:
                    data = response.json()
                    print("Cấu trúc response:")
                    print(json.dumps(data, indent=2, ensure_ascii=False))
                    
                    # Phân tích dữ liệu
                    self.analyze_realtime_data(data)
                    return data
                else:
                    print(f"Error: {response.text}")
                    return None
        except Exception as e:
            print(f"Exception: {e}")
            return None

    async def test_multiple_days(self, station_id: str = None, days: int = 7):
        """Test lấy dữ liệu nhiều ngày để tích lũy"""
        print(f"\n=== TEST MULTIPLE DAYS ({days} days) ===")
        
        all_data = []
        end_date = datetime.now()
        
        for i in range(days):
            test_date = (end_date - timedelta(days=i)).strftime("%Y-%m-%d")
            print(f"\n--- Testing date: {test_date} ---")
            
            data = await self.test_stats_api(station_id, test_date)
            if data:
                all_data.append(data)
            
            # Delay để tránh rate limit
            await asyncio.sleep(1)
        
        if all_data:
            print(f"\n✅ Successfully collected data for {len(all_data)} days")
            self.analyze_accumulated_data(all_data)
        else:
            print("❌ No data collected")
        
        return all_data

    def analyze_accumulated_data(self, data_list: List[Dict[str, Any]]):
        """Phân tích dữ liệu tích lũy từ nhiều ngày"""
        print("\n=== PHÂN TÍCH DỮ LIỆU TÍCH LŨY ===")
        
        all_measurements = []
        total_days = len(data_list)
        
        for data in data_list:
            if 'Data' in data:
                for station_data in data['Data']:
                    for meas in station_data.get('value', []):
                        meas_dict = meas.copy()
                        meas_dict['station_id'] = station_data.get('station_id', 'Unknown')
                        all_measurements.append(meas_dict)
        
        if not all_measurements:
            print("Không có dữ liệu để phân tích")
            return
        
        df = pd.DataFrame(all_measurements)
        df['time_point'] = pd.to_datetime(df['time_point'])
        df['Year'] = df['time_point'].dt.year
        df['Month'] = df['time_point'].dt.month
        df['Day'] = df['time_point'].dt.day
        
        print(f"Tổng số đo: {len(df)}")
        print(f"Số ngày có dữ liệu: {df['Day'].nunique()}")
        print(f"Số trạm có dữ liệu: {df['station_id'].nunique()}")
        print(f"Khoảng thời gian: {df['time_point'].min()} đến {df['time_point'].max()}")
        
        # Phân tích theo ngày
        daily_stats = df.groupby('Day').agg({
            'depth': ['count', 'mean', 'max'],
            'station_id': 'nunique'
        }).round(3)
        print(f"\nThống kê theo ngày:")
        print(daily_stats)
        
        # Phân tích theo trạm
        station_stats = df.groupby('station_id').agg({
            'depth': ['count', 'mean', 'max'],
            'Day': 'nunique'
        }).round(3)
        print(f"\nThống kê theo trạm:")
        print(station_stats)

    def analyze_realtime_data(self, data: Dict[str, Any]):
        """Phân tích cấu trúc dữ liệu realtime"""
        print("\n=== PHÂN TÍCH CẤU TRÚC DỮ LIỆU ===")
        
        if 'Data' not in data:
            print("Không tìm thấy key 'Data' trong response")
            return
            
        stations_data = data['Data']
        print(f"Số lượng trạm có dữ liệu: {len(stations_data)}")
        
        total_measurements = 0
        time_ranges = []
        
        for station in stations_data:
            station_id = station.get('station_id', 'Unknown')
            measurements = station.get('value', [])
            total_measurements += len(measurements)
            
            if measurements:
                # Phân tích khoảng thời gian
                times = [pd.to_datetime(m['time_point']) for m in measurements]
                time_range = {
                    'station_id': station_id,
                    'start': min(times),
                    'end': max(times),
                    'count': len(measurements),
                    'frequency': len(measurements) / ((max(times) - min(times)).total_seconds() / 3600)  # measurements/hour
                }
                time_ranges.append(time_range)
                
                print(f"\nTrạm {station_id}:")
                print(f"  - Số lượng đo: {len(measurements)}")
                print(f"  - Từ: {time_range['start']}")
                print(f"  - Đến: {time_range['end']}")
                print(f"  - Tần suất đo: {time_range['frequency']:.2f} đo/giờ")
                
                # Phân tích giá trị depth
                depths = [m['depth'] for m in measurements if 'depth' in m]
                if depths:
                    print(f"  - Depth min: {min(depths):.3f} m")
                    print(f"  - Depth max: {max(depths):.3f} m")
                    print(f"  - Depth mean: {sum(depths)/len(depths):.3f} m")
        
        print(f"\nTổng số đo: {total_measurements}")
        
        # Phân tích tần suất đo tổng thể
        if time_ranges:
            avg_frequency = sum(r['frequency'] for r in time_ranges) / len(time_ranges)
            print(f"Tần suất đo trung bình: {avg_frequency:.2f} đo/giờ")

    def simulate_frequency_analysis(self, data: Dict[str, Any]):
        """Mô phỏng phân tích tần suất với dữ liệu realtime"""
        print("\n=== MÔ PHỎNG PHÂN TÍCH TẦN SUẤT ===")
        
        if 'Data' not in data:
            print("Không có dữ liệu để phân tích")
            return
            
        # Chuyển đổi dữ liệu thành DataFrame
        all_measurements = []
        for station_data in data['Data']:
            for meas in station_data.get('value', []):
                meas_dict = meas.copy()
                meas_dict['station_id'] = station_data.get('station_id', 'Unknown')
                all_measurements.append(meas_dict)
        
        if not all_measurements:
            print("Không có dữ liệu đo")
            return
            
        df = pd.DataFrame(all_measurements)
        df['time_point'] = pd.to_datetime(df['time_point'])
        df['Year'] = df['time_point'].dt.year
        df['Month'] = df['time_point'].dt.month
        df['Day'] = df['time_point'].dt.day
        
        # Lọc dữ liệu depth > 0
        df = df[df['depth'] > 0]
        
        print(f"Tổng số đo hợp lệ: {len(df)}")
        print(f"Số năm có dữ liệu: {df['Year'].nunique()}")
        print(f"Số trạm có dữ liệu: {df['station_id'].nunique()}")
        
        # Phân tích theo năm và trạm
        yearly_max = df.groupby(['station_id', 'Year'])['depth'].max().reset_index()
        print(f"\nSố lượng giá trị max theo năm: {len(yearly_max)}")
        
        # Phân tích theo trạm
        station_stats = yearly_max.groupby('station_id').agg({
            'depth': ['count', 'mean', 'std', 'min', 'max']
        }).round(3)
        print("\nThống kê theo trạm:")
        print(station_stats)
        
        # Đánh giá tính khả thi cho phân tích tần suất
        print("\n=== ĐÁNH GIÁ TÍNH KHẢ THI ===")
        
        # Kiểm tra số năm dữ liệu
        years_per_station = yearly_max.groupby('station_id')['Year'].nunique()
        print(f"Số năm dữ liệu theo trạm:")
        print(years_per_station.describe())
        
        # Kiểm tra độ dài chuỗi thời gian
        time_span = df['time_point'].max() - df['time_point'].min()
        print(f"\nĐộ dài chuỗi thời gian: {time_span}")
        
        # Đánh giá chất lượng dữ liệu
        missing_data = df.groupby(['station_id', 'Year']).size().reset_index(name='count')
        print(f"\nSố đo trung bình mỗi năm: {missing_data['count'].mean():.1f}")
        
        # Khuyến nghị
        print("\n=== KHUYẾN NGHỊ ===")
        if years_per_station.max() < 10:
            print("⚠️  Cảnh báo: Dữ liệu ít hơn 10 năm - có thể ảnh hưởng đến độ tin cậy của phân tích tần suất")
        
        if time_span.days < 365:
            print("⚠️  Cảnh báo: Chuỗi thời gian ngắn hơn 1 năm - cần tích lũy thêm dữ liệu")
        
        if missing_data['count'].mean() < 100:
            print("⚠️  Cảnh báo: Số lượng đo mỗi năm thấp - có thể ảnh hưởng đến độ chính xác")
        
        print("✅ Khuyến nghị: Tích hợp dữ liệu realtime vào MongoDB để tích lũy dữ liệu dài hạn")

async def main():
    """Hàm chính để chạy test"""
    tester = RealtimeAPITester()
    
    # Test API stations
    stations = await tester.test_stations_api()
    
    if stations:
        # Test với trạm đầu tiên
        first_station_id = stations[0].get('uuid') if stations else None
        print(f"\nTest với trạm: {first_station_id}")
        
        # Test API stats cho ngày hiện tại
        data = await tester.test_stats_api(first_station_id)
        
        if data:
            # Mô phỏng phân tích tần suất
            tester.simulate_frequency_analysis(data)
        
        # Test lấy dữ liệu nhiều ngày để tích lũy
        print("\n" + "="*50)
        await tester.test_multiple_days(first_station_id, days=3)
    else:
        # Test không có station_id (tất cả trạm)
        print("\nTest với tất cả trạm:")
        data = await tester.test_stats_api()
        if data:
            tester.simulate_frequency_analysis(data)
        
        # Test lấy dữ liệu nhiều ngày
        print("\n" + "="*50)
        await tester.test_multiple_days(days=3)

if __name__ == "__main__":
    asyncio.run(main()) 