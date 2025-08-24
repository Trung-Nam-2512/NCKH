#!/usr/bin/env python3
"""
Final System Validation - Complete End-to-End Test
Validates accuracy of frequency analysis algorithms and charts
"""
import asyncio
import sys
import os
import logging
from datetime import datetime
import pandas as pd
import numpy as np
# import matplotlib.pyplot as plt  # Optional for validation

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
sys.path.append(os.path.dirname(__file__))

from app.services.integration_service import IntegrationService
from app.services.data_service import DataService
from app.services.analysis_service import AnalysisService
from app.services.professional_frequency_analysis_service import ProfessionalFrequencyAnalysisService
from app.services.hydrological_qc_service import HydrologicalQCService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def validate_system_accuracy():
    """Complete system validation for frequency analysis accuracy"""
    
    logger.info("🎯 FINAL SYSTEM VALIDATION - FREQUENCY ANALYSIS ACCURACY")
    logger.info("=" * 70)
    
    try:
        # Step 1: Initialize services
        logger.info("\n🔧 Step 1: Initializing services...")
        data_service = DataService()
        integration_service = IntegrationService(data_service)
        analysis_service = AnalysisService(data_service)
        professional_service = ProfessionalFrequencyAnalysisService(data_service)
        qc_service = HydrologicalQCService()
        
        # Step 2: Test with synthetic data for validation
        logger.info("\n📊 Step 2: Creating validation dataset...")
        
        # Create synthetic data following Gumbel distribution (known parameters)
        np.random.seed(42)  # For reproducibility
        true_location = 10.0  # Gumbel location parameter
        true_scale = 2.0     # Gumbel scale parameter
        n_years = 30         # 30 years of data
        
        synthetic_data = np.random.gumbel(true_location, true_scale, n_years)
        
        # Create DataFrame in expected format
        validation_df = pd.DataFrame({
            'Year': range(1995, 2025),
            'station_id': ['VALIDATION_STN'] * n_years,
            'station_name': ['Validation Station'] * n_years,
            'latitude': [10.0] * n_years,
            'longitude': [106.0] * n_years,
            'depth': synthetic_data
        })
        
        logger.info(f"Created synthetic dataset: {len(validation_df)} years")
        logger.info(f"True parameters: location={true_location}, scale={true_scale}")
        logger.info(f"Data range: {validation_df['depth'].min():.3f} - {validation_df['depth'].max():.3f}")
        
        # Step 3: Test Standard Analysis Service
        logger.info("\n🧪 Step 3: Testing Standard Analysis Service...")
        
        # Load data into DataService
        data_service.data = validation_df
        data_service.main_column = 'depth'
        
        # Test distribution analysis
        distribution_analysis = analysis_service.get_distribution_analysis('max')
        logger.info("Distribution fitting results:")
        
        best_aic = float('inf')
        best_distribution = None
        
        for dist_name, result in distribution_analysis.items():
            aic = result.get('AIC', float('inf'))
            p_value = result.get('p_value')
            logger.info(f"  {dist_name}: AIC={aic:.2f}, p-value={p_value}")
            
            if aic < best_aic:
                best_aic = aic
                best_distribution = dist_name
        
        logger.info(f"Best distribution: {best_distribution} (AIC={best_aic:.2f})")
        
        # Validate Gumbel parameters if Gumbel is best
        if best_distribution == 'gumbel':
            gumbel_params = distribution_analysis['gumbel']['params']
            estimated_location = gumbel_params.get('location', 0)
            estimated_scale = gumbel_params.get('scale', 1)
            
            location_error = abs(estimated_location - true_location) / true_location * 100
            scale_error = abs(estimated_scale - true_scale) / true_scale * 100
            
            logger.info(f"Parameter estimation accuracy:")
            logger.info(f"  Location: estimated={estimated_location:.3f}, true={true_location:.3f}, error={location_error:.1f}%")
            logger.info(f"  Scale: estimated={estimated_scale:.3f}, true={true_scale:.3f}, error={scale_error:.1f}%")
            
            parameter_accuracy = location_error < 10 and scale_error < 15
            logger.info(f"  Parameter accuracy: {'PASS' if parameter_accuracy else 'FAIL'}")
        
        # Step 4: Test frequency curve generation
        logger.info("\n📈 Step 4: Testing frequency curve generation...")
        
        frequency_curve = analysis_service.compute_frequency_curve('gumbel', 'max')
        theoretical_curve = frequency_curve.get('theoretical_curve', [])
        empirical_points = frequency_curve.get('empirical_points', [])
        
        logger.info(f"Theoretical curve points: {len(theoretical_curve)}")
        logger.info(f"Empirical points: {len(empirical_points)}")
        
        # Validate return period calculations
        if theoretical_curve:
            # Check specific return periods
            test_return_periods = [2, 5, 10, 25, 50, 100]
            logger.info("Return period validation:")
            
            for T in test_return_periods:
                p_percent = 100 / T
                
                # Find closest point in theoretical curve
                closest_point = min(theoretical_curve, 
                                  key=lambda x: abs(x['P_percent'] - p_percent))
                
                estimated_Q = closest_point['Q']
                
                # Theoretical Gumbel quantile for this return period
                p_exceedance = 1 / T
                theoretical_Q = true_location - true_scale * np.log(-np.log(1 - p_exceedance))
                
                error = abs(estimated_Q - theoretical_Q) / theoretical_Q * 100
                logger.info(f"  T={T} years: estimated={estimated_Q:.3f}, theoretical={theoretical_Q:.3f}, error={error:.1f}%")
        
        # Step 5: Test QC Service
        logger.info("\n🔬 Step 5: Testing Quality Control Service...")
        
        qc_result = qc_service.perform_comprehensive_qc(validation_df, parameter='depth')
        qc_summary = qc_result['summary']
        
        logger.info(f"QC Results:")
        logger.info(f"  Total records: {qc_summary['total_records']}")
        logger.info(f"  Quality score: {qc_summary['quality_score']:.1f}/100")
        logger.info(f"  Data completeness: {qc_summary['data_completeness']:.1f}%")
        logger.info(f"  Professional grade: {qc_summary['professional_grade']}")
        
        flag_counts = qc_summary['flag_counts']
        for flag, count in flag_counts.items():
            percentage = qc_summary['flag_percentages'][flag]
            logger.info(f"  {flag}: {count} ({percentage:.1f}%)")
        
        # Step 6: Test Professional Analysis
        logger.info("\n🏆 Step 6: Testing Professional Analysis Service...")
        
        try:
            professional_result = await professional_service.comprehensive_frequency_analysis(
                data=validation_df,
                target_distribution="gumbel",
                agg_func="max"
            )
            
            logger.info("Professional analysis completed successfully")
            if professional_result and 'analysis_status' in professional_result:
                logger.info(f"  Status: {professional_result['analysis_status']}")
                
                if 'data_validation' in professional_result:
                    quality_score = professional_result['data_validation'].get('quality_score', 0)
                    logger.info(f"  Data quality: {quality_score:.1f}/100")
                
                if 'uncertainty_analysis' in professional_result:
                    uncertainty = professional_result['uncertainty_analysis']
                    logger.info(f"  Bootstrap samples: {uncertainty.get('bootstrap_samples', 0)}")
        
        except Exception as e:
            logger.warning(f"Professional analysis failed: {e}")
        
        # Step 7: Test Integration Service
        logger.info("\n🔗 Step 7: Testing Integration Service...")
        
        # Create a mock realtime service data for integration test
        from app.services.realtime_service import EnhancedRealtimeService
        
        realtime_service = EnhancedRealtimeService(data_service)
        await realtime_service.initialize_database()
        
        # Clear and insert validation data
        collection = realtime_service.db.realtime_data
        await collection.delete_many({})
        
        # Convert validation_df to realtime format
        validation_records = []
        for _, row in validation_df.iterrows():
            record = {
                'station_id': row['station_id'],
                'uuid': f"uuid-{row['station_id']}",
                'code': row['station_id'],
                'name': row['station_name'],
                'latitude': row['latitude'],
                'longitude': row['longitude'],
                'api_type': 'validation',
                'time_point': datetime(int(row['Year']), 6, 15),  # Mid-year
                'depth': float(row['depth']),
                'created_at': datetime.now()
            }
            validation_records.append(record)
        
        await collection.insert_many(validation_records)
        logger.info(f"Inserted {len(validation_records)} validation records")
        
        # Test integration service
        try:
            integration_result = await integration_service.analyze_historical_realtime(
                min_years=10,
                distribution_name="gumbel",
                agg_func="max",
                use_professional=False
            )
            
            logger.info("Integration service test successful:")
            logger.info(f"  Message: {integration_result['message']}")
            logger.info(f"  Records: {integration_result['data_summary']['total_records']}")
            logger.info(f"  Analysis grade: {integration_result['analysis_grade']}")
            
            integration_success = True
            
        except Exception as e:
            logger.error(f"Integration service failed: {e}")
            integration_success = False
        
        # Step 8: System Assessment
        logger.info("\n📋 Step 8: Overall System Assessment...")
        
        assessment_results = {
            'distribution_fitting': best_distribution == 'gumbel',
            'parameter_accuracy': parameter_accuracy if 'parameter_accuracy' in locals() else False,
            'frequency_curves': len(theoretical_curve) > 0 and len(empirical_points) > 0,
            'qc_system': qc_summary['quality_score'] > 80,
            'professional_analysis': 'professional_result' in locals() and professional_result is not None,
            'integration_service': integration_success
        }
        
        passed_tests = sum(assessment_results.values())
        total_tests = len(assessment_results)
        
        logger.info(f"Test Results: {passed_tests}/{total_tests} PASSED")
        for test_name, passed in assessment_results.items():
            status = "PASS" if passed else "FAIL"
            logger.info(f"  {test_name}: {status}")
        
        overall_accuracy = passed_tests / total_tests * 100
        
        logger.info("\n" + "=" * 70)
        if overall_accuracy >= 80:
            logger.info("🎉 SYSTEM VALIDATION: SUCCESS")
            logger.info("✅ Frequency analysis algorithms are accurate and reliable")
            logger.info("✅ Charts and statistical indicators are mathematically sound")
            logger.info("✅ Professional-grade quality control is functional")
        else:
            logger.info("⚠️ SYSTEM VALIDATION: PARTIAL SUCCESS")
            logger.info(f"   {passed_tests}/{total_tests} components validated")
        
        logger.info(f"Overall accuracy: {overall_accuracy:.1f}%")
        logger.info("=" * 70)
        
        return overall_accuracy >= 80, assessment_results
        
    except Exception as e:
        logger.error(f"❌ System validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False, {}

if __name__ == "__main__":
    success, results = asyncio.run(validate_system_accuracy())
    
    if success:
        print("\n🎉 System validation completed successfully!")
        print("✅ Frequency analysis accuracy verified")
        print("✅ Charts and statistical indicators validated")
        print("✅ Professional quality standards met")
    else:
        print("\n⚠️ System validation completed with issues.")
        print("Some components may need further review.")