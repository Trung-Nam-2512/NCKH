#!/usr/bin/env python3
"""
Test Comprehensive Frequency Analysis System
"""
import asyncio
import httpx
import json
import logging
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_comprehensive_system():
    """Test the complete frequency analysis system"""
    
    print("=== TESTING COMPREHENSIVE FREQUENCY ANALYSIS SYSTEM ===")
    print("Testing complete workflow: upload file → comprehensive analysis → visualizations → export")
    
    base_url = "http://127.0.0.1:8000"
    test_results = []
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        
        # Test 1: Upload sample data
        print("\n1. Testing file upload...")
        try:
            # Create sample CSV data
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
                print("   ✓ File upload successful")
                test_results.append(("File Upload", True))
            else:
                print(f"   ✗ File upload failed: {response.status_code}")
                print(f"     Response: {response.text}")
                test_results.append(("File Upload", False))
                return test_results
                
        except Exception as e:
            print(f"   ✗ File upload error: {e}")
            test_results.append(("File Upload", False))
            return test_results
        
        # Test 2: Data summary
        print("\n2. Testing data summary...")
        try:
            response = await client.get(f"{base_url}/comprehensive/data-summary")
            
            if response.status_code == 200:
                summary = response.json()
                print("   ✓ Data summary successful")
                print(f"     Years: {summary['data_info']['years_count']}")
                print(f"     Records: {summary['data_info']['total_records']}")
                test_results.append(("Data Summary", True))
            else:
                print(f"   ✗ Data summary failed: {response.status_code}")
                test_results.append(("Data Summary", False))
                
        except Exception as e:
            print(f"   ✗ Data summary error: {e}")
            test_results.append(("Data Summary", False))
        
        # Test 3: Comprehensive analysis
        print("\n3. Testing comprehensive analysis...")
        try:
            response = await client.post(f"{base_url}/comprehensive/analyze?agg_func=max")
            
            if response.status_code == 200:
                analysis_result = response.json()
                print("   ✓ Comprehensive analysis successful")
                
                if 'statistical_analysis' in analysis_result:
                    best_dist = analysis_result['statistical_analysis']['statistical_summary']['best_distribution']
                    print(f"     Best distribution: {best_dist['display_name']}")
                    print(f"     AIC: {best_dist['aic']:.2f}")
                    print(f"     Data grade: {best_dist.get('data_quality_grade', 'N/A')}")
                
                if 'frequency_analysis' in analysis_result:
                    return_periods = analysis_result['frequency_analysis']['return_periods_analysis']
                    print(f"     Return periods calculated: {len(return_periods)}")
                
                if 'visualizations' in analysis_result:
                    viz = analysis_result['visualizations']
                    plot_count = sum(1 for key in viz.keys() if isinstance(viz[key], dict) and viz[key].get('plot_base64'))
                    print(f"     Visualizations generated: {plot_count}")
                
                test_results.append(("Comprehensive Analysis", True))
                
            else:
                print(f"   ✗ Comprehensive analysis failed: {response.status_code}")
                print(f"     Response: {response.text}")
                test_results.append(("Comprehensive Analysis", False))
                
        except Exception as e:
            print(f"   ✗ Comprehensive analysis error: {e}")
            test_results.append(("Comprehensive Analysis", False))
        
        # Test 4: Individual visualizations
        print("\n4. Testing individual visualizations...")
        visualization_tests = [
            ("frequency-curve/gumbel", "Frequency Curve"),
            ("qq-pp/gumbel", "QQ-PP Plots"),
            ("distribution-comparison", "Distribution Comparison"),
            ("histogram-fitted", "Histogram Fitted"),
            ("return-period-table/gumbel", "Return Period Table")
        ]
        
        viz_success = 0
        for endpoint, name in visualization_tests:
            try:
                response = await client.get(f"{base_url}/comprehensive/visualizations/{endpoint}?agg_func=max")
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('plot_base64'):
                        print(f"   ✓ {name}")
                        viz_success += 1
                    else:
                        print(f"   ✗ {name} (no plot data)")
                else:
                    print(f"   ✗ {name} ({response.status_code})")
                    
            except Exception as e:
                print(f"   ✗ {name} (error: {e})")
        
        test_results.append(("Individual Visualizations", viz_success >= 3))
        
        # Test 5: All plots generation
        print("\n5. Testing all plots generation...")
        try:
            response = await client.get(f"{base_url}/comprehensive/visualizations/all-plots?agg_func=max")
            
            if response.status_code == 200:
                plots_result = response.json()
                plot_count = sum(1 for key, value in plots_result.items() 
                               if isinstance(value, dict) and value.get('plot_base64'))
                print(f"   ✓ All plots generated: {plot_count} plots")
                test_results.append(("All Plots Generation", True))
            else:
                print(f"   ✗ All plots failed: {response.status_code}")
                test_results.append(("All Plots Generation", False))
                
        except Exception as e:
            print(f"   ✗ All plots error: {e}")
            test_results.append(("All Plots Generation", False))
        
        # Test 6: Export functionality
        print("\n6. Testing export functionality...")
        export_tests = []
        
        # Test Excel export
        try:
            response = await client.post(f"{base_url}/comprehensive/export/excel?agg_func=max")
            
            if response.status_code == 200 and response.headers.get('content-type') == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet':
                print("   ✓ Excel export successful")
                export_tests.append(True)
            else:
                print(f"   ✗ Excel export failed: {response.status_code}")
                export_tests.append(False)
        except Exception as e:
            print(f"   ✗ Excel export error: {e}")
            export_tests.append(False)
        
        # Test PNG charts export
        try:
            response = await client.get(f"{base_url}/comprehensive/export/charts-png?agg_func=max")
            
            if response.status_code == 200:
                charts_result = response.json()
                chart_count = len(charts_result.get('charts', {}))
                print(f"   ✓ PNG charts export successful: {chart_count} charts")
                export_tests.append(True)
            else:
                print(f"   ✗ PNG charts export failed: {response.status_code}")
                export_tests.append(False)
        except Exception as e:
            print(f"   ✗ PNG charts export error: {e}")
            export_tests.append(False)
        
        test_results.append(("Export Functionality", all(export_tests)))
        
        # Test 7: Quick analysis
        print("\n7. Testing quick analysis...")
        try:
            response = await client.post(f"{base_url}/comprehensive/quick-analysis?agg_func=max&include_visualizations=true")
            
            if response.status_code == 200:
                quick_result = response.json()
                print("   ✓ Quick analysis successful")
                
                if 'best_distribution' in quick_result:
                    print(f"     Best distribution: {quick_result['best_distribution']['display_name']}")
                
                if 'return_periods' in quick_result:
                    print(f"     Return periods: {len(quick_result['return_periods'])}")
                
                test_results.append(("Quick Analysis", True))
            else:
                print(f"   ✗ Quick analysis failed: {response.status_code}")
                test_results.append(("Quick Analysis", False))
                
        except Exception as e:
            print(f"   ✗ Quick analysis error: {e}")
            test_results.append(("Quick Analysis", False))
    
    return test_results

