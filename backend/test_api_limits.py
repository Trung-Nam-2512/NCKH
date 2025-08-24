#!/usr/bin/env python3
"""
Script test giới hạn API để xác nhận khả năng lấy dữ liệu 2 tháng
"""

import asyncio
import httpx
import pandas as pd
from datetime import datetime, timedelta
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class APILimitsTester:
    def __init__(self):
        self.stations_url = os.getenv("STATIONS_API_BASE_URL")
        self.stats_url = os.getenv("STATS_API_BASE_URL")
        self.api_key = os.getenv("API_KEY")
        self.headers = {"X-API-Key": self.api_key} if self.api_key else {}
        
        print("=== API LIMITS TESTER ===")
        print(f"Stations URL: {self.stations_url}")
        print(f"Stats URL: {self.stats_url}")
        print(f"API Key: {'Set' if self.api_key else 'Not set'}")

    async def test_date_range_limits(self):
        """Test các khoảng thời gian khác nhau để xác định giới hạn"""
        print("\n=== TESTING DATE RANGE LIMITS ===")
        
        test_ranges = [
            (1, "1 ngày"),
            (7, "1 tuần"),
            (30, "1 tháng"),
            (60, "2 tháng"),
            (90, "3 tháng"),
            (120, "4 tháng")
        ]
        
        results = {}
        
        for days, description in test_ranges:
            print(f"\n--- Testing {description} ({days} days) ---")
            
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # Test với ngày đầu tiên trong khoảng
            test_date = start_date.strftime("%Y-%m-%d")
            success = await self.test_single_date(test_date)
            
            results[description] = {
                "days": days,
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d"),
                "single_date_success": success
            }
            
            if success:
                print(f"✅ {description}: Có thể lấy dữ liệu")
            else:
                print(f"❌ {description}: Không thể lấy dữ liệu")
        
        return results

    async def test_single_date(self, date: str):
        """Test lấy dữ liệu cho một ngày cụ thể"""
        start_time = f"{date} 05:00:00"
        end_time = f"{date} 23:00:00"
        
        params = {
            "start_time": start_time,
            "end_time": end_time
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(self.stats_url, params=params, headers=self.headers)
                if response.status_code == 200:
                    data = response.json()
                    if 'Data' in data and len(data['Data']) > 0:
                        return True
                return False
        except Exception as e:
            print(f"Error testing {date}: {e}")
            return False

    async def test_continuous_fetch(self, days: int = 60):
        """Test lấy dữ liệu liên tục trong 60 ngày"""
        print(f"\n=== TESTING CONTINUOUS FETCH ({days} days) ===")
        
        end_date = datetime.now()
        successful_days = 0
        failed_days = 0
        total_records = 0
        
        for i in range(days):
            test_date = (end_date - timedelta(days=i)).strftime("%Y-%m-%d")
            print(f"Testing {test_date}...", end=" ")
            
            success = await self.test_single_date(test_date)
            if success:
                successful_days += 1
                print("✅")
            else:
                failed_days += 1
                print("❌")
            
            # Delay để tránh rate limit
            await asyncio.sleep(0.5)
        
        print(f"\n--- RESULTS ---")
        print(f"Successful days: {successful_days}")
        print(f"Failed days: {failed_days}")
        print(f"Success rate: {successful_days/(successful_days+failed_days)*100:.1f}%")
        
        return {
            "successful_days": successful_days,
            "failed_days": failed_days,
            "success_rate": successful_days/(successful_days+failed_days)*100
        }

    async def test_rate_limits(self):
        """Test rate limits của API"""
        print("\n=== TESTING RATE LIMITS ===")
        
        # Test gọi API liên tục
        delays = [0.1, 0.5, 1.0, 2.0]
        
        for delay in delays:
            print(f"\nTesting with {delay}s delay...")
            
            success_count = 0
            total_calls = 10
            
            for i in range(total_calls):
                test_date = datetime.now().strftime("%Y-%m-%d")
                success = await self.test_single_date(test_date)
                if success:
                    success_count += 1
                
                await asyncio.sleep(delay)
            
            success_rate = success_count / total_calls * 100
            print(f"Success rate with {delay}s delay: {success_rate:.1f}%")
            
            if success_rate >= 90:
                print(f"✅ {delay}s delay is safe")
            else:
                print(f"⚠️ {delay}s delay may be too fast")

async def main():
    """Hàm chính để test"""
    tester = APILimitsTester()
    
    # Test giới hạn khoảng thời gian
    range_results = await tester.test_date_range_limits()
    
    # Test lấy dữ liệu liên tục
    continuous_results = await tester.test_continuous_fetch(days=60)
    
    # Test rate limits
    await tester.test_rate_limits()
    
    # Tổng kết
    print("\n" + "="*50)
    print("=== SUMMARY ===")
    print("API Limits Analysis:")
    for desc, result in range_results.items():
        print(f"- {desc}: {'✅ Available' if result['single_date_success'] else '❌ Not available'}")
    
    print(f"\nContinuous Fetch Results:")
    print(f"- Success rate: {continuous_results['success_rate']:.1f}%")
    print(f"- Successful days: {continuous_results['successful_days']}")
    print(f"- Failed days: {continuous_results['failed_days']}")

if __name__ == "__main__":
    asyncio.run(main()) 