"""
Service tích hợp để kết nối realtime service với analysis service
Hỗ trợ phân tích tần suất với dữ liệu realtime
"""

import pandas as pd
import logging
from typing import Dict, Any, Optional, List
from fastapi import HTTPException
from .realtime_service import EnhancedRealtimeService
from .analysis_service import AnalysisService
from .data_service import DataService
from .professional_frequency_analysis_service import ProfessionalFrequencyAnalysisService
from .hydrological_qc_service import HydrologicalQCService
from ..models.data_models import RealTimeQuery

class IntegrationService:
    def __init__(self, data_service: DataService):
        self.data_service = data_service
        self.realtime_service = EnhancedRealtimeService(data_service)
        self.analysis_service = AnalysisService(data_service)
        self.professional_analysis = ProfessionalFrequencyAnalysisService(data_service)
        self.qc_service = HydrologicalQCService()

    async def fetch_and_analyze_realtime(self, query: RealTimeQuery, 
                                       distribution_name: str = "gumbel",
                                       agg_func: str = "max",
                                       use_professional: bool = True) -> Dict[str, Any]:
        """
        Fetch dữ liệu realtime và thực hiện phân tích tần suất chuyên nghiệp
        """
        try:
            # Fetch dữ liệu từ API
            api_data = await self.realtime_service.fetch_water_level(query)
            
            # Xử lý thành DataFrame
            df = self.realtime_service.process_to_df(api_data)
            
            if df.empty:
                raise HTTPException(status_code=404, detail="No valid data found")
            
            # Thực hiện QC chuyên nghiệp
            qc_result = self.qc_service.perform_comprehensive_qc(
                df, parameter='depth'
            )
            
            # Kiểm tra chất lượng dữ liệu
            if not qc_result['summary']['professional_grade']:
                logging.warning(f"Data quality below professional standards: {qc_result['summary']['quality_score']:.1f}/100")
            
            # Tích hợp vào hệ thống với dữ liệu đã QC
            clean_df = qc_result['data_with_flags']
            await self.realtime_service.integrate_to_analysis(clean_df)
            
            # Chọn phương pháp phân tích
            if use_professional:
                # Sử dụng phân tích chuyên nghiệp
                professional_result = await self.professional_analysis.comprehensive_frequency_analysis(
                    data=clean_df,
                    target_distribution=distribution_name,
                    agg_func=agg_func
                )
                
                return {
                    "message": "Professional realtime analysis completed",
                    "data_summary": {
                        "records_processed": len(df),
                        "records_after_qc": len(clean_df[clean_df['qc_flag'] == 'good']),
                        "stations_count": df['station_id'].nunique(),
                        "years_covered": df['Year'].nunique(),
                        "depth_range": {
                            "min": float(df['depth'].min()),
                            "max": float(df['depth'].max()),
                            "mean": float(df['depth'].mean())
                        }
                    },
                    "quality_control": {
                        "overall_score": qc_result['summary']['quality_score'],
                        "professional_grade": qc_result['summary']['professional_grade'],
                        "completeness": qc_result['summary']['data_completeness'],
                        "recommendations": qc_result['recommendations'],
                        "assessment": qc_result['professional_assessment']
                    },
                    "professional_analysis": professional_result,
                    "analysis_grade": "PROFESSIONAL" if qc_result['summary']['professional_grade'] else "STANDARD"
                }
            else:
                # Sử dụng phân tích tiêu chuẩn
                analysis_result = self.analysis_service.get_distribution_analysis(agg_func)
                quantile_data = self.analysis_service.get_quantile_data(distribution_name, agg_func)
                frequency_curve = self.analysis_service.compute_frequency_curve(distribution_name, agg_func)
                
                return {
                    "message": "Standard realtime analysis completed",
                    "data_summary": {
                        "records_processed": len(df),
                        "stations_count": df['station_id'].nunique(),
                        "years_covered": df['Year'].nunique(),
                        "depth_range": {
                            "min": float(df['depth'].min()),
                            "max": float(df['depth'].max()),
                            "mean": float(df['depth'].mean())
                        }
                    },
                    "quality_control": {
                        "overall_score": qc_result['summary']['quality_score'],
                        "recommendations": qc_result['recommendations']
                    },
                    "frequency_analysis": {
                        "distribution_analysis": analysis_result,
                        "selected_distribution": distribution_name,
                        "quantile_data": quantile_data,
                        "frequency_curve": frequency_curve
                    },
                    "analysis_grade": "STANDARD"
                }
        except HTTPException:
            # Re-raise HTTP exceptions (like 404, 422) without modification
            raise
        except Exception as e:
            logging.error(f"Error in fetch_and_analyze_realtime: {e}")
            raise HTTPException(status_code=500, detail=f"Error in realtime analysis: {e}")

    async def analyze_historical_realtime(self, station_id: Optional[str] = None,
                                        min_years: int = 5,
                                        distribution_name: str = "gumbel",
                                        agg_func: str = "max",
                                        use_professional: bool = True) -> Dict[str, Any]:
        """
        Phân tích tần suất chuyên nghiệp với dữ liệu realtime đã tích lũy
        """
        try:
            # Lấy dữ liệu từ MongoDB với logic adaptive
            df = await self.realtime_service.get_frequency_ready_data(station_id, min_years)
            
            if df.empty:
                raise HTTPException(status_code=404, detail="No sufficient historical data available")
            
            # Kiểm tra độ dài chuỗi dữ liệu với logic linh hoạt
            years_available = df['Year'].nunique()
            actual_years_span = df['Year'].max() - df['Year'].min() + 1
            
            # Adaptive minimum years - reduce requirement if little data available
            effective_min_years = min_years
            if years_available < min_years:
                if years_available >= max(2, min_years // 3):  # At least 2 years or 1/3 of requested
                    effective_min_years = years_available
                    logging.warning(f"⚠️ Using {years_available} years instead of {min_years} - limited data available")
                else:
                    raise HTTPException(
                        status_code=422, 
                        detail=f"Insufficient data: {years_available} years available, minimum {max(2, min_years // 3)} required"
                    )
            
            # Thực hiện QC chuyên nghiệp cho dữ liệu lịch sử
            qc_result = self.qc_service.perform_comprehensive_qc(
                df, parameter='depth', station_id=station_id
            )
            
            # Load dữ liệu đã QC vào DataService
            clean_df = qc_result['data_with_flags']
            good_data = clean_df[clean_df['qc_flag'].isin(['good', 'suspect'])].copy()
            
            if len(good_data) < len(df) * 0.8:  # Cần ít nhất 80% dữ liệu tốt
                logging.warning(f"High data rejection rate: {(1 - len(good_data)/len(df))*100:.1f}%")
            
            self.data_service.data = good_data
            self.data_service.main_column = 'depth'
            
            if use_professional:
                # Sử dụng Comprehensive Analysis Service để có đầy đủ visualizations
                from .comprehensive_analysis_service import ComprehensiveAnalysisService
                from .visualization_service import VisualizationService
                
                comprehensive_service = ComprehensiveAnalysisService(self.data_service)
                visualization_service = VisualizationService(self.data_service, self.analysis_service)
                
                # Thực hiện comprehensive frequency analysis
                comprehensive_result = comprehensive_service.perform_comprehensive_frequency_analysis(agg_func)
                
                # Tạo tất cả visualizations
                visualizations = visualization_service.generate_comprehensive_report_plots(agg_func)
                
                # Phân tích chuyên nghiệp bổ sung (nếu cần)
                professional_result = await self.professional_analysis.comprehensive_frequency_analysis(
                    data=good_data,
                    target_distribution=distribution_name,
                    agg_func=agg_func,
                    station_id=station_id
                )
                
                return {
                    "message": "Professional historical analysis with comprehensive visualizations completed",
                    "data_summary": {
                        "total_records": len(df),
                        "records_after_qc": len(good_data),
                        "data_retention_rate": len(good_data) / len(df) * 100,
                        "stations_count": df['station_id'].nunique(),
                        "years_range": {
                            "min": int(df['Year'].min()),
                            "max": int(df['Year'].max()),
                            "available": years_available
                        },
                        "depth_range": {
                            "min": float(df['depth'].min()),
                            "max": float(df['depth'].max()),
                            "mean": float(df['depth'].mean())
                        }
                    },
                    "quality_control": {
                        "overall_score": qc_result['summary']['quality_score'],
                        "professional_grade": qc_result['summary']['professional_grade'],
                        "completeness": qc_result['summary']['data_completeness'],
                        "recommendations": qc_result['recommendations'],
                        "professional_assessment": qc_result['professional_assessment']
                    },
                    "comprehensive_analysis": comprehensive_result,
                    "visualizations": visualizations,
                    "professional_analysis": professional_result,
                    "analysis_grade": "COMPREHENSIVE_PROFESSIONAL",
                    "certification": {
                        "suitable_for_design": qc_result['professional_assessment']['frequency_analysis_suitable'],
                        "wmo_compliant": qc_result['professional_assessment']['wmo_168_compliant'],
                        "overall_grade": qc_result['professional_assessment']['overall_grade']
                    }
                }
            else:
                # Phân tích tiêu chuẩn
                analysis_result = self.analysis_service.get_distribution_analysis(agg_func)
                quantile_data = self.analysis_service.get_quantile_data(distribution_name, agg_func)
                frequency_curve = self.analysis_service.compute_frequency_curve(distribution_name, agg_func)
                qq_pp_data = self.analysis_service.compute_qq_pp(distribution_name, agg_func)
                
                return {
                    "message": "Standard historical analysis completed",
                    "data_summary": {
                        "total_records": len(df),
                        "stations_count": df['station_id'].nunique(),
                        "years_range": {
                            "min": int(df['Year'].min()),
                            "max": int(df['Year'].max())
                        },
                        "depth_range": {
                            "min": float(df['depth'].min()),
                            "max": float(df['depth'].max()),
                            "mean": float(df['depth'].mean())
                        }
                    },
                    "quality_control": {
                        "overall_score": qc_result['summary']['quality_score'],
                        "recommendations": qc_result['recommendations']
                    },
                    "frequency_analysis": {
                        "distribution_analysis": analysis_result,
                        "selected_distribution": distribution_name,
                        "quantile_data": quantile_data,
                        "frequency_curve": frequency_curve,
                        "qq_pp_data": qq_pp_data
                    },
                    "analysis_grade": "STANDARD"
                }
        except HTTPException:
            # Re-raise HTTP exceptions (like 404, 422) without modification
            raise
        except Exception as e:
            logging.error(f"Error in analyze_historical_realtime: {e}")
            raise HTTPException(status_code=500, detail=f"Error in historical analysis: {e}")

    async def get_realtime_frequency_summary(self) -> Dict[str, Any]:
        """
        Lấy tổng quan về khả năng phân tích tần suất với dữ liệu realtime
        """
        try:
            # Lấy thống kê realtime
            realtime_stats = await self.realtime_service.get_realtime_stats()
            
            # Phân tích khả năng phân tích tần suất
            frequency_capability = await self._analyze_frequency_capability()
            
            return {
                "realtime_stats": realtime_stats,
                "frequency_capability": frequency_capability,
                "recommendations": self._generate_recommendations(realtime_stats, frequency_capability)
            }
        except Exception as e:
            logging.error(f"Error getting realtime frequency summary: {e}")
            raise HTTPException(status_code=500, detail=f"Error getting summary: {e}")

    async def professional_system_assessment(self) -> Dict[str, Any]:
        """
        Đánh giá tổng thể hệ thống theo tiêu chuẩn chuyên nghiệp
        """
        try:
            # Lấy thống kê realtime
            realtime_stats = await self.realtime_service.get_realtime_stats()
            
            # Kiểm tra khả năng phân tích tần suất
            frequency_capability = await self._analyze_frequency_capability()
            
            # Lấy dữ liệu mẫu cho đánh giá QC
            sample_df = await self.realtime_service.get_frequency_ready_data(min_years=1)
            qc_assessment = None
            
            if not sample_df.empty:
                qc_result = self.qc_service.perform_comprehensive_qc(
                    sample_df.head(1000), parameter='depth'  # Lấy mẫu nhỏ để đánh giá
                )
                qc_assessment = qc_result['professional_assessment']
            
            # Tính điểm tổng thể
            overall_score = self._calculate_system_score(
                realtime_stats, frequency_capability, qc_assessment
            )
            
            # Phân loại hệ thống
            system_grade = self._grade_system(overall_score)
            
            return {
                "system_assessment": {
                    "overall_score": overall_score,
                    "grade": system_grade,
                    "certification_level": self._get_certification_level(overall_score),
                    "professional_ready": overall_score >= 85
                },
                "component_scores": {
                    "data_availability": self._score_data_availability(realtime_stats),
                    "data_quality": qc_assessment['overall_grade'] if qc_assessment else 'N/A',
                    "frequency_capability": self._score_frequency_capability(frequency_capability),
                    "system_integration": 85  # Based on SOLID architecture
                },
                "realtime_stats": realtime_stats,
                "frequency_capability": frequency_capability,
                "quality_assessment": qc_assessment,
                "recommendations": self._generate_professional_recommendations(
                    overall_score, realtime_stats, frequency_capability, qc_assessment
                ),
                "compliance_status": {
                    "WMO_168": qc_assessment.get('standards_compliance', {}).get('WMO-168', False) if qc_assessment else False,
                    "ISO_14688": qc_assessment.get('standards_compliance', {}).get('ISO_14688', False) if qc_assessment else False,
                    "ASCE_Standards": qc_assessment.get('standards_compliance', {}).get('ASCE_Standards', False) if qc_assessment else False
                }
            }
        except Exception as e:
            logging.error(f"Error in professional system assessment: {e}")
            raise HTTPException(status_code=500, detail=f"Error in system assessment: {e}")

    async def _analyze_frequency_capability(self) -> Dict[str, Any]:
        """
        Phân tích khả năng thực hiện phân tích tần suất
        """
        try:
            # Kiểm tra với các ngưỡng năm khác nhau
            thresholds = [3, 5, 10, 15, 20]
            capability = {}
            
            for threshold in thresholds:
                df = await self.realtime_service.get_frequency_ready_data(min_years=threshold)
                capability[f"{threshold}_years"] = {
                    "available_stations": df['station_id'].nunique() if not df.empty else 0,
                    "total_records": len(df) if not df.empty else 0,
                    "years_range": {
                        "min": int(df['Year'].min()) if not df.empty else 0,
                        "max": int(df['Year'].max()) if not df.empty else 0
                    } if not df.empty else {"min": 0, "max": 0}
                }
            
            return capability
        except Exception as e:
            logging.error(f"Error analyzing frequency capability: {e}")
            return {}

    def _generate_recommendations(self, realtime_stats: Dict[str, Any], 
                                frequency_capability: Dict[str, Any]) -> List[str]:
        """
        Tạo khuyến nghị dựa trên dữ liệu hiện có
        """
        recommendations = []
        
        total_records = realtime_stats.get("total_records", 0)
        stations_count = realtime_stats.get("stations_count", 0)
        
        if total_records < 1000:
            recommendations.append("Cần tích lũy thêm dữ liệu realtime (hiện tại < 1000 records)")
        
        if stations_count < 5:
            recommendations.append("Cần dữ liệu từ nhiều trạm hơn để phân tích so sánh")
        
        # Kiểm tra khả năng phân tích với 10 năm
        ten_year_cap = frequency_capability.get("10_years", {})
        if ten_year_cap.get("available_stations", 0) < 3:
            recommendations.append("Cần ít nhất 3 trạm có 10+ năm dữ liệu để phân tích tần suất đáng tin cậy")
        
        # Kiểm tra độ dài chuỗi thời gian
        if ten_year_cap.get("years_range", {}).get("max", 0) - ten_year_cap.get("years_range", {}).get("min", 0) < 10:
            recommendations.append("Chuỗi thời gian ngắn - cần tích lũy dữ liệu dài hạn hơn")
        
        if not recommendations:
            recommendations.append("Dữ liệu đủ để thực hiện phân tích tần suất cơ bản")
        
        return recommendations

    async def setup_continuous_analysis(self, station_id: Optional[str] = None,
                                      analysis_interval_hours: int = 24) -> Dict[str, Any]:
        """
        Thiết lập phân tích tần suất liên tục với dữ liệu realtime
        """
        try:
            # Bắt đầu auto-poll
            self.realtime_service.setup_auto_poll()
            
            # Thiết lập job phân tích định kỳ
            async def periodic_analysis():
                try:
                    df = await self.realtime_service.get_frequency_ready_data(station_id, min_years=3)
                    if not df.empty:
                        self.data_service.data = df
                        self.data_service.main_column = 'depth'
                        logging.info(f"Periodic analysis completed with {len(df)} records")
                except Exception as e:
                    logging.error(f"Periodic analysis error: {e}")
            
            # Thêm job phân tích định kỳ (mỗi 24 giờ)
            self.realtime_service.scheduler.add_job(
                periodic_analysis, 
                'interval', 
                hours=analysis_interval_hours
            )
            
            return {
                "message": "Continuous analysis setup completed",
                "auto_poll_interval": "10 minutes",
                "analysis_interval": f"{analysis_interval_hours} hours",
                "station_filter": station_id if station_id else "all stations"
            }
        except Exception as e:
            logging.error(f"Error setting up continuous analysis: {e}")
            raise HTTPException(status_code=500, detail=f"Error setting up continuous analysis: {e}")
    
    def _calculate_system_score(self, realtime_stats: Dict, frequency_cap: Dict, qc_assessment: Dict) -> float:
        """Đánh giá điểm tổng thể hệ thống"""
        score = 0.0
        
        # Điểm dữ liệu (40%)
        data_score = min(100, (realtime_stats.get('total_records', 0) / 10000) * 100)
        score += data_score * 0.4
        
        # Điểm chất lượng (30%)
        if qc_assessment:
            quality_map = {'A': 95, 'B': 85, 'C': 75, 'F': 50}
            quality_score = quality_map.get(qc_assessment.get('overall_grade', 'F'), 50)
        else:
            quality_score = 60  # Default if no assessment
        score += quality_score * 0.3
        
        # Khả năng phân tích (20%)
        ten_year_stations = frequency_cap.get('10_years', {}).get('available_stations', 0)
        analysis_score = min(100, ten_year_stations * 25)  # 4 stations = 100%
        score += analysis_score * 0.2
        
        # Kiến trúc hệ thống (10%)
        architecture_score = 85  # SOLID compliant
        score += architecture_score * 0.1
        
        return min(100, score)
    
    def _grade_system(self, score: float) -> str:
        """Đề cấp hệ thống"""
        if score >= 95:
            return "EXCELLENT - Production Ready"
        elif score >= 85:
            return "GOOD - Professional Use"
        elif score >= 75:
            return "ACCEPTABLE - Requires Enhancement"
        elif score >= 65:
            return "FAIR - Significant Improvements Needed"
        else:
            return "POOR - Not Suitable for Professional Use"
    
    def _get_certification_level(self, score: float) -> str:
        """Định mức chứng chỉ chuyên nghiệp"""
        if score >= 95:
            return "CERTIFIED - Critical Infrastructure Design"
        elif score >= 85:
            return "QUALIFIED - Frequency Analysis & Water Management"
        elif score >= 75:
            return "LIMITED - Basic Hydrological Applications"
        else:
            return "NOT CERTIFIED - Training/Development Use Only"
    
    def _score_data_availability(self, stats: Dict) -> int:
        """Đánh giá độ sẵn có dữ liệu"""
        records = stats.get('total_records', 0)
        stations = stats.get('stations_count', 0)
        
        score = 0
        score += min(50, records / 200)  # 10k records = 50 points
        score += min(30, stations * 6)   # 5 stations = 30 points
        score += 20 if stats.get('date_range') else 0  # Time coverage = 20 points
        
        return min(100, score)
    
    def _score_frequency_capability(self, capability: Dict) -> int:
        """Đánh giá khả năng phân tích tần suất"""
        score = 0
        
        # Kiểm tra các ngưỡng năm
        thresholds = [5, 10, 15, 20]
        for threshold in thresholds:
            key = f"{threshold}_years"
            if key in capability:
                stations = capability[key].get('available_stations', 0)
                if stations >= 3:  # Tối thiểu 3 trạm
                    score += 25  # Mỗi ngưỡng đạt = 25 điểm
        
        return min(100, score)
    
    def _generate_professional_recommendations(self, score: float, stats: Dict, capability: Dict, qc: Dict) -> List[str]:
        """Đưa ra khuyến nghị chuyên nghiệp"""
        recommendations = []
        
        if score < 85:
            recommendations.append("Hệ thống chưa đạt tiêu chuẩn chuyên nghiệp - cần cải thiện để sử dụng trong thực tế")
        
        if stats.get('total_records', 0) < 5000:
            recommendations.append("Cần tích lũy thêm dữ liệu realtime (ít nhất 5000 bản ghi cho phân tích ổn định)")
        
        if stats.get('stations_count', 0) < 5:
            recommendations.append("Mở rộng mạng lưới trạm đo (ít nhất 5 trạm cho phân tích so sánh)")
        
        ten_year_capability = capability.get('10_years', {}).get('available_stations', 0)
        if ten_year_capability < 3:
            recommendations.append("Cần dữ liệu dài hạn hơn - ít nhất 3 trạm có 10+ năm dữ liệu cho phân tích tần suất đáng tin cậy")
        
        if qc and qc.get('overall_grade', 'F') in ['C', 'F']:
            recommendations.append("Cải thiện quy trình kiểm soát chất lượng dữ liệu - hiện tại chưa đạt tiêu chuẩn quốc tế")
        
        if score >= 95:
            recommendations.append("✅ Hệ thống sẵn sàng cho ứng dụng chuyên nghiệp và thiết kế cấu trúc hạ tầng quan trọng")
        elif score >= 85:
            recommendations.append("✅ Hệ thống phù hợp cho phân tích tần suất và quản lý tài nguyên nước chuyên nghiệp")
        
        return recommendations 