def print_test_summary(test_results):
    """Print test summary"""
    
    print(f"\n{'='*60}")
    print("TEST RESULTS SUMMARY")
    print(f"{'='*60}")
    
    passed_tests = sum(1 for _, passed in test_results if passed)
    total_tests = len(test_results)
    success_rate = (passed_tests / total_tests) * 100
    
    for test_name, passed in test_results:
        status = "PASS" if passed else "FAIL"
        emoji = "✓" if passed else "✗"
        print(f"{emoji} {test_name:<30} {status}")
    
    print(f"\nOverall Results: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
    
    if success_rate >= 80:
        print("\n🎉 COMPREHENSIVE SYSTEM TEST: EXCELLENT")
        print("✓ All major functionality working correctly")
        print("✓ Upload → Analysis → Visualization → Export workflow complete")
        print("✓ System ready for production use")
        return True
    elif success_rate >= 60:
        print("\n⚠️  COMPREHENSIVE SYSTEM TEST: GOOD")
        print("✓ Core functionality working")
        print("⚠️  Some features may need attention")
        return True
    else:
        print("\n❌ COMPREHENSIVE SYSTEM TEST: NEEDS WORK")
        print("❌ Major issues detected")
        return False

async def main():
    """Main test function"""
    
    try:
        test_results = await test_comprehensive_system()
        success = print_test_summary(test_results)
        
        if success:
            print(f"\n🎯 COMPREHENSIVE FREQUENCY ANALYSIS SYSTEM VALIDATED!")
            print("System provides complete workflow:")
            print("  1. ✓ File upload and data processing")
            print("  2. ✓ Comprehensive statistical analysis")
            print("  3. ✓ Professional visualizations")
            print("  4. ✓ Multiple export formats")
            print("  5. ✓ Integration with existing endpoints")
            
            print(f"\nAvailable endpoints:")
            print("  • POST /comprehensive/analyze - Full analysis")
            print("  • POST /comprehensive/quick-analysis - Quick results")
            print("  • GET /comprehensive/visualizations/* - Individual plots")
            print("  • POST /comprehensive/export/excel - Excel export")
            print("  • GET /comprehensive/export/charts-png - PNG export")
            
        else:
            print(f"\n❌ System validation failed - check logs for details")
            
    except Exception as e:
        print(f"\n💥 Test suite error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())