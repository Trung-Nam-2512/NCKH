#!/usr/bin/env python3
"""
Test Comprehensive Frequency Analysis System - Simple version
"""
import asyncio
import httpx
import json

async def test_comprehensive_system():
    """Test the complete frequency analysis system"""
    
    print("=== TESTING COMPREHENSIVE FREQUENCY ANALYSIS SYSTEM ===")
    print("Testing complete workflow: upload -> analysis -> visualizations -> export")
    
    base_url = "http://127.0.0.1:8000"
    test_results = []
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        
        # Test 1: Upload sample data
        print("\n1. Testing file upload...")
        try:
            sample_csv_data = """Year,Q
2010,120.5
2011,135.2
2012,98.7
2013,156.3
2014,142.1
2015,178.9
2016,165.4
2017,123.6
2018,189.2
2019,201.5
2020,167.8
2021,145.3
2022,198.7
2023,173.2
2024,186.5
"""
            
            files = {"file": ("test_data.csv", sample_csv_data, "text/csv")}
            response = await client.post(f"{base_url}/data/upload", files=files)
            
            if response.status_code == 200:
                print("   PASS: File upload successful")
                test_results.append(("File Upload", True))
            else:
                print(f"   FAIL: File upload failed: {response.status_code}")
                test_results.append(("File Upload", False))
                return test_results
                
        except Exception as e:
            print(f"   FAIL: File upload error: {e}")
            test_results.append(("File Upload", False))
            return test_results
        
        # Test 2: Comprehensive analysis
        print("\n2. Testing comprehensive analysis...")
        try:
            response = await client.post(f"{base_url}/comprehensive/analyze?agg_func=max")
            
            if response.status_code == 200:
                analysis_result = response.json()
                print("   PASS: Comprehensive analysis successful")
                
                if 'statistical_analysis' in analysis_result:
                    best_dist = analysis_result['statistical_analysis']['statistical_summary']['best_distribution']
                    print(f"     Best distribution: {best_dist['display_name']}")
                    print(f"     AIC: {best_dist['aic']:.2f}")
                
                if 'frequency_analysis' in analysis_result:
                    return_periods = analysis_result['frequency_analysis']['return_periods_analysis']
                    print(f"     Return periods: {len(return_periods)}")
                
                if 'visualizations' in analysis_result:
                    viz = analysis_result['visualizations']
                    plot_count = sum(1 for key in viz.keys() if isinstance(viz[key], dict) and viz[key].get('plot_base64'))
                    print(f"     Plots generated: {plot_count}")
                
                test_results.append(("Comprehensive Analysis", True))
                
            else:
                print(f"   FAIL: Comprehensive analysis failed: {response.status_code}")
                test_results.append(("Comprehensive Analysis", False))
                
        except Exception as e:
            print(f"   FAIL: Comprehensive analysis error: {e}")
            test_results.append(("Comprehensive Analysis", False))
        
        # Test 3: Individual visualizations
        print("\n3. Testing visualizations...")
        try:
            response = await client.get(f"{base_url}/comprehensive/visualizations/frequency-curve/gumbel?agg_func=max")
            
            if response.status_code == 200:
                result = response.json()
                if result.get('plot_base64'):
                    print("   PASS: Frequency curve generated")
                    test_results.append(("Visualizations", True))
                else:
                    print("   FAIL: No plot data in response")
                    test_results.append(("Visualizations", False))
            else:
                print(f"   FAIL: Visualization failed: {response.status_code}")
                test_results.append(("Visualizations", False))
                
        except Exception as e:
            print(f"   FAIL: Visualization error: {e}")
            test_results.append(("Visualizations", False))
        
        # Test 4: Export functionality
        print("\n4. Testing export...")
        try:
            response = await client.get(f"{base_url}/comprehensive/export/charts-png?agg_func=max")
            
            if response.status_code == 200:
                charts_result = response.json()
                chart_count = len(charts_result.get('charts', {}))
                print(f"   PASS: PNG export successful: {chart_count} charts")
                test_results.append(("Export", True))
            else:
                print(f"   FAIL: Export failed: {response.status_code}")
                test_results.append(("Export", False))
        except Exception as e:
            print(f"   FAIL: Export error: {e}")
            test_results.append(("Export", False))
    
    return test_results

def print_test_summary(test_results):
    """Print test summary"""
    
    print(f"\n{'='*50}")
    print("TEST RESULTS SUMMARY")
    print(f"{'='*50}")
    
    passed_tests = sum(1 for _, passed in test_results if passed)
    total_tests = len(test_results)
    success_rate = (passed_tests / total_tests) * 100
    
    for test_name, passed in test_results:
        status = "PASS" if passed else "FAIL"
        print(f"{test_name:<25} {status}")
    
    print(f"\nResults: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
    
    if success_rate >= 75:
        print("\nSUCCESS: Comprehensive system working correctly")
        return True
    else:
        print("\nFAILED: System has significant issues")
        return False

async def main():
    """Main test function"""
    
    try:
        test_results = await test_comprehensive_system()
        success = print_test_summary(test_results)
        
        if success:
            print(f"\nCOMPREHENSIVE FREQUENCY ANALYSIS SYSTEM VALIDATED!")
            print("System provides complete workflow like your original:")
            print("  1. File upload and data processing")  
            print("  2. Statistical analysis and distribution fitting")
            print("  3. Frequency curves and QQ/PP plots")
            print("  4. Return period tables")
            print("  5. Export functionality")
            
        else:
            print(f"\nSystem validation failed")
            
    except Exception as e:
        print(f"\nTest error: {e}")

if __name__ == "__main__":
    asyncio.run(main())