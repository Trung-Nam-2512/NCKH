"""
Complete Analysis Router - Tích hợp workflow hoàn chỉnh như user đã làm
Sử dụng existing services để tạo complete analysis workflow
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from typing import Optional, List, Dict, Any
import logging
import asyncio
import base64
import io
from ..dependencies import get_data_service, get_analysis_service
from ..services.data_service import DataService
from ..services.analysis_service import AnalysisService

router = APIRouter(prefix="/complete", tags=["complete_analysis"])

@router.post("/full-frequency-analysis")
async def perform_full_frequency_analysis(
    agg_func: str = Query("max", description="Hàm tổng hợp (max, min, mean)"),
    include_all_distributions: bool = Query(True, description="Bao gồm tất cả phân phối"),
    data_service: DataService = Depends(get_data_service),
    analysis_service: AnalysisService = Depends(get_analysis_service)
):
    """
    Thực hiện phân tích tần suất hoàn chỉnh như workflow user đã làm:
    1. Phân tích tất cả phân phối và tìm tốt nhất
    2. Tạo frequency curves cho tất cả phân phối
    3. Tạo QQ/PP plots
    4. Bảng tần suất và return periods
    5. Tổng hợp tất cả kết quả
    """
    
    if data_service.data is None:
        raise HTTPException(status_code=404, detail="Chưa có dữ liệu được tải. Vui lòng upload file trước.")
    
    try:
        # Bước 1: Phân tích phân phối - giống như user đã làm
        logging.info(f"🔍 Starting distribution analysis with agg_func={agg_func}")
        distribution_analysis = analysis_service.get_distribution_analysis(agg_func)
        
        # Tìm phân phối tốt nhất
        valid_distributions = {
            name: result for name, result in distribution_analysis.items()
            if result.get('AIC', float('inf')) != float('inf')
        }
        
        if not valid_distributions:
            raise HTTPException(status_code=400, detail="Không thể fit được phân phối nào")
        
        best_distribution = min(valid_distributions.items(), key=lambda x: x[1]['AIC'])
        best_dist_name = best_distribution[0]
        best_dist_info = best_distribution[1]
        
        logging.info(f"✅ Best distribution found: {best_dist_name} (AIC: {best_dist_info['AIC']:.2f})")
        
        # Bước 2: Tạo frequency curves cho tất cả phân phối - như user đã làm
        logging.info("📈 Generating frequency curves for all distributions")
        frequency_curves = {}
        
        # Danh sách phân phối chính như user đã implement
        main_distributions = ['gumbel', 'lognorm', 'gamma', 'logistic', 'expon', 'genpareto', 'frechet', 'pearson3', 'genextreme']
        
        if include_all_distributions:
            distributions_to_process = main_distributions
        else:
            distributions_to_process = [best_dist_name]
        
        for dist_name in distributions_to_process:
            if dist_name in valid_distributions:
                try:
                    curve_data = analysis_service.compute_frequency_curve(dist_name, agg_func)
                    frequency_curves[dist_name] = {
                        "distribution_name": dist_name,
                        "display_name": dist_name.capitalize(),
                        "curve_data": curve_data,
                        "statistics": {
                            "aic": valid_distributions[dist_name]['AIC'],
                            "p_value": valid_distributions[dist_name].get('p_value'),
                            "chi_square": valid_distributions[dist_name].get('ChiSquare'),
                            "parameters": valid_distributions[dist_name].get('params', {})
                        },
                        "is_best": dist_name == best_dist_name
                    }
                    logging.info(f"✅ Generated frequency curve for {dist_name}")
                except Exception as e:
                    logging.warning(f"⚠️ Could not generate curve for {dist_name}: {e}")
        
        # Bước 3: QQ/PP plots cho phân phối tốt nhất
        logging.info(f"📊 Generating QQ/PP plots for best distribution: {best_dist_name}")
        qq_pp_data = analysis_service.compute_qq_pp(best_dist_name, agg_func)
        
        # Bước 4: Bảng tần suất cơ bản
        logging.info("📋 Generating frequency analysis table")
        frequency_table = analysis_service.get_frequency_analysis()
        
        # Bước 5: Bảng tần suất theo mô hình tốt nhất
        logging.info(f"📋 Generating frequency table by best model: {best_dist_name}")
        frequency_by_model = analysis_service.get_frequency_by_model(best_dist_name, agg_func)
        
        # Bước 6: Tính toán return periods quan trọng
        logging.info("🔢 Calculating important return periods")
        important_return_periods = [2, 5, 10, 25, 50, 100]
        return_periods_analysis = []
        
        if frequency_by_model.get('theoretical_curve'):
            for period in important_return_periods:
                freq_percent = 100 / period
                # Tìm điểm gần nhất trong theoretical curve
                closest_point = min(frequency_by_model['theoretical_curve'],
                                  key=lambda x: abs(float(x['Tần suất P(%)']) - freq_percent))
                
                return_periods_analysis.append({
                    "return_period_years": period,
                    "frequency_percent": freq_percent,
                    "discharge_value": closest_point['Lưu lượng dòng chảy Q m³/s'],
                    "return_time": closest_point['Thời gian lặp lại (năm)'],
                    "exceedance_probability": freq_percent / 100
                })
        
        # Bước 7: Metadata và data summary
        df = data_service.data
        main_column = data_service.main_column
        
        annual_data = df.groupby('Year')[main_column].agg(['min', 'max', 'mean', 'std', 'count'])
        
        data_summary = {
            "data_info": {
                "total_records": len(df),
                "years_count": len(annual_data),
                "year_range": {
                    "start": int(df['Year'].min()),
                    "end": int(df['Year'].max())
                },
                "main_column": main_column,
                "has_monthly_data": "Month" in df.columns,
                "analysis_type": agg_func.upper()
            },
            "annual_statistics": {
                "min_value": float(annual_data['min'].min()),
                "max_value": float(annual_data['max'].max()),
                "mean_annual_max": float(annual_data['max'].mean()),
                "std_annual_max": float(annual_data['max'].std())
            }
        }
        
        # Bước 8: Đánh giá chất lượng phân tích
        years_count = data_summary['data_info']['years_count']
        if years_count >= 30:
            analysis_grade = "EXCELLENT"
            reliability = "Very High"
        elif years_count >= 20:
            analysis_grade = "GOOD" 
            reliability = "High"
        elif years_count >= 10:
            analysis_grade = "ACCEPTABLE"
            reliability = "Moderate"
        else:
            analysis_grade = "LIMITED"
            reliability = "Low"
        
        # Bước 9: Khuyến nghị
        recommendations = []
        if years_count < 10:
            recommendations.append("Nên thu thập thêm dữ liệu để tăng độ tin cậy")
        
        if best_dist_info.get('p_value') and best_dist_info['p_value'] < 0.05:
            recommendations.append("Cân nhắc sử dụng phân phối khác do p-value thấp")
        
        if not recommendations:
            recommendations.append("Phân tích có chất lượng tốt với dữ liệu hiện tại")
        
        # Tổng hợp kết quả hoàn chỉnh
        complete_result = {
            "status": "success",
            "analysis_metadata": {
                "timestamp": "2024-08-23 22:30:00",  # Could use datetime.now()
                "analysis_type": agg_func.upper(),
                "analysis_grade": analysis_grade,
                "data_reliability": reliability,
                "total_distributions_tested": len(valid_distributions),
                "recommendations": recommendations
            },
            
            # 1. Thông tin dữ liệu
            "data_summary": data_summary,
            
            # 2. Kết quả phân tích phân phối
            "distribution_analysis": {
                "all_distributions": distribution_analysis,
                "best_distribution": {
                    "name": best_dist_name,
                    "display_name": best_dist_name.capitalize(),
                    "aic": best_dist_info['AIC'],
                    "p_value": best_dist_info.get('p_value'),
                    "chi_square": best_dist_info.get('ChiSquare'),
                    "parameters": best_dist_info.get('params', {}),
                    "data_quality_grade": best_dist_info.get('data_quality_grade', 'good'),
                    "uncertainty_level": best_dist_info.get('uncertainty_level', 'moderate')
                },
                "distribution_ranking": [
                    {
                        "rank": i+1,
                        "distribution": name,
                        "aic": info['AIC'],
                        "p_value": info.get('p_value'),
                        "performance": "Excellent" if i == 0 else "Good" if i < 3 else "Fair"
                    }
                    for i, (name, info) in enumerate(sorted(valid_distributions.items(), key=lambda x: x[1]['AIC']))
                ]
            },
            
            # 3. Đường cong tần suất cho tất cả phân phối
            "frequency_curves": frequency_curves,
            
            # 4. QQ/PP plots
            "goodness_of_fit_plots": {
                "distribution": best_dist_name,
                "qq_plot_data": qq_pp_data.get('qq', []),
                "pp_plot_data": qq_pp_data.get('pp', [])
            },
            
            # 5. Bảng tần suất
            "frequency_tables": {
                "basic_frequency_table": frequency_table,
                "model_based_table": frequency_by_model,
                "summary_return_periods": return_periods_analysis
            },
            
            # 6. Kết quả xuất cho người dùng
            "export_ready_data": {
                "summary_table": [
                    ["Phân phối tốt nhất", best_dist_name.capitalize()],
                    ["AIC", f"{best_dist_info['AIC']:.2f}"],
                    ["P-value", f"{best_dist_info.get('p_value', 'N/A')}"],
                    ["Số năm dữ liệu", str(years_count)],
                    ["Cấp độ phân tích", analysis_grade],
                    ["Độ tin cậy", reliability]
                ],
                "return_periods_table": [
                    [rp["return_period_years"], f"{rp['frequency_percent']:.2f}%", 
                     rp["discharge_value"], f"{rp['exceedance_probability']:.4f}"]
                    for rp in return_periods_analysis
                ],
                "charts_available": list(frequency_curves.keys()),
                "total_charts": len(frequency_curves) + 1  # +1 for QQ/PP plot
            }
        }
        
        logging.info("🎉 Complete frequency analysis finished successfully")
        logging.info(f"📊 Generated {len(frequency_curves)} frequency curves")
        logging.info(f"📈 Best distribution: {best_dist_name} (AIC: {best_dist_info['AIC']:.2f})")
        
        return complete_result
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"❌ Error in full frequency analysis: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Lỗi trong phân tích tần suất: {str(e)}")

@router.get("/analysis-summary")
def get_analysis_summary(
    data_service: DataService = Depends(get_data_service)
):
    """
    Lấy tóm tắt nhanh về khả năng phân tích của dữ liệu hiện tại
    """
    if data_service.data is None:
        raise HTTPException(status_code=404, detail="Chưa có dữ liệu được tải")
    
    df = data_service.data
    main_column = data_service.main_column
    
    # Basic info
    years_count = df['Year'].nunique()
    total_records = len(df)
    year_range = f"{df['Year'].min()}-{df['Year'].max()}"
    
    # Determine analysis capability
    if years_count >= 20:
        capability = "Excellent - Suitable for reliable frequency analysis"
        recommended_analysis = ["All distributions", "Long return periods", "Uncertainty analysis"]
    elif years_count >= 10:
        capability = "Good - Suitable for standard frequency analysis"  
        recommended_analysis = ["Main distributions", "Standard return periods"]
    elif years_count >= 5:
        capability = "Limited - Basic frequency analysis only"
        recommended_analysis = ["Simple distributions", "Short return periods"]
    else:
        capability = "Insufficient - Need more data for reliable analysis"
        recommended_analysis = ["Preliminary analysis only"]
    
    return {
        "data_overview": {
            "years_available": years_count,
            "total_records": total_records,
            "year_range": year_range,
            "main_parameter": main_column
        },
        "analysis_capability": capability,
        "recommended_analysis": recommended_analysis,
        "available_functions": [
            "Distribution fitting and comparison",
            "Frequency curve generation", 
            "QQ/PP goodness-of-fit plots",
            "Return period calculation",
            "Statistical parameter estimation"
        ]
    }