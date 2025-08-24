#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script to check frequency analysis logic
Kiem tra logic tinh tan suat
"""
import pandas as pd
import numpy as np
import sys

def test_frequency_logic():
    """Test current frequency analysis logic"""
    
    # Create test data
    test_data = pd.DataFrame({
        'Year': [2020, 2021, 2022, 2023, 2024],
        'depth': [100, 150, 200, 250, 300]
    })
    
    print("Test data:")
    print(test_data)
    print()
    
    # Test current logic
    main_column = 'depth'
    agg_df = test_data.groupby('Year', as_index=False).agg({main_column: 'max'})
    agg_df['Thoi_gian'] = agg_df['Year'].astype(str) + '-' + (agg_df['Year'] + 1).astype(str)
    agg_df['Thu_hang'] = agg_df[main_column].rank(ascending=False, method='min').astype(int)
    
    n = len(agg_df)
    agg_df['Tan_suat_P_percent'] = (agg_df['Thu_hang'] / (n + 1)) * 100
    
    print("Current logic results:")
    print(agg_df[['Year', 'depth', 'Thu_hang', 'Tan_suat_P_percent']])
    print()
    
    # Compare with standard Weibull plotting position
    agg_df_sorted = agg_df.sort_values('depth', ascending=False).reset_index(drop=True)
    agg_df_sorted['Rank'] = range(1, len(agg_df_sorted) + 1)
    agg_df_sorted['Weibull_P_percent'] = (agg_df_sorted['Rank'] / (n + 1)) * 100
    
    print("Standard Weibull plotting position (sorted by decreasing value):")
    print(agg_df_sorted[['Year', 'depth', 'Rank', 'Weibull_P_percent']])
    print()
    
    # Test with larger dataset
    print("=== TEST WITH LARGER DATASET ===")
    large_data = pd.DataFrame({
        'Year': range(2000, 2025),
        'depth': np.random.uniform(100, 1000, 25)  # Random values 100-1000
    })
    
    print("25 years of data with values 100-1000:")
    main_column = 'depth'
    agg_df = large_data.groupby('Year', as_index=False).agg({main_column: 'max'})
    agg_df['Thu_hang'] = agg_df[main_column].rank(ascending=False, method='min').astype(int)
    
    n = len(agg_df)
    agg_df['Tan_suat_P_percent'] = (agg_df['Thu_hang'] / (n + 1)) * 100
    
    # Show top and bottom 5 values
    print("Top 5 highest values:")
    top_5 = agg_df.nlargest(5, 'depth')[['Year', 'depth', 'Thu_hang', 'Tan_suat_P_percent']]
    print(top_5)
    
    print("\nTop 5 lowest values:")
    bottom_5 = agg_df.nsmallest(5, 'depth')[['Year', 'depth', 'Thu_hang', 'Tan_suat_P_percent']]
    print(bottom_5)
    
    print(f"\nFrequency range: {agg_df['Tan_suat_P_percent'].min():.2f}% - {agg_df['Tan_suat_P_percent'].max():.2f}%")
    
    # Check for potential issues
    print("\n=== POTENTIAL ISSUES CHECK ===")
    
    # Check if frequencies are in reasonable range (should be 0-100%)
    min_freq = agg_df['Tan_suat_P_percent'].min()
    max_freq = agg_df['Tan_suat_P_percent'].max()
    
    print(f"Frequency range: {min_freq:.3f}% to {max_freq:.3f}%")
    
    if min_freq < 0 or max_freq > 100:
        print("ERROR: Frequencies outside 0-100% range!")
    else:
        print("OK: Frequencies within 0-100% range")
    
    # Check if rankings are correct
    sorted_by_value = agg_df.sort_values('depth', ascending=False)
    expected_ranks = range(1, len(sorted_by_value) + 1)
    actual_ranks = sorted_by_value['Thu_hang'].values
    
    if list(expected_ranks) == list(actual_ranks):
        print("OK: Rankings are correct")
    else:
        print("ERROR: Rankings are incorrect!")
        print(f"Expected: {list(expected_ranks)}")
        print(f"Actual: {list(actual_ranks)}")
    
    # Check if the formula is applied correctly
    print("\n=== FORMULA VERIFICATION ===")
    print("Formula used: rank / (n + 1) * 100")
    print(f"Where n = {n}")
    
    for i, row in agg_df.iterrows():
        rank = row['Thu_hang']
        expected_freq = (rank / (n + 1)) * 100
        actual_freq = row['Tan_suat_P_percent']
        
        if abs(expected_freq - actual_freq) > 0.001:  # Allow small floating point errors
            print(f"ERROR: Year {row['Year']}, Rank {rank}")
            print(f"  Expected: {expected_freq:.3f}%, Actual: {actual_freq:.3f}%")
    
    print("Formula verification completed.")
    
    return agg_df

if __name__ == "__main__":
    test_frequency_logic()