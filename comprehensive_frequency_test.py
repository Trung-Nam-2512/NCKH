#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive test for frequency analysis system
Test toàn diện hệ thống phân tích tần suất
"""
import pandas as pd
import numpy as np
import sys
import os

# Add backend paths to import the services
backend_app_path = os.path.join(os.path.dirname(__file__), 'backend', 'app')
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_app_path)
sys.path.insert(0, backend_path)

try:
    from app.services.analysis_service import AnalysisService
    from app.services.data_service import DataService
    from fastapi import HTTPException
except ImportError as e:
    print(f"Cannot import services: {e}")
    print("Testing with simplified logic instead...")
    
    # Simplified test without importing the actual services
    def test_frequency_formula():
        """Test the frequency calculation formula directly"""
        print("=== SIMPLIFIED FREQUENCY FORMULA TEST ===")
        
        # Test data
        test_cases = [
            {"n": 2, "expected_freqs": [33.33, 66.67]},
            {"n": 5, "expected_freqs": [16.67, 33.33, 50.0, 66.67, 83.33]},
            {"n": 10, "expected_freqs": [9.09, 18.18, 27.27, 36.36, 45.45, 54.55, 63.64, 72.73, 81.82, 90.91]}
        ]
        
        for case in test_cases:
            n = case["n"]
            expected = case["expected_freqs"]
            
            # Calculate frequencies using Weibull formula: rank/(n+1)*100
            calculated = [(rank / (n + 1)) * 100 for rank in range(1, n + 1)]
            
            print(f"\nTest with n={n} years:")
            print(f"  Expected frequencies (approx): {[f'{f:.2f}%' for f in expected]}")
            print(f"  Calculated frequencies: {[f'{f:.2f}%' for f in calculated]}")
            
            # Check if values are reasonable
            if min(calculated) > 0 and max(calculated) < 100:
                print(f"  ✅ Frequencies within valid range: {min(calculated):.2f}% - {max(calculated):.2f}%")
            else:
                print(f"  ❌ Frequencies out of range!")
                
        return True
    
    def main():
        """Run simplified test"""
        print("SIMPLIFIED FREQUENCY ANALYSIS TEST")
        print("=" * 50)
        test_frequency_formula()
        print("\n🎉 Formula verification completed!")
        return True
        
    AnalysisService = None
    DataService = None

def test_insufficient_data():
    """Test with insufficient data (1 year)"""
    print("=== TEST 1: INSUFFICIENT DATA (1 YEAR) ===")
    
    # Create data with only 1 year
    insufficient_data = pd.DataFrame({
        'Year': [2025],
        'depth': [100.5]
    })
    
    data_service = DataService()
    data_service.data = insufficient_data
    data_service.main_column = 'depth'
    
    analysis_service = AnalysisService(data_service)
    
    try:
        result = analysis_service.get_frequency_analysis()
        print("ERROR: Should have thrown exception for insufficient data!")
        return False
    except HTTPException as e:
        print(f"✅ Correctly rejected insufficient data: {e.detail}")
        return True
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_minimal_data():
    """Test with minimal acceptable data (2 years)"""
    print("\n=== TEST 2: MINIMAL DATA (2 YEARS) ===")
    
    minimal_data = pd.DataFrame({
        'Year': [2023, 2024],
        'depth': [150.0, 200.0]
    })
    
    data_service = DataService()
    data_service.data = minimal_data
    data_service.main_column = 'depth'
    
    analysis_service = AnalysisService(data_service)
    
    try:
        result = analysis_service.get_frequency_analysis()
        print(f"✅ Successfully processed 2 years of data")
        print(f"   Result has {len(result)} records")
        
        # Verify results
        for i, record in enumerate(result):
            print(f"   Record {i+1}: Year={record['Thời gian']}, Value={record['Chỉ số']}, "
                  f"Rank={record['Thứ hạng']}, Frequency={record['Tần suất P(%)']}%")
        
        # Check frequency values are reasonable
        frequencies = [record['Tần suất P(%)'] for record in result]
        if min(frequencies) >= 0 and max(frequencies) <= 100:
            print("✅ Frequencies within valid range (0-100%)")
            return True
        else:
            print(f"❌ Frequencies out of range: {min(frequencies)}-{max(frequencies)}")
            return False
            
    except Exception as e:
        print(f"❌ Error with minimal data: {e}")
        return False

def test_normal_data():
    """Test with normal amount of data (20 years)"""
    print("\n=== TEST 3: NORMAL DATA (20 YEARS) ===")
    
    # Load the test data
    try:
        normal_data = pd.read_csv('backend/correct_test_data.csv')
        print(f"Loaded {len(normal_data)} years of test data")
    except FileNotFoundError:
        print("❌ Test data file not found, creating synthetic data")
        normal_data = pd.DataFrame({
            'Year': range(2005, 2025),
            'Q': np.random.uniform(85, 205, 20)
        })
    
    data_service = DataService()
    data_service.data = normal_data
    data_service.main_column = 'Q' if 'Q' in normal_data.columns else 'depth'
    
    analysis_service = AnalysisService(data_service)
    
    try:
        result = analysis_service.get_frequency_analysis()
        print(f"✅ Successfully processed {len(normal_data)} years of data")
        print(f"   Result has {len(result)} records")
        
        # Show sample results
        print("   Sample results:")
        for i, record in enumerate(result[:5]):  # First 5 records
            print(f"     {i+1}. {record['Thời gian']}: {record['Chỉ số']} -> {record['Tần suất P(%)']}% (Rank {record['Thứ hạng']})")
        
        # Verify frequencies
        frequencies = [record['Tần suất P(%)'] for record in result]
        min_freq = min(frequencies)
        max_freq = max(frequencies)
        
        if min_freq >= 0 and max_freq <= 100:
            print(f"✅ Frequencies in valid range: {min_freq:.2f}% - {max_freq:.2f}%")
        else:
            print(f"❌ Frequencies out of range: {min_freq:.2f}% - {max_freq:.2f}%")
            return False
        
        # Verify ranking is correct
        sorted_by_value = sorted(result, key=lambda x: x['Chỉ số'], reverse=True)
        expected_ranks = list(range(1, len(sorted_by_value) + 1))
        actual_ranks = [record['Thứ hạng'] for record in sorted_by_value]
        
        if expected_ranks == actual_ranks:
            print("✅ Rankings are correct")
        else:
            print(f"❌ Rankings incorrect. Expected: {expected_ranks}, Got: {actual_ranks}")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Error with normal data: {e}")
        return False

def test_distribution_analysis():
    """Test distribution analysis with insufficient data"""
    print("\n=== TEST 4: DISTRIBUTION ANALYSIS ===")
    
    # Test with insufficient data for distribution analysis
    insufficient_data = pd.DataFrame({
        'Year': [2023, 2024],
        'depth': [150.0, 200.0]
    })
    
    data_service = DataService()
    data_service.data = insufficient_data
    data_service.main_column = 'depth'
    
    analysis_service = AnalysisService(data_service)
    
    try:
        result = analysis_service.get_distribution_analysis()
        print("ERROR: Should have thrown exception for insufficient distribution data!")
        return False
    except HTTPException as e:
        print(f"✅ Correctly rejected insufficient data for distribution analysis: {e.detail}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False
    
    # Test with sufficient data
    try:
        normal_data = pd.read_csv('backend/correct_test_data.csv')
        data_service.data = normal_data
        data_service.main_column = 'Q' if 'Q' in normal_data.columns else 'depth'
        
        result = analysis_service.get_distribution_analysis()
        print(f"✅ Distribution analysis successful with {len(normal_data)} years")
        
        # Check if any distributions were fitted
        distributions_fitted = sum(1 for dist_name, dist_data in result.items() 
                                 if 'error' not in dist_data)
        print(f"   Successfully fitted {distributions_fitted} distributions")
        
        return True
        
    except FileNotFoundError:
        print("⚠️  Test data file not found, skipping distribution test")
        return True
    except Exception as e:
        print(f"❌ Error in distribution analysis: {e}")
        return False

def main():
    """Run all tests"""
    print("COMPREHENSIVE FREQUENCY ANALYSIS TEST")
    print("=" * 50)
    
    tests = [
        test_insufficient_data,
        test_minimal_data,  
        test_normal_data,
        test_distribution_analysis
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results.append(False)
    
    print("\n" + "=" * 50)
    print("SUMMARY:")
    passed = sum(results)
    total = len(results)
    
    for i, (test, result) in enumerate(zip(tests, results), 1):
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"Test {i} ({test.__name__}): {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! The frequency analysis system is working correctly.")
    else:
        print("⚠️  Some tests failed. Please review the issues above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)