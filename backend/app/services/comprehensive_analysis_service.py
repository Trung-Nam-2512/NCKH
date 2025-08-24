"""
Comprehensive Analysis Service - Tổng hợp tất cả kết quả phân tích tần suất
"""
import pandas as pd
import numpy as np
import math
import json
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime
from .data_service import DataService
from .analysis_service import AnalysisService
from .visualization_service import VisualizationService

class ComprehensiveAnalysisService:
    """Service tổng hợp toàn bộ phân tích tần suất như workflow gốc của user"""
    
    def __init__(self, data_service: DataService):
        self.data_service = data_service
        self.analysis_service = AnalysisService(data_service)
        self.visualization_service = VisualizationService(data_service, self.analysis_service)
    
    def clean_numeric_values(self, obj):
        """Recursively clean numeric values to make them JSON serializable"""
        if isinstance(obj, dict):
            return {k: self.clean_numeric_values(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self.clean_numeric_values(item) for item in obj]
        elif isinstance(obj, (float, np.floating)):
            if math.isnan(obj) or math.isinf(obj):
                return None
            return float(obj)
        elif isinstance(obj, (int, np.integer)):
            return int(obj)
        elif isinstance(obj, np.ndarray):
            return self.clean_numeric_values(obj.tolist())
        else:
            return obj
    
    def get_data_summary(self) -> Dict[str, Any]:
        """Tóm tắt dữ liệu đã upload"""
        
        if self.data_service.data is None:
            return {"error": "Không có dữ liệu"}
        
        df = self.data_service.data
        main_column = self.data_service.main_column
        
        # Basic statistics
        annual_data = df.groupby('Year')[main_column].agg(['min', 'max', 'mean', 'std', 'count'])
        
        summary = {
            "data_info": {
                "total_records": len(df),
                "years_count": len(annual_data),
                "year_range": {
                    "start": int(df['Year'].min()),
                    "end": int(df['Year'].max())
                },
                "main_column": main_column,
                "has_monthly_data": "Month" in df.columns
            },
            "annual_statistics": {
                "min_value": float(annual_data['min'].min()),
                "max_value": float(annual_data['max'].max()),
                "mean_value": float(annual_data['mean'].mean()),
                "std_value": float(annual_data['std'].mean())
            },
            "annual_data": annual_data.round(3).to_dict('index')
        }
        
        # Clean numeric values before returning
        summary = self.clean_numeric_values(summary)
        return summary
    
    def perform_comprehensive_frequency_analysis(self, agg_func: str = 'max') -> Dict[str, Any]:
        """Thực hiện phân tích tần suất toàn diện như workflow gốc"""
        
        if self.data_service.data is None:
            return {"error": "Không có dữ liệu để phân tích"}
        
        try:
            # 1. Data Summary
            data_summary = self.get_data_summary()
            
            # 2. Distribution Analysis - So sánh tất cả phân phối
            distribution_analysis = self.analysis_service.get_distribution_analysis(agg_func)
            
            # Sắp xếp theo AIC để tìm phân phối tốt nhất
            valid_distributions = {
                name: result for name, result in distribution_analysis.items()
                if result.get('AIC', float('inf')) != float('inf')
            }
            
            if not valid_distributions:
                return {"error": "Không thể fit được phân phối nào"}
            
            best_distribution = min(valid_distributions.items(), key=lambda x: x[1]['AIC'])
            best_dist_name = best_distribution[0]
            best_dist_info = best_distribution[1]
            
            # 3. Frequency Analysis Table (Bảng tần suất cơ bản)
            frequency_table = self.analysis_service.get_frequency_analysis()
            
            # 4. Frequency by Model (Bảng tần suất theo mô hình tốt nhất)
            frequency_by_model = self.analysis_service.get_frequency_by_model(best_dist_name, agg_func)
            
            # 5. QQ/PP Plot Data
            qq_pp_data = self.analysis_service.compute_qq_pp(best_dist_name, agg_func)
            
            # 6. Frequency Curves cho tất cả phân phối chính
            frequency_curves = {}
            main_distributions = ['gumbel', 'genextreme', 'lognorm', 'gamma', 'logistic']
            
            for dist_name in main_distributions:
                if dist_name in valid_distributions:
                    try:
                        curve_data = self.analysis_service.compute_frequency_curve(dist_name, agg_func)
                        frequency_curves[dist_name] = {
                            "curve_data": curve_data,
                            "aic": valid_distributions[dist_name]['AIC'],
                            "p_value": valid_distributions[dist_name].get('p_value'),
                            "params": valid_distributions[dist_name]['params']
                        }
                    except Exception as e:
                        logging.warning(f"Could not generate curve for {dist_name}: {e}")
            
            # 7. Generate All Visualizations
            visualizations = self.visualization_service.generate_comprehensive_report_plots(agg_func)
            
            # 8. Statistical Summary for Best Distribution
            statistical_summary = {
                "best_distribution": {
                    "name": best_dist_name,
                    "display_name": best_dist_name.capitalize(),
                    "aic": best_dist_info['AIC'],
                    "chi_square": best_dist_info.get('ChiSquare'),
                    "p_value": best_dist_info.get('p_value'),
                    "parameters": best_dist_info.get('params', {}),
                    "data_quality_grade": best_dist_info.get('data_quality_grade', 'unknown'),
                    "uncertainty_level": best_dist_info.get('uncertainty_level', 'unknown')
                },
                "goodness_of_fit_ranking": [
                    {
                        "rank": i+1,
                        "distribution": name,
                        "aic": result['AIC'],
                        "p_value": result.get('p_value'),
                        "status": "Tốt" if result.get('p_value', 0) > 0.05 else "Cần cân nhắc" if result.get('p_value') else "Không xác định"
                    }
                    for i, (name, result) in enumerate(sorted(valid_distributions.items(), key=lambda x: x[1]['AIC']))
                ]
            }
            
            # 9. Return Periods Analysis (Chu kỳ lặp lại quan trọng)
            important_return_periods = [2, 5, 10, 25, 50, 100]
            return_periods_analysis = []
            
            if frequency_by_model.get('theoretical_curve'):
                for period in important_return_periods:
                    freq_percent = 100 / period
                    closest_point = min(frequency_by_model['theoretical_curve'],
                                      key=lambda x: abs(float(x['Tần suất P(%)']) - freq_percent))
                    
                    return_periods_analysis.append({
                        "return_period": period,
                        "frequency_percent": freq_percent,
                        "discharge_value": closest_point['Lưu lượng dòng chảy Q m³/s'],
                        "exceedance_probability": freq_percent / 100
                    })
            
            # 10. Analysis Metadata
            metadata = {
                "analysis_date": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "analysis_type": agg_func.upper(),
                "data_years": data_summary['data_info']['years_count'],
                "total_records": data_summary['data_info']['total_records'],
                "analysis_grade": self._determine_analysis_grade(data_summary['data_info']['years_count']),
                "recommendations": self._generate_recommendations(data_summary['data_info']['years_count'], best_dist_info)
            }
            
            # Comprehensive Result
            comprehensive_result = {
                "status": "success",
                "metadata": metadata,
                "data_summary": data_summary,
                "statistical_analysis": {
                    "distribution_comparison": distribution_analysis,
                    "statistical_summary": statistical_summary,
                    "goodness_of_fit_tests": statistical_summary["goodness_of_fit_ranking"]
                },
                "frequency_analysis": {
                    "basic_frequency_table": frequency_table,
                    "frequency_by_best_model": frequency_by_model,
                    "return_periods_analysis": return_periods_analysis,
                    "frequency_curves": frequency_curves
                },
                "quality_assessment": {
                    "qq_pp_plots_data": qq_pp_data,
                    "data_quality_grade": best_dist_info.get('data_quality_grade', 'unknown'),
                    "uncertainty_level": best_dist_info.get('uncertainty_level', 'unknown'),
                    "sample_size": best_dist_info.get('sample_size', 0)
                },
                "visualizations": visualizations,
                "export_data": self._prepare_export_data(frequency_by_model, return_periods_analysis, statistical_summary)
            }
            
            # Clean numeric values before returning
            comprehensive_result = self.clean_numeric_values(comprehensive_result)
            return comprehensive_result
            
        except Exception as e:
            logging.error(f"Error in comprehensive frequency analysis: {e}")
            return {"error": f"Lỗi trong phân tích toàn diện: {str(e)}"}
    
    def _determine_analysis_grade(self, years_count: int) -> str:
        """Xác định cấp độ phân tích dựa trên số năm dữ liệu"""
        if years_count >= 30:
            return "EXCELLENT"
        elif years_count >= 20:
            return "GOOD"
        elif years_count >= 10:
            return "ACCEPTABLE"
        elif years_count >= 5:
            return "LIMITED"
        else:
            return "PRELIMINARY"
    
    def _generate_recommendations(self, years_count: int, best_dist_info: Dict) -> List[str]:
        """Tạo khuyến nghị dựa trên chất lượng dữ liệu"""
        recommendations = []
        
        if years_count < 10:
            recommendations.append("Nên thu thập thêm dữ liệu để tăng độ tin cậy của phân tích")
        
        if best_dist_info.get('p_value') and best_dist_info['p_value'] < 0.05:
            recommendations.append("Phân phối tốt nhất có p-value < 0.05, cần cân nhắc phân phối khác")
        
        uncertainty = best_dist_info.get('uncertainty_level', '')
        if uncertainty in ['high', 'very high']:
            recommendations.append("Kết quả có độ bất định cao, cần thận trọng khi sử dụng")
        
        if years_count >= 20:
            recommendations.append("Dữ liệu đủ dài để thực hiện phân tích tần suất đáng tin cậy")
        
        if not recommendations:
            recommendations.append("Phân tích tần suất được thực hiện với chất lượng tốt")
        
        return recommendations
    
    def _prepare_export_data(self, frequency_by_model: Dict, return_periods: List, statistical_summary: Dict) -> Dict:
        """Chuẩn bị dữ liệu để export ra Excel/PDF"""
        
        export_data = {
            "summary_table": {
                "title": "Tóm tắt phân tích tần suất",
                "data": [
                    ["Phân phối tốt nhất", statistical_summary["best_distribution"]["display_name"]],
                    ["AIC", f"{statistical_summary['best_distribution']['aic']:.2f}"],
                    ["P-value", f"{statistical_summary['best_distribution'].get('p_value', 'N/A')}"],
                    ["Cấp độ chất lượng", statistical_summary["best_distribution"].get('data_quality_grade', 'N/A')],
                    ["Mức độ bất định", statistical_summary["best_distribution"].get('uncertainty_level', 'N/A')]
                ]
            },
            "return_periods_table": {
                "title": "Bảng chu kỳ lặp lại",
                "headers": ["Chu kỳ (năm)", "Tần suất (%)", "Lưu lượng (m³/s)", "Xác suất vượt quá"],
                "data": [
                    [
                        rp["return_period"],
                        f"{rp['frequency_percent']:.2f}%",
                        rp["discharge_value"],
                        f"{rp['exceedance_probability']:.4f}"
                    ]
                    for rp in return_periods
                ]
            },
            "distribution_comparison_table": {
                "title": "So sánh các phân phối",
                "headers": ["Thứ hạng", "Phân phối", "AIC", "P-value", "Đánh giá"],
                "data": [
                    [
                        item["rank"],
                        item["distribution"].capitalize(),
                        f"{item['aic']:.2f}",
                        f"{item['p_value']:.4f}" if item['p_value'] else "N/A",
                        item["status"]
                    ]
                    for item in statistical_summary["goodness_of_fit_ranking"]
                ]
            }
        }
        
        # Add frequency model data if available
        if frequency_by_model.get('theoretical_curve'):
            export_data["frequency_model_table"] = {
                "title": "Bảng tần suất theo mô hình",
                "headers": ["STT", "Tần suất (%)", "Lưu lượng (m³/s)", "Chu kỳ lặp lại (năm)"],
                "data": [
                    [
                        point.get("Thứ tự", i+1),
                        point.get("Tần suất P(%)", "N/A"),
                        point.get("Lưu lượng dòng chảy Q m³/s", "N/A"),
                        point.get("Thời gian lặp lại (năm)", "N/A")
                    ]
                    for i, point in enumerate(frequency_by_model['theoretical_curve'])
                ]
            }
        
        return export_data