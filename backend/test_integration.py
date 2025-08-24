#!/usr/bin/env python3
"""
Test Integration Endpoint for Station Analysis
"""
import asyncio
import httpx
import json

async def test_station_integration():
    """Test station-based frequency analysis"""
    
    print("TESTING STATION INTEGRATION FOR FREQUENCY ANALYSIS")
    print("=" * 60)
    
    base_url = "http://127.0.0.1:8000"
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        
        # Test integration endpoint
        print("\n1. TESTING INTEGRATION/ANALYZE-HISTORICAL")
        print("-" * 40)
        
        # Test data for integration endpoint
        test_payload = {
            "station_ids": ["056882", "1026766701"],  # Use first two stations
            "years_threshold": 5,
            "agg_func": "max"
        }
        
        try:
            response = await client.post(f"{base_url}/integration/analyze-historical", 
                                       json=test_payload,
                                       headers={"Content-Type": "application/json"})
            
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print("SUCCESS: Integration analysis completed")
                
                # Check what's available
                print(f"Keys in result: {list(result.keys())}")
                
                if 'analysis_results' in result:
                    analysis = result['analysis_results']
                    print(f"Analysis keys: {list(analysis.keys())}")
                    
                    # Check for frequency analysis
                    if 'frequency_analysis' in analysis:
                        freq_analysis = analysis['frequency_analysis']
                        print("FREQUENCY ANALYSIS AVAILABLE:")
                        print(f"  Keys: {list(freq_analysis.keys())}")
                        
                        # Check for distribution analysis
                        if 'distribution_comparison' in freq_analysis:
                            dist_comparison = freq_analysis['distribution_comparison']
                            print(f"  Distribution comparison: {len(dist_comparison)} distributions")
                        
                        # Check for visualizations
                        if 'visualizations' in freq_analysis:
                            visualizations = freq_analysis['visualizations']
                            print(f"  Visualizations: {list(visualizations.keys())}")
                            
                            # Check each visualization
                            for viz_name, viz_data in visualizations.items():
                                has_plot = 'plot_base64' in viz_data and viz_data['plot_base64']
                                print(f"    {viz_name}: {'Available' if has_plot else 'Missing'}")
                    
                    # Check for metadata
                    if 'metadata' in analysis:
                        metadata = analysis['metadata']
                        print(f"Metadata: {metadata}")
                
            else:
                print(f"FAILED: Integration analysis error {response.status_code}")
                if response.content:
                    try:
                        error_data = response.json()
                        print(f"Error details: {error_data}")
                    except:
                        print(f"Raw error: {response.text}")
        
        except Exception as e:
            print(f"ERROR: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_station_integration())