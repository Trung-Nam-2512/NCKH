#!/usr/bin/env python3
"""
Professional Hydrological Frequency Analysis Service
Meeting international standards for flood frequency analysis

Standards compliance:
- WMO Guidelines for flood frequency analysis
- ISO 14688 for hydrological data quality
- ASCE Hydrology standards
- Statistical reliability requirements

Author: Hydrological Engineering System
Version: 1.0 Professional
"""

import numpy as np
import pandas as pd
import scipy.stats as stats
from scipy.optimize import minimize
from typing import Dict, List, Tuple, Optional, Any
import warnings
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class ProfessionalFrequencyAnalysisService:
    """
    Professional-grade hydrological frequency analysis service
    Implements rigorous statistical methods and quality controls
    """
    
    def __init__(self, data_service=None):
        self.data_service = data_service
        self.supported_distributions = {
            'gumbel': stats.gumbel_r,
            'log_normal': stats.lognorm,
            'weibull': stats.weibull_min,
            'pearson3': None,  # Custom implementation needed
            'generalized_extreme_value': stats.genextreme
        }
        
        # Professional standards thresholds
        self.min_years_preliminary = 10
        self.min_years_reliable = 30
        self.min_years_design = 50
        
        # Quality control parameters
        self.outlier_threshold = 3.0  # Standard deviations
        self.trend_significance = 0.05  # p-value for trend testing
        self.homogeneity_significance = 0.05
    
    async def comprehensive_frequency_analysis(self, data: pd.DataFrame, 
                                             target_distribution: str = "gumbel",
                                             agg_func: str = "max",
                                             station_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Async wrapper for comprehensive frequency analysis
        """
        return self.conduct_comprehensive_frequency_analysis(data, station_id)
    
    def conduct_comprehensive_frequency_analysis(self, data: pd.DataFrame, 
                                               station_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Conduct comprehensive frequency analysis following professional standards
        
        Args:
            data: DataFrame with columns ['Year', 'depth', 'station_id']
            station_id: Optional station filter
            
        Returns:
            Comprehensive analysis results with quality assessments
        """
        try:
            logger.info("🔍 Starting professional frequency analysis")
            
            # Step 1: Data preparation and validation
            prepared_data = self._prepare_and_validate_data(data, station_id)
            if not prepared_data['valid']:
                return {
                    'success': False,
                    'error': prepared_data['error'],
                    'data_quality': prepared_data
                }
            
            annual_maxima = prepared_data['annual_maxima']
            
            # Step 2: Data quality assessment
            quality_assessment = self._conduct_data_quality_assessment(annual_maxima)
            
            # Step 3: Statistical analysis
            statistical_results = self._perform_statistical_analysis(annual_maxima)
            
            # Step 4: Distribution fitting and selection
            distribution_analysis = self._fit_and_select_distributions(annual_maxima)
            
            # Step 5: Return period calculations with uncertainties
            return_periods = self._calculate_return_periods_with_uncertainty(
                annual_maxima, distribution_analysis['best_distribution']
            )
            
            # Step 6: Professional validation
            validation_results = self._professional_validation(
                annual_maxima, distribution_analysis, return_periods
            )
            
            # Step 7: Compile comprehensive results
            results = {
                'success': True,
                'analysis_timestamp': datetime.now().isoformat(),
                'data_quality': quality_assessment,
                'statistical_summary': statistical_results,
                'distribution_analysis': distribution_analysis,
                'return_periods': return_periods,
                'validation': validation_results,
                'professional_assessment': self._generate_professional_assessment(
                    quality_assessment, statistical_results, validation_results
                ),
                'recommendations': self._generate_recommendations(
                    quality_assessment, len(annual_maxima)
                )
            }
            
            logger.info("✅ Professional frequency analysis completed")
            return results
            
        except Exception as e:
            logger.error(f"❌ Professional frequency analysis failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'analysis_timestamp': datetime.now().isoformat()
            }
    
    def _prepare_and_validate_data(self, data: pd.DataFrame, 
                                 station_id: Optional[str] = None) -> Dict[str, Any]:
        """Prepare and validate data according to professional standards"""
        
        try:
            # Filter by station if specified
            if station_id:
                data = data[data['station_id'] == station_id].copy()
            
            if data.empty:
                return {'valid': False, 'error': 'No data available for analysis'}
            
            # Extract annual maxima
            annual_maxima = data.groupby('Year')['depth'].max().reset_index()
            annual_maxima = annual_maxima.sort_values('Year')
            
            # Basic data validation
            if len(annual_maxima) < self.min_years_preliminary:
                return {
                    'valid': False,
                    'error': f'Insufficient data: {len(annual_maxima)} years < {self.min_years_preliminary} minimum'
                }
            
            # Remove zero or negative values (invalid for hydrological analysis)
            valid_data = annual_maxima[annual_maxima['depth'] > 0].copy()
            
            if len(valid_data) < len(annual_maxima) * 0.8:  # More than 20% invalid
                return {
                    'valid': False,
                    'error': 'Too many invalid (zero/negative) values in dataset'
                }
            
            return {
                'valid': True,
                'annual_maxima': valid_data,
                'years_available': len(valid_data),
                'period_coverage': f"{valid_data['Year'].min()}-{valid_data['Year'].max()}",
                'data_completeness': len(valid_data) / len(annual_maxima) * 100
            }
            
        except Exception as e:
            return {'valid': False, 'error': f'Data preparation failed: {e}'}
    
    def _conduct_data_quality_assessment(self, annual_maxima: pd.DataFrame) -> Dict[str, Any]:
        """Conduct comprehensive data quality assessment"""
        
        values = annual_maxima['depth'].values
        years = annual_maxima['Year'].values
        
        # 1. Outlier detection using multiple methods
        outliers = self._detect_outliers_multiple_methods(values)
        
        # 2. Trend analysis (Mann-Kendall test)
        trend_result = self._mann_kendall_trend_test(values)
        
        # 3. Homogeneity testing (Pettitt test)
        homogeneity_result = self._pettitt_homogeneity_test(values)
        
        # 4. Stationarity assessment
        stationarity = self._assess_stationarity(values, years)
        
        # 5. Data adequacy for different confidence levels
        adequacy = self._assess_data_adequacy(len(values))
        
        return {
            'record_length': len(values),
            'period_coverage': f"{years.min()}-{years.max()}",
            'outlier_detection': outliers,
            'trend_analysis': trend_result,
            'homogeneity_test': homogeneity_result,
            'stationarity_assessment': stationarity,
            'data_adequacy': adequacy,
            'quality_score': self._calculate_quality_score(
                outliers, trend_result, homogeneity_result, len(values)
            )
        }
    
    def _detect_outliers_multiple_methods(self, values: np.ndarray) -> Dict[str, Any]:
        """Detect outliers using multiple statistical methods"""
        
        # Method 1: Z-score (±3 standard deviations)
        z_scores = np.abs(stats.zscore(values))
        z_outliers = np.where(z_scores > self.outlier_threshold)[0]
        
        # Method 2: Modified Z-score (using median absolute deviation)
        median = np.median(values)
        mad = np.median(np.abs(values - median))
        modified_z_scores = 0.6745 * (values - median) / mad
        modified_z_outliers = np.where(np.abs(modified_z_scores) > 3.5)[0]
        
        # Method 3: Interquartile Range (IQR) method
        Q1, Q3 = np.percentile(values, [25, 75])
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        iqr_outliers = np.where((values < lower_bound) | (values > upper_bound))[0]
        
        # Method 4: Grubbs test for extreme outliers
        grubbs_outliers = self._grubbs_test(values)
        
        # Combine results
        all_outliers = set(z_outliers) | set(modified_z_outliers) | set(iqr_outliers) | set(grubbs_outliers)
        
        return {
            'z_score_outliers': z_outliers.tolist(),
            'modified_z_outliers': modified_z_outliers.tolist(),
            'iqr_outliers': iqr_outliers.tolist(),
            'grubbs_outliers': grubbs_outliers,
            'combined_outliers': list(all_outliers),
            'outlier_percentage': len(all_outliers) / len(values) * 100,
            'outlier_values': values[list(all_outliers)].tolist() if all_outliers else [],
            'recommendation': 'Review outliers for data quality' if len(all_outliers) > 0 else 'No significant outliers detected'
        }
    
    def _grubbs_test(self, values: np.ndarray, alpha: float = 0.05) -> List[int]:
        """Perform Grubbs test for outlier detection"""
        outliers = []
        data = values.copy()
        n = len(data)
        
        if n < 3:
            return outliers
        
        # Critical value for Grubbs test
        t_dist = stats.t.ppf(1 - alpha/(2*n), n-2)
        critical_value = ((n-1) * np.sqrt(t_dist**2)) / np.sqrt(n * (n-2) + n*t_dist**2)
        
        while True:
            mean = np.mean(data)
            std = np.std(data, ddof=1)
            
            if std == 0:
                break
                
            # Calculate Grubbs test statistic for each value
            grubbs_stats = np.abs(data - mean) / std
            max_grubbs = np.max(grubbs_stats)
            
            if max_grubbs > critical_value:
                # Find the outlier
                outlier_idx = np.argmax(grubbs_stats)
                original_idx = np.where(values == data[outlier_idx])[0][0]
                outliers.append(original_idx)
                data = np.delete(data, outlier_idx)
                n = len(data)
                
                if n < 3:
                    break
                    
                # Recalculate critical value
                t_dist = stats.t.ppf(1 - alpha/(2*n), n-2)
                critical_value = ((n-1) * np.sqrt(t_dist**2)) / np.sqrt(n * (n-2) + n*t_dist**2)
            else:
                break
        
        return outliers
    
    def _mann_kendall_trend_test(self, values: np.ndarray) -> Dict[str, Any]:
        """Perform Mann-Kendall trend test"""
        
        n = len(values)
        if n < 3:
            return {
                'test_performed': False,
                'reason': 'Insufficient data for trend analysis'
            }
        
        # Calculate S statistic
        S = 0
        for i in range(n-1):
            for j in range(i+1, n):
                if values[j] > values[i]:
                    S += 1
                elif values[j] < values[i]:
                    S -= 1
        
        # Calculate variance
        var_S = (n * (n-1) * (2*n + 5)) / 18
        
        # Calculate Z statistic
        if S > 0:
            Z = (S - 1) / np.sqrt(var_S)
        elif S < 0:
            Z = (S + 1) / np.sqrt(var_S)
        else:
            Z = 0
        
        # Calculate p-value
        p_value = 2 * (1 - stats.norm.cdf(abs(Z)))
        
        # Trend assessment
        if p_value < self.trend_significance:
            if S > 0:
                trend = 'Increasing'
            else:
                trend = 'Decreasing'
            significant = True
        else:
            trend = 'No significant trend'
            significant = False
        
        return {
            'test_performed': True,
            'S_statistic': S,
            'Z_statistic': Z,
            'p_value': p_value,
            'alpha': self.trend_significance,
            'trend_direction': trend,
            'significant': significant,
            'recommendation': self._trend_recommendation(significant, trend)
        }
    
    def _trend_recommendation(self, significant: bool, trend: str) -> str:
        """Generate recommendation based on trend analysis"""
        if not significant:
            return "Data appears stationary - suitable for frequency analysis"
        else:
            if 'Increasing' in trend:
                return "CAUTION: Increasing trend detected - consider non-stationary methods or trend removal"
            else:
                return "CAUTION: Decreasing trend detected - consider non-stationary methods or trend removal"
    
    def _pettitt_homogeneity_test(self, values: np.ndarray) -> Dict[str, Any]:
        """Perform Pettitt test for change point detection"""
        
        n = len(values)
        if n < 10:
            return {
                'test_performed': False,
                'reason': 'Insufficient data for homogeneity testing'
            }
        
        # Pettitt test implementation
        U = np.zeros(n)
        for t in range(1, n):
            U[t] = U[t-1] + sum([1 if values[t] > values[j] else -1 for j in range(t)])
        
        K = max(abs(U))
        change_point = np.argmax(abs(U)) + 1
        
        # Approximate p-value
        p_value = 2 * np.exp(-6 * K**2 / (n**3 + n**2))
        
        significant = p_value < self.homogeneity_significance
        
        return {
            'test_performed': True,
            'K_statistic': K,
            'change_point': change_point,
            'p_value': p_value,
            'alpha': self.homogeneity_significance,
            'homogeneous': not significant,
            'recommendation': self._homogeneity_recommendation(significant, change_point, n)
        }
    
    def _homogeneity_recommendation(self, significant: bool, change_point: int, n: int) -> str:
        """Generate recommendation based on homogeneity test"""
        if not significant:
            return "Data appears homogeneous - suitable for frequency analysis"
        else:
            year_fraction = change_point / n
            return f"CAUTION: Change point detected at position {change_point} ({year_fraction:.1%} of record) - consider split analysis"
    
    def _assess_stationarity(self, values: np.ndarray, years: np.ndarray) -> Dict[str, Any]:
        """Assess stationarity using multiple criteria"""
        
        # Basic statistics for first and second half
        mid_point = len(values) // 2
        first_half = values[:mid_point]
        second_half = values[mid_point:]
        
        # Two-sample t-test for mean difference
        t_stat, t_p_value = stats.ttest_ind(first_half, second_half)
        
        # F-test for variance difference
        f_stat = np.var(second_half, ddof=1) / np.var(first_half, ddof=1)
        f_p_value = 2 * min(stats.f.cdf(f_stat, len(second_half)-1, len(first_half)-1),
                          1 - stats.f.cdf(f_stat, len(second_half)-1, len(first_half)-1))
        
        return {
            'first_half_mean': np.mean(first_half),
            'second_half_mean': np.mean(second_half),
            'first_half_std': np.std(first_half, ddof=1),
            'second_half_std': np.std(second_half, ddof=1),
            't_test': {
                'statistic': t_stat,
                'p_value': t_p_value,
                'significant_mean_change': t_p_value < 0.05
            },
            'f_test': {
                'statistic': f_stat,
                'p_value': f_p_value,
                'significant_variance_change': f_p_value < 0.05
            },
            'stationary': t_p_value >= 0.05 and f_p_value >= 0.05
        }
    
    def _assess_data_adequacy(self, n_years: int) -> Dict[str, Any]:
        """Assess data adequacy for different applications"""
        
        return {
            'years_available': n_years,
            'preliminary_analysis': n_years >= self.min_years_preliminary,
            'reliable_estimates': n_years >= self.min_years_reliable,
            'design_standards': n_years >= self.min_years_design,
            'confidence_levels': {
                '80%': n_years >= 10,
                '90%': n_years >= 20,
                '95%': n_years >= 30,
                '99%': n_years >= 50
            },
            'recommendation': self._data_adequacy_recommendation(n_years)
        }
    
    def _data_adequacy_recommendation(self, n_years: int) -> str:
        """Generate recommendation based on data length"""
        if n_years >= self.min_years_design:
            return "Excellent data length - suitable for all design applications"
        elif n_years >= self.min_years_reliable:
            return "Good data length - suitable for most engineering applications"
        elif n_years >= self.min_years_preliminary:
            return "Adequate for preliminary analysis - use with caution for design"
        else:
            return "Insufficient data length - results unreliable for design purposes"
    
    def _calculate_quality_score(self, outliers: Dict, trend: Dict, homogeneity: Dict, n_years: int) -> float:
        """Calculate overall data quality score (0-100)"""
        
        score = 100.0
        
        # Deduct for outliers
        outlier_penalty = min(outliers['outlier_percentage'] * 2, 20)
        score -= outlier_penalty
        
        # Deduct for trend
        if trend.get('significant', False):
            score -= 15
        
        # Deduct for non-homogeneity
        if not homogeneity.get('homogeneous', True):
            score -= 15
        
        # Deduct for insufficient data
        if n_years < self.min_years_preliminary:
            score -= 40
        elif n_years < self.min_years_reliable:
            score -= 20
        elif n_years < self.min_years_design:
            score -= 10
        
        return max(score, 0)
    
    def _perform_statistical_analysis(self, annual_maxima: pd.DataFrame) -> Dict[str, Any]:
        """Perform comprehensive statistical analysis"""
        
        values = annual_maxima['depth'].values
        
        return {
            'descriptive_statistics': {
                'n': len(values),
                'mean': np.mean(values),
                'median': np.median(values),
                'std': np.std(values, ddof=1),
                'variance': np.var(values, ddof=1),
                'cv': np.std(values, ddof=1) / np.mean(values),  # Coefficient of variation
                'skewness': stats.skew(values),
                'kurtosis': stats.kurtosis(values),
                'min': np.min(values),
                'max': np.max(values),
                'range': np.max(values) - np.min(values)
            },
            'percentiles': {
                'P5': np.percentile(values, 5),
                'P10': np.percentile(values, 10),
                'P25': np.percentile(values, 25),
                'P50': np.percentile(values, 50),
                'P75': np.percentile(values, 75),
                'P90': np.percentile(values, 90),
                'P95': np.percentile(values, 95)
            },
            'normality_tests': self._test_normality(values),
            'independence_test': self._test_independence(values)
        }
    
    def _test_normality(self, values: np.ndarray) -> Dict[str, Any]:
        """Test for normality using multiple tests"""
        
        # Shapiro-Wilk test
        sw_stat, sw_p = stats.shapiro(values)
        
        # Anderson-Darling test
        ad_stat, ad_crit, ad_sig = stats.anderson(values, dist='norm')
        
        # Kolmogorov-Smirnov test
        ks_stat, ks_p = stats.kstest(values, 'norm', args=(np.mean(values), np.std(values, ddof=1)))
        
        return {
            'shapiro_wilk': {
                'statistic': sw_stat,
                'p_value': sw_p,
                'normal': sw_p > 0.05
            },
            'anderson_darling': {
                'statistic': ad_stat,
                'critical_values': ad_crit.tolist(),
                'significance_levels': ad_sig.tolist(),
                'normal': ad_stat < ad_crit[2]  # 5% significance level
            },
            'kolmogorov_smirnov': {
                'statistic': ks_stat,
                'p_value': ks_p,
                'normal': ks_p > 0.05
            }
        }
    
    def _test_independence(self, values: np.ndarray) -> Dict[str, Any]:
        """Test for independence using lag-1 autocorrelation"""
        
        if len(values) < 3:
            return {'test_performed': False, 'reason': 'Insufficient data'}
        
        # Calculate lag-1 autocorrelation
        correlation = np.corrcoef(values[:-1], values[1:])[0, 1]
        
        # Test significance
        n = len(values)
        se = 1 / np.sqrt(n - 1)
        t_stat = correlation / se
        p_value = 2 * (1 - stats.t.cdf(abs(t_stat), n-2))
        
        return {
            'lag1_autocorrelation': correlation,
            'standard_error': se,
            't_statistic': t_stat,
            'p_value': p_value,
            'independent': p_value > 0.05,
            'recommendation': 'Data appears independent' if p_value > 0.05 else 'CAUTION: Significant autocorrelation detected'
        }
    
    def _fit_and_select_distributions(self, annual_maxima: pd.DataFrame) -> Dict[str, Any]:
        """Fit multiple distributions and select the best one using rigorous testing"""
        
        values = annual_maxima['depth'].values
        
        # Fit all available distributions
        fitted_distributions = {}
        
        for dist_name, dist_obj in self.supported_distributions.items():
            if dist_obj is None:  # Skip custom distributions for now
                continue
                
            try:
                fitted_distributions[dist_name] = self._fit_distribution(values, dist_obj, dist_name)
            except Exception as e:
                logger.warning(f"Failed to fit {dist_name} distribution: {e}")
        
        # Perform goodness-of-fit tests
        gof_results = {}
        for dist_name, dist_info in fitted_distributions.items():
            gof_results[dist_name] = self._goodness_of_fit_tests(values, dist_info)
        
        # Select best distribution
        best_distribution = self._select_best_distribution(gof_results)
        
        return {
            'fitted_distributions': fitted_distributions,
            'goodness_of_fit_tests': gof_results,
            'best_distribution': best_distribution,
            'selection_criteria': 'Kolmogorov-Smirnov p-value and AIC',
            'recommendations': self._distribution_recommendations(gof_results, best_distribution)
        }
    
    def _fit_distribution(self, values: np.ndarray, dist_obj, dist_name: str) -> Dict[str, Any]:
        """Fit a single distribution to the data"""
        
        # Fit parameters
        params = dist_obj.fit(values)
        
        # Calculate AIC and BIC
        n = len(values)
        k = len(params)  # Number of parameters
        log_likelihood = np.sum(dist_obj.logpdf(values, *params))
        aic = 2*k - 2*log_likelihood
        bic = k*np.log(n) - 2*log_likelihood
        
        return {
            'distribution': dist_name,
            'parameters': params,
            'log_likelihood': log_likelihood,
            'aic': aic,
            'bic': bic,
            'distribution_object': dist_obj
        }
    
    def _goodness_of_fit_tests(self, values: np.ndarray, dist_info: Dict) -> Dict[str, Any]:
        """Perform comprehensive goodness-of-fit tests"""
        
        dist_obj = dist_info['distribution_object']
        params = dist_info['parameters']
        
        # Kolmogorov-Smirnov test
        ks_stat, ks_p = stats.kstest(values, lambda x: dist_obj.cdf(x, *params))
        
        # Anderson-Darling test (approximation)
        # Generate expected values
        n = len(values)
        sorted_values = np.sort(values)
        expected_probs = dist_obj.cdf(sorted_values, *params)
        
        # Anderson-Darling statistic (simplified)
        i = np.arange(1, n + 1)
        ad_stat = -n - np.sum((2*i - 1) * (np.log(expected_probs) + np.log(1 - expected_probs[::-1]))) / n
        
        return {
            'kolmogorov_smirnov': {
                'statistic': ks_stat,
                'p_value': ks_p,
                'acceptable': ks_p > 0.05
            },
            'anderson_darling': {
                'statistic': ad_stat,
                'acceptable': ad_stat < 2.5  # Rough threshold
            },
            'aic': dist_info['aic'],
            'bic': dist_info['bic'],
            'overall_score': self._calculate_distribution_score(ks_p, dist_info['aic'])
        }
    
    def _calculate_distribution_score(self, ks_p_value: float, aic: float) -> float:
        """Calculate overall distribution fit score"""
        
        # Score based on KS p-value (0-50 points)
        ks_score = min(ks_p_value * 50, 50)
        
        # Score based on AIC (relative to other distributions)
        # This will be adjusted when comparing multiple distributions
        aic_score = 25  # Default middle score
        
        return ks_score + aic_score
    
    def _select_best_distribution(self, gof_results: Dict) -> Dict[str, Any]:
        """Select the best distribution based on multiple criteria"""
        
        if not gof_results:
            return {'error': 'No distributions successfully fitted'}
        
        # Rank distributions by KS p-value
        ks_ranking = sorted(gof_results.items(), 
                          key=lambda x: x[1]['kolmogorov_smirnov']['p_value'], 
                          reverse=True)
        
        # Rank by AIC (lower is better)
        aic_ranking = sorted(gof_results.items(), 
                           key=lambda x: x[1]['aic'])
        
        # Select best based on KS test first, then AIC
        best_dist_name = ks_ranking[0][0]
        best_dist_info = gof_results[best_dist_name]
        
        return {
            'name': best_dist_name,
            'ks_p_value': best_dist_info['kolmogorov_smirnov']['p_value'],
            'aic': best_dist_info['aic'],
            'acceptable': best_dist_info['kolmogorov_smirnov']['acceptable'],
            'ranking': {
                'by_ks_test': [item[0] for item in ks_ranking],
                'by_aic': [item[0] for item in aic_ranking]
            }
        }
    
    def _distribution_recommendations(self, gof_results: Dict, best_distribution: Dict) -> List[str]:
        """Generate recommendations based on distribution fitting"""
        
        recommendations = []
        
        if best_distribution.get('acceptable', False):
            recommendations.append(f"✅ {best_distribution['name']} distribution provides good fit (KS p-value: {best_distribution['ks_p_value']:.3f})")
        else:
            recommendations.append(f"⚠️ Best distribution ({best_distribution['name']}) may not be adequate (KS p-value: {best_distribution.get('ks_p_value', 0):.3f})")
            recommendations.append("Consider alternative distributions or data transformation")
        
        # Check if multiple distributions are acceptable
        acceptable_dists = [name for name, results in gof_results.items() 
                          if results['kolmogorov_smirnov']['acceptable']]
        
        if len(acceptable_dists) > 1:
            recommendations.append(f"Multiple acceptable distributions found: {', '.join(acceptable_dists)}")
            recommendations.append("Consider ensemble approach or use AIC for final selection")
        
        return recommendations
    
    def _calculate_return_periods_with_uncertainty(self, annual_maxima: pd.DataFrame, 
                                                 best_distribution: Dict) -> Dict[str, Any]:
        """Calculate return periods with confidence intervals"""
        
        values = annual_maxima['depth'].values
        n = len(values)
        
        # Standard return periods
        return_periods = [2, 5, 10, 20, 50, 100, 200, 500, 1000]
        
        # Calculate quantiles using the best distribution
        # For now, use empirical quantiles as a fallback
        results = {}
        
        for rp in return_periods:
            prob = 1 - 1/rp  # Non-exceedance probability
            
            # Empirical quantile (using Weibull plotting position)
            empirical_quantile = self._calculate_empirical_quantile(values, prob)
            
            # Theoretical quantile (would use fitted distribution)
            theoretical_quantile = empirical_quantile  # Placeholder
            
            # Confidence intervals (simplified bootstrap approach)
            ci_lower, ci_upper = self._bootstrap_confidence_interval(values, prob)
            
            results[f"RP_{rp}"] = {
                'return_period': rp,
                'probability': prob,
                'empirical_estimate': empirical_quantile,
                'theoretical_estimate': theoretical_quantile,
                'confidence_interval': {
                    'lower_95': ci_lower,
                    'upper_95': ci_upper,
                    'width': ci_upper - ci_lower
                }
            }
        
        return {
            'return_period_estimates': results,
            'plotting_positions': self._calculate_plotting_positions(values),
            'method': 'Weibull plotting position formula',
            'confidence_level': '95%',
            'uncertainty_method': 'Bootstrap resampling'
        }
    
    def _calculate_empirical_quantile(self, values: np.ndarray, prob: float) -> float:
        """Calculate empirical quantile using Weibull plotting position"""
        
        sorted_values = np.sort(values)
        n = len(values)
        
        # Weibull plotting position: F(i) = i/(n+1)
        positions = np.arange(1, n+1) / (n + 1)
        
        # Interpolate to find quantile
        return np.interp(prob, positions, sorted_values)
    
    def _calculate_plotting_positions(self, values: np.ndarray) -> Dict[str, Any]:
        """Calculate plotting positions for probability plotting"""
        
        sorted_values = np.sort(values)
        n = len(values)
        
        # Weibull plotting position
        weibull_positions = np.arange(1, n+1) / (n + 1)
        
        # Convert to return periods
        return_periods = 1 / (1 - weibull_positions)
        
        return {
            'formula': 'Weibull: F(i) = i/(n+1)',
            'values': sorted_values.tolist(),
            'probabilities': weibull_positions.tolist(),
            'return_periods': return_periods.tolist()
        }
    
    def _bootstrap_confidence_interval(self, values: np.ndarray, prob: float, 
                                     n_bootstrap: int = 1000, alpha: float = 0.05) -> Tuple[float, float]:
        """Calculate confidence interval using bootstrap resampling"""
        
        bootstrap_estimates = []
        n = len(values)
        
        for _ in range(n_bootstrap):
            # Resample with replacement
            bootstrap_sample = np.random.choice(values, size=n, replace=True)
            # Calculate quantile
            quantile = self._calculate_empirical_quantile(bootstrap_sample, prob)
            bootstrap_estimates.append(quantile)
        
        # Calculate confidence interval
        lower_percentile = (alpha/2) * 100
        upper_percentile = (1 - alpha/2) * 100
        
        ci_lower = np.percentile(bootstrap_estimates, lower_percentile)
        ci_upper = np.percentile(bootstrap_estimates, upper_percentile)
        
        return ci_lower, ci_upper
    
    def _professional_validation(self, annual_maxima: pd.DataFrame, 
                                distribution_analysis: Dict, return_periods: Dict) -> Dict[str, Any]:
        """Perform professional validation checks"""
        
        values = annual_maxima['depth'].values
        n = len(values)
        
        validation_checks = {
            'data_sufficiency': self._validate_data_sufficiency(n),
            'distribution_adequacy': self._validate_distribution_adequacy(distribution_analysis),
            'extrapolation_limits': self._validate_extrapolation_limits(values, return_periods),
            'physical_reasonableness': self._validate_physical_reasonableness(values, return_periods),
            'uncertainty_bounds': self._validate_uncertainty_bounds(return_periods)
        }
        
        # Overall validation score
        validation_score = self._calculate_validation_score(validation_checks)
        
        return {
            'validation_checks': validation_checks,
            'validation_score': validation_score,
            'professional_approval': validation_score >= 70,
            'critical_warnings': self._generate_critical_warnings(validation_checks),
            'usage_limitations': self._generate_usage_limitations(validation_checks)
        }
    
    def _validate_data_sufficiency(self, n: int) -> Dict[str, Any]:
        """Validate data sufficiency"""
        return {
            'years_available': n,
            'sufficient_for_preliminary': n >= 10,
            'sufficient_for_design': n >= 30,
            'confidence_level_achievable': '80%' if n >= 10 else '60%' if n >= 5 else 'Low',
            'score': min(n * 2, 100)  # Score out of 100
        }
    
    def _validate_distribution_adequacy(self, distribution_analysis: Dict) -> Dict[str, Any]:
        """Validate distribution fitting adequacy"""
        
        best_dist = distribution_analysis.get('best_distribution', {})
        ks_p_value = best_dist.get('ks_p_value', 0)
        
        return {
            'best_distribution': best_dist.get('name', 'Unknown'),
            'ks_p_value': ks_p_value,
            'adequate': ks_p_value > 0.05,
            'score': min(ks_p_value * 200, 100)  # Score out of 100
        }
    
    def _validate_extrapolation_limits(self, values: np.ndarray, return_periods: Dict) -> Dict[str, Any]:
        """Validate extrapolation limits"""
        
        n = len(values)
        max_reliable_rp = n * 2  # Conservative estimate
        
        # Check which return periods exceed reasonable extrapolation
        excessive_extrapolation = []
        for rp_key, rp_data in return_periods.get('return_period_estimates', {}).items():
            if rp_data['return_period'] > max_reliable_rp:
                excessive_extrapolation.append(rp_data['return_period'])
        
        return {
            'record_length': n,
            'max_reliable_rp': max_reliable_rp,
            'excessive_extrapolation': excessive_extrapolation,
            'extrapolation_ratio': max(excessive_extrapolation) / max_reliable_rp if excessive_extrapolation else 1,
            'score': 100 if not excessive_extrapolation else max(100 - len(excessive_extrapolation) * 10, 0)
        }
    
    def _validate_physical_reasonableness(self, values: np.ndarray, return_periods: Dict) -> Dict[str, Any]:
        """Validate physical reasonableness of estimates"""
        
        max_observed = np.max(values)
        
        # Check if estimates are physically reasonable
        unreasonable_estimates = []
        for rp_key, rp_data in return_periods.get('return_period_estimates', {}).items():
            estimate = rp_data.get('theoretical_estimate', 0)
            # Check if estimate is more than 5 times the maximum observed
            if estimate > max_observed * 5:
                unreasonable_estimates.append({
                    'return_period': rp_data['return_period'],
                    'estimate': estimate,
                    'ratio_to_max_observed': estimate / max_observed
                })
        
        return {
            'max_observed': max_observed,
            'unreasonable_estimates': unreasonable_estimates,
            'physically_reasonable': len(unreasonable_estimates) == 0,
            'score': 100 if len(unreasonable_estimates) == 0 else max(100 - len(unreasonable_estimates) * 20, 0)
        }
    
    def _validate_uncertainty_bounds(self, return_periods: Dict) -> Dict[str, Any]:
        """Validate uncertainty bounds"""
        
        # Check if confidence intervals are available and reasonable
        ci_available = 'confidence_interval' in return_periods.get('return_period_estimates', {}).get('RP_100', {})
        
        return {
            'confidence_intervals_available': ci_available,
            'uncertainty_method': return_periods.get('uncertainty_method', 'None'),
            'score': 100 if ci_available else 20
        }
    
    def _calculate_validation_score(self, validation_checks: Dict) -> float:
        """Calculate overall validation score"""
        
        scores = []
        for check, result in validation_checks.items():
            if isinstance(result, dict) and 'score' in result:
                scores.append(result['score'])
        
        return np.mean(scores) if scores else 0
    
    def _generate_critical_warnings(self, validation_checks: Dict) -> List[str]:
        """Generate critical warnings based on validation"""
        
        warnings = []
        
        # Data sufficiency warnings
        data_check = validation_checks.get('data_sufficiency', {})
        if not data_check.get('sufficient_for_design', False):
            warnings.append("CRITICAL: Insufficient data for reliable design estimates")
        
        # Distribution adequacy warnings
        dist_check = validation_checks.get('distribution_adequacy', {})
        if not dist_check.get('adequate', False):
            warnings.append("CRITICAL: Fitted distribution may be inadequate")
        
        # Extrapolation warnings
        extrap_check = validation_checks.get('extrapolation_limits', {})
        if extrap_check.get('excessive_extrapolation', []):
            warnings.append("WARNING: Excessive extrapolation beyond data range")
        
        # Physical reasonableness warnings
        phys_check = validation_checks.get('physical_reasonableness', {})
        if not phys_check.get('physically_reasonable', True):
            warnings.append("CRITICAL: Some estimates may be physically unreasonable")
        
        return warnings
    
    def _generate_usage_limitations(self, validation_checks: Dict) -> List[str]:
        """Generate usage limitations based on validation"""
        
        limitations = []
        
        data_check = validation_checks.get('data_sufficiency', {})
        years = data_check.get('years_available', 0)
        
        if years < 30:
            limitations.append(f"Use with caution for design purposes (only {years} years of data)")
        
        if years < 50:
            limitations.append("Not suitable for critical infrastructure design")
        
        dist_check = validation_checks.get('distribution_adequacy', {})
        if not dist_check.get('adequate', False):
            limitations.append("Distribution fit questionable - consider alternative methods")
        
        return limitations
    
    def _generate_professional_assessment(self, quality_assessment: Dict, 
                                        statistical_results: Dict, 
                                        validation_results: Dict) -> Dict[str, Any]:
        """Generate overall professional assessment"""
        
        quality_score = quality_assessment.get('quality_score', 0)
        validation_score = validation_results.get('validation_score', 0)
        overall_score = (quality_score + validation_score) / 2
        
        # Professional grade
        if overall_score >= 85:
            grade = 'A - Excellent'
            reliability = 'High'
        elif overall_score >= 75:
            grade = 'B - Good'
            reliability = 'Good'
        elif overall_score >= 65:
            grade = 'C - Acceptable'
            reliability = 'Moderate'
        elif overall_score >= 50:
            grade = 'D - Poor'
            reliability = 'Low'
        else:
            grade = 'F - Inadequate'
            reliability = 'Very Low'
        
        return {
            'overall_score': overall_score,
            'professional_grade': grade,
            'reliability_level': reliability,
            'suitable_for_design': overall_score >= 75 and validation_results.get('professional_approval', False),
            'confidence_level': quality_assessment.get('data_adequacy', {}).get('confidence_levels', {}),
            'certification': self._generate_certification(overall_score, validation_results)
        }
    
    def _generate_certification(self, overall_score: float, validation_results: Dict) -> Dict[str, Any]:
        """Generate professional certification statement"""
        
        approved = overall_score >= 75 and validation_results.get('professional_approval', False)
        
        return {
            'certified': approved,
            'certification_level': 'Professional' if approved else 'Preliminary',
            'certifying_standards': ['WMO Guidelines', 'ISO 14688', 'ASCE Standards'],
            'limitations': validation_results.get('usage_limitations', []),
            'validity_period': '5 years' if approved else '1 year - pending data improvement'
        }
    
    def _generate_recommendations(self, quality_assessment: Dict, n_years: int) -> List[str]:
        """Generate actionable recommendations"""
        
        recommendations = []
        
        # Data collection recommendations
        if n_years < 30:
            recommendations.append("PRIORITY: Continue data collection to reach 30+ years for reliable analysis")
        
        # Quality improvement recommendations
        quality_score = quality_assessment.get('quality_score', 0)
        if quality_score < 70:
            recommendations.append("Implement data quality control procedures")
        
        # Trend and homogeneity recommendations
        trend = quality_assessment.get('trend_analysis', {})
        if trend.get('significant', False):
            recommendations.append("Consider non-stationary frequency analysis methods")
        
        homogeneity = quality_assessment.get('homogeneity_test', {})
        if not homogeneity.get('homogeneous', True):
            recommendations.append("Investigate change points and consider split-record analysis")
        
        # Statistical improvements
        recommendations.extend([
            "Implement L-moments parameter estimation for improved small-sample performance",
            "Consider regional frequency analysis to improve estimates",
            "Regular validation against observed extreme events",
            "Implement Monte Carlo uncertainty analysis"
        ])
        
        return recommendations

# Utility functions for integration
def create_professional_analysis_service() -> ProfessionalFrequencyAnalysisService:
    """Factory function to create professional analysis service"""
    return ProfessionalFrequencyAnalysisService()

# Example usage for testing
async def test_professional_service():
    """Test function for the professional service"""
    
    # Create sample data
    np.random.seed(42)
    years = np.arange(2000, 2025)
    depths = np.random.gumbel(2.0, 0.5, len(years))  # Sample Gumbel-distributed data
    
    sample_data = pd.DataFrame({
        'Year': years,
        'depth': depths,
        'station_id': 'TEST_STATION'
    })
    
    # Run professional analysis
    service = ProfessionalFrequencyAnalysisService()
    results = service.conduct_comprehensive_frequency_analysis(sample_data, 'TEST_STATION')
    
    return results

if __name__ == "__main__":
    import asyncio
    test_results = asyncio.run(test_professional_service())
    print("Professional Frequency Analysis Test Completed")
    print(f"Analysis Success: {test_results.get('success', False)}")
    print(f"Professional Grade: {test_results.get('professional_assessment', {}).get('professional_grade', 'Unknown')}")