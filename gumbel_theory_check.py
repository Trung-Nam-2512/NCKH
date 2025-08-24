#!/usr/bin/env python3
"""
Verify Gumbel distribution theory and formulas
Check against standard references
"""
import numpy as np
import scipy.stats as stats

print("=== GUMBEL DISTRIBUTION THEORY VERIFICATION ===")

# Standard Gumbel parameters
mu = 50.0    # location parameter
beta = 10.0  # scale parameter

print(f"Standard Gumbel: location μ={mu}, scale β={beta}")

# Generate sample to verify
np.random.seed(42)
sample = stats.gumbel_r.rvs(loc=mu, scale=beta, size=10000)
print(f"Large sample mean: {np.mean(sample):.3f} (should be ≈ {mu + beta * 0.5772:.3f})")
print(f"Large sample std: {np.std(sample):.3f} (should be ≈ {beta * np.pi / np.sqrt(6):.3f})")

print(f"\n=== RETURN PERIOD FORMULA VERIFICATION ===")

# Standard Gumbel return period formula
# Q_T = μ + β * ln(-ln(1-1/T)) for exceedance probability
# or Q_T = μ + β * ln(-ln(F)) where F = non-exceedance probability

return_periods = [2, 5, 10, 25, 50, 100]

print(f"{'T':<6}{'F (non-exceed)':<15}{'ln(-ln(F))':<12}{'Q_T formula':<12}{'ppf method':<12}{'Error %':<8}")
print("-" * 75)

for T in return_periods:
    # Non-exceedance probability F = 1 - 1/T
    F = 1 - 1/T
    
    # Gumbel reduced variate
    y = -np.log(-np.log(F))
    
    # Return level formula: Q_T = μ + β * y
    Q_formula = mu + beta * y
    
    # Using scipy ppf
    Q_ppf = stats.gumbel_r.ppf(F, loc=mu, scale=beta)
    
    # Error between methods
    error = abs(Q_formula - Q_ppf) / Q_formula * 100
    
    print(f"{T:<6}{F:<15.6f}{y:<12.3f}{Q_formula:<12.1f}{Q_ppf:<12.1f}{error:<8.2f}")

# Test with real fitted data
print(f"\n=== FITTED DATA VERIFICATION ===")

# Use smaller realistic sample
np.random.seed(12345)
fitted_data = stats.gumbel_r.rvs(loc=50, scale=10, size=50, random_state=12345)

# Fit parameters
params = stats.gumbel_r.fit(fitted_data)
fitted_mu, fitted_beta = params

print(f"Fitted parameters: μ={fitted_mu:.3f}, β={fitted_beta:.3f}")
print(f"True parameters:   μ={mu:.3f}, β={beta:.3f}")

# Calculate return periods with fitted parameters
print(f"\nReturn periods with fitted parameters:")
print(f"{'T':<6}{'Formula':<12}{'PPF':<12}{'Error %':<8}")
print("-" * 40)

for T in [10, 50, 100]:
    F = 1 - 1/T
    y = -np.log(-np.log(F))
    
    Q_formula = fitted_mu + fitted_beta * y
    Q_ppf = stats.gumbel_r.ppf(F, loc=fitted_mu, scale=fitted_beta)
    
    error = abs(Q_formula - Q_ppf) / Q_formula * 100
    
    print(f"{T:<6}{Q_formula:<12.1f}{Q_ppf:<12.1f}{error:<8.2f}")

# Expected values for T=100 with μ=50, β=10
print(f"\n=== EXPECTED T=100 CALCULATION ===")
T = 100
F = 1 - 1/T  # F = 0.99
y = -np.log(-np.log(F))  # y = -ln(-ln(0.99))
expected_Q100 = 50 + 10 * y

print(f"T = {T}")
print(f"Non-exceedance prob F = {F}")
print(f"Reduced variate y = -ln(-ln({F})) = {y:.3f}")
print(f"Expected Q_100 = {mu} + {beta} * {y:.3f} = {expected_Q100:.1f}")
print(f"PPF result = {stats.gumbel_r.ppf(F, loc=50, scale=10):.1f}")

# This should match the literature value
print(f"\nLiterature check:")
print(f"For standard Gumbel (μ=50, β=10), T=100 should give ≈ {expected_Q100:.1f}")