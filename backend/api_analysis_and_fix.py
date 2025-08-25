#!/usr/bin/env python3
"""
PHÂN TÍCH VÀ SỬA LỖI API LOGIC

Vấn đề phát hiện:
1. API KTTV sử dụng start_time/end_time -> có thể trùng lặp data khi chạy nhiều lần
2. API NOKTTV không có tham số thời gian -> chỉ trả dữ liệu hiện tại
3. Logic scheduler chưa xử lý đúng deduplication

Giải pháp cần thiết:
- Phân tích chính xác behavior của từng API
- Thiết kế collection strategy phù hợp cho từng loại API
- Đảm bảo no duplicate data khi API trả về time ranges
"""

import asyncio
import logging
import httpx
from datetime import datetime, timedelta
import json

# Cấu hình logging
logging.basicConfig(level=logging.INFO)

async def analyze_kttv_api():
    """
    Phân tích KTTV API để hiểu rõ behavior
    - Có sử dụng start_time/end_time parameters
    - Giới hạn time range (1-2 giờ max)
    - Trả về dữ liệu trong khoảng thời gian specified
    """
    print("\n🔍 ANALYZING KTTV API BEHAVIOR")
    print("="*50)
    
    # Test case 1: Time range behavior
    print("📊 Test 1: Time range behavior")
    
    base_time = datetime.now()
    
    # Test multiple time windows
    test_scenarios = [
        {"hours": 1, "description": "1 hour window"},
        {"hours": 2, "description": "2 hour window"}, 
        {"hours": 3, "description": "3 hour window (should fail)"},
    ]
    
    for scenario in test_scenarios:
        end_time = base_time
        start_time = end_time - timedelta(hours=scenario["hours"])
        
        print(f"   Testing {scenario['description']}")
        print(f"   Range: {start_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}")
        
        # Simulate API call results
        if scenario["hours"] <= 2:
            print(f"   ✅ Expected: SUCCESS - Returns ~{scenario['hours']*6} records (10min intervals)")
        else:
            print(f"   ❌ Expected: FAIL - 'time range too wide' error")
    
    print("\n📋 KTTV API Characteristics:")
    print("- Uses start_time/end_time parameters")
    print("- Returns data within specified time range")
    print("- Max range: 1-2 hours")
    print("- Data interval: ~10 minutes")
    print("- Risk: DUPLICATE DATA if same time range queried multiple times")
    
    return {
        "api_type": "kttv",
        "uses_time_params": True,
        "max_range_hours": 2,
        "duplicate_risk": "HIGH",
        "deduplication_required": True
    }

async def analyze_nokttv_api():
    """
    Phân tích NOKTTV API để hiểu rõ behavior
    - Không có start_time/end_time parameters
    - Chỉ trả về dữ liệu hiện tại/gần đây nhất
    """
    print("\n🔍 ANALYZING NOKTTV API BEHAVIOR")
    print("="*50)
    
    print("📊 Test: Parameter behavior")
    print("   Empty params = {} -> Returns current/recent data only")
    print("   No time filtering available")
    
    print("\n📋 NOKTTV API Characteristics:")
    print("- NO time parameters")
    print("- Returns only current/recent data")
    print("- Data scope: Last few hours or current day")
    print("- Risk: LOW duplicate risk (current data only)")
    
    return {
        "api_type": "nokttv", 
        "uses_time_params": False,
        "max_range_hours": None,
        "duplicate_risk": "LOW",
        "deduplication_required": False
    }

def analyze_current_scheduler_logic():
    """
    Phân tích logic scheduler hiện tại và identify issues
    """
    print("\n🔍 ANALYZING CURRENT SCHEDULER LOGIC")
    print("="*50)
    
    print("📊 Current Issues Identified:")
    print("\n1. UNIFORM TREATMENT ISSUE:")
    print("   - Both APIs treated the same way")
    print("   - KTTV API can return duplicate data across multiple calls")  
    print("   - NOKTTV API only returns current data (less duplication risk)")
    
    print("\n2. DEDUPLICATION ISSUES:")
    print("   - Unique constraint: (station_id, time_point, api_type)")
    print("   - KTTV: Multiple calls might return same time_point data")
    print("   - Need stronger deduplication for KTTV")
    
    print("\n3. COLLECTION STRATEGY ISSUES:")
    print("   - 3 times daily collection might collect same KTTV data")
    print("   - No time-aware collection for KTTV")
    print("   - Missing backfill strategy for missed data")
    
    return {
        "uniform_treatment": "PROBLEMATIC",
        "kttv_duplicate_risk": "HIGH",
        "nokttv_duplicate_risk": "LOW",
        "collection_strategy": "NEEDS_REVISION"
    }

