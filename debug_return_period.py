#!/usr/bin/env python3
"""
Debug return period calculation
"""
import numpy as np
import scipy.stats as stats

# Test với dữ liệu chuẩn
np.random.seed(12345)
data = stats.gumbel_r.rvs(loc=50, scale=10, size=50, random_state=12345)
print(f'Data range: {data.min():.1f} - {data.max():.1f}')

# Fit parameters
params = stats.gumbel_r.fit(data)
location, scale = params
print(f'Fitted: location={location:.3f}, scale={scale:.3f}')

# Return period calculation for T=100
T = 100
print(f'\nReturn period T={T}:')

# Method 1: System method - ppf with (1 - p_values)
p_percent = 100 / T  # Exceedance probability %
p_values = p_percent / 100  # Exceedance probability as decimal
# For return period: we need non-exceedance probability = 1 - exceedance
non_exceed_prob = 1 - p_values
system_result = stats.gumbel_r.ppf(non_exceed_prob, *params)
print(f'System method (ppf): {system_result:.1f}')

# Method 2: Manual Gumbel formula
# Q_T = location + scale * ln(-ln(1-1/T))
# where 1-1/T is non-exceedance probability
non_exceed = 1 - 1/T
manual_result = location + scale * np.log(-np.log(non_exceed))
print(f'Manual formula: {manual_result:.1f}')

# Method 3: Theoretical with true parameters
theoretical = 50 + 10 * np.log(-np.log(1 - 1/T))
print(f'Theoretical: {theoretical:.1f}')

print(f'\nErrors vs theoretical:')
print(f'System: {abs(system_result-theoretical)/theoretical*100:.1f}%')
print(f'Manual: {abs(manual_result-theoretical)/theoretical*100:.1f}%')

# Test với multiple return periods
print(f'\n=== MULTIPLE RETURN PERIODS ===')
return_periods = [2, 5, 10, 25, 50, 100]

for T in return_periods:
    p_percent = 100 / T
    p_values = p_percent / 100
    system_val = stats.gumbel_r.ppf(1 - p_values, *params)
    theoretical_val = 50 + 10 * np.log(-np.log(1 - 1/T))
    error = abs(system_val - theoretical_val) / theoretical_val * 100
    
    print(f'T={T:3}: System={system_val:6.1f}, Theory={theoretical_val:6.1f}, Error={error:5.1f}%')