def design_improved_collection_strategy():
    """
    Thiết kế collection strategy cải tiến dựa trên API behavior
    """
    print("\n💡 IMPROVED COLLECTION STRATEGY")
    print("="*50)
    
    strategy = {
        "kttv_strategy": {
            "approach": "TIME_WINDOW_BASED",
            "description": "Use non-overlapping time windows",
            "collection_times": [
                {"time": "06:30", "window": "05:00-07:00", "target": "night/early morning data"},
                {"time": "14:30", "window": "12:00-14:00", "target": "midday data"},  
                {"time": "22:30", "window": "20:00-22:00", "target": "evening data"}
            ],
            "deduplication": "STRICT - Check exact time_point + station_id",
            "backfill": "Query missed windows with specific time ranges"
        },
        "nokttv_strategy": {
            "approach": "CURRENT_DATA_ONLY",
            "description": "Collect current data, no time params needed",
            "collection_times": ["06:30", "14:30", "22:30"],
            "deduplication": "STANDARD - (station_id, time_point, api_type)",
            "backfill": "Not applicable (no historical query capability)"
        }
    }
    
    for api_type, config in strategy.items():
        print(f"\n🔧 {api_type.upper()} Strategy:")
        print(f"   Approach: {config['approach']}")
        print(f"   Description: {config['description']}")
        if 'collection_times' in config:
            if isinstance(config['collection_times'], list) and len(config['collection_times']) > 0:
                if isinstance(config['collection_times'][0], dict):
                    for slot in config['collection_times']:
                        print(f"   Time: {slot['time']} - {slot['target']} ({slot['window']})")
                else:
                    print(f"   Times: {', '.join(config['collection_times'])}")
        print(f"   Deduplication: {config['deduplication']}")
    
    return strategy

def identify_critical_fixes():
    """
    Xác định các fixes quan trọng cần thực hiện
    """
    print("\n🚨 CRITICAL FIXES REQUIRED")
    print("="*50)
    
    fixes = [
        {
            "priority": "CRITICAL",
            "component": "DailyDataCollector.fetch_daily_stats()",
            "issue": "KTTV API cần time parameters, hiện tại dùng empty params",
            "fix": "Add time window logic for KTTV API"
        },
        {
            "priority": "HIGH", 
            "component": "Collection deduplication logic",
            "issue": "Unique constraint có thể không đủ cho KTTV overlapping data",
            "fix": "Strengthen deduplication with additional checks"
        },
        {
            "priority": "HIGH",
            "component": "Scheduler collection times",
            "issue": "3 times daily có thể collect duplicate KTTV data",
            "fix": "Use non-overlapping time windows for KTTV"
        },
        {
            "priority": "MEDIUM",
            "component": "API-specific handling",
            "issue": "Uniform treatment không tận dụng được đặc điểm riêng của từng API",
            "fix": "Implement API-specific collection strategies"
        },
        {
            "priority": "MEDIUM",
            "component": "Backfill mechanism",
            "issue": "Chưa có mechanism để collect missed data",
            "fix": "Add intelligent backfill for KTTV time windows"
        }
    ]
    
    for fix in fixes:
        print(f"\n🔥 {fix['priority']}: {fix['component']}")
        print(f"   Issue: {fix['issue']}")
        print(f"   Fix: {fix['fix']}")
    
    return fixes

async def main():
    """Run comprehensive API analysis"""
    print("API BEHAVIOR ANALYSIS & DEDUPLICATION STRATEGY")
    print("="*70)
    
    # Analyze both APIs
    kttv_analysis = await analyze_kttv_api()
    nokttv_analysis = await analyze_nokttv_api()
    
    # Analyze current logic
    current_issues = analyze_current_scheduler_logic()
    
    # Design improved strategy
    improved_strategy = design_improved_collection_strategy()
    
    # Identify fixes
    critical_fixes = identify_critical_fixes()
    
    # Summary
    print("\n📊 ANALYSIS SUMMARY")
    print("="*70)
    
    print(f"KTTV API: {kttv_analysis['duplicate_risk']} duplicate risk")
    print(f"NOKTTV API: {nokttv_analysis['duplicate_risk']} duplicate risk")
    print(f"Current scheduler: {current_issues['collection_strategy']}")
    print(f"Critical fixes needed: {len(critical_fixes)}")
    
    print("\n⚠️ CONCLUSION:")
    print("Current implementation CÓ NGUY CƠ TRÙNG LẶP DỮ LIỆU từ KTTV API")
    print("Cần thiết kế lại collection logic với API-specific strategies")
    
    return {
        "kttv_analysis": kttv_analysis,
        "nokttv_analysis": nokttv_analysis,
        "current_issues": current_issues,
        "improved_strategy": improved_strategy,
        "critical_fixes": critical_fixes
    }

if __name__ == "__main__":
    asyncio.run(main())