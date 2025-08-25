"""
COMPREHENSIVE ANALYSIS ROUTER - Complete workflow phân tích tần suất chuyên nghiệp

Module này cung cấp end-to-end analysis workflow tương tự như các 
chuyên gia thủy văn thực hiện trong nghiên cứu và thiết kế:

COMPREHENSIVE WORKFLOW:
- File upload với validation và auto-detection
- Multi-distribution analysis (Gumbel, Log-Normal, Gamma, etc.)  
- Best-fit selection với statistical criteria
- Professional visualization (frequency curves, QQ/PP plots)
- Return period calculations cho engineering design
- Export functionality với multiple formats
- Research-grade reporting và documentation

PROFESSIONAL FEATURES:
- Automated goodness-of-fit testing
- Uncertainty quantification
- Multiple visualization options
- Export-ready tables và charts
- Statistical validation metrics
- Engineering design recommendations

USE CASES:
- Hydrological engineering design (bridges, dams, drainage)
- Research publications và technical reports
- Professional consulting projects
- Academic research và education
- Regulatory compliance studies
"""
from fastapi import APIRouter, Depends, Query, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from typing import Optional
import logging
import io
import pandas as pd
from ..dependencies import get_data_service
from ..services.data_service import DataService
from ..services.comprehensive_analysis_service import ComprehensiveAnalysisService
from ..services.visualization_service import VisualizationService
from ..services.analysis_service import AnalysisService
from ..services.export_service import ExportService

# Router với prefix "/comprehensive" cho complete analysis workflows
# Tags="comprehensive_analysis" để phân biệt với simple analysis endpoints
router = APIRouter(prefix="/comprehensive", tags=["comprehensive_analysis"])

def get_comprehensive_service(data_service: DataService = Depends(get_data_service)) -> ComprehensiveAnalysisService:
    """Dependency provider cho ComprehensiveAnalysisService"""
    return ComprehensiveAnalysisService(data_service)

def get_visualization_service(data_service: DataService = Depends(get_data_service)) -> VisualizationService:
    """Dependency provider cho VisualizationService với AnalysisService"""
    analysis_service = AnalysisService(data_service)
    return VisualizationService(data_service, analysis_service)

def get_export_service() -> ExportService:
    """Dependency provider cho ExportService"""
    return ExportService()

@router.post("/analyze")
async def perform_comprehensive_analysis(
    file: UploadFile = File(...),
    agg_func: str = Form("max"),
    data_service: DataService = Depends(get_data_service),
    comprehensive_service: ComprehensiveAnalysisService = Depends(get_comprehensive_service)
):
    """
    Thực hiện phân tích tần suất toàn diện như workflow gốc của user
    - Upload file CSV
    - Phân tích tất cả phân phối  
    - Tạo biểu đồ frequency curves, QQ/PP plots
    - Bảng tần suất và chu kỳ lặp lại
    - Xuất kết quả đầy đủ
    """
    try:
        # Read and validate file
        content = await file.read()
        
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="Only CSV files are supported")
        
        df = pd.read_csv(io.StringIO(content.decode('utf-8')))
        
        if df.empty:
            raise HTTPException(status_code=400, detail="File is empty")
        
        # Load data into service
        data_service.data = df
        if 'Q' in df.columns:
            data_service.main_column = 'Q'
        elif 'depth' in df.columns:
            data_service.main_column = 'depth'
        else:
            numeric_cols = df.select_dtypes(include=['number']).columns
            if len(numeric_cols) == 0:
                raise HTTPException(status_code=400, detail="No numeric data found in file")
            data_service.main_column = numeric_cols[-1]
        
        # Perform comprehensive analysis
        result = comprehensive_service.perform_comprehensive_frequency_analysis(agg_func)
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
        
    except Exception as e:
        logging.error(f"Error in comprehensive analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/data-summary")
def get_data_summary(
    comprehensive_service: ComprehensiveAnalysisService = Depends(get_comprehensive_service)
):
    """
    Lấy tóm tắt dữ liệu đã upload
    """
    try:
        summary = comprehensive_service.get_data_summary()
        
        if "error" in summary:
            raise HTTPException(status_code=404, detail=summary["error"])
        
        return summary
        
    except Exception as e:
        logging.error(f"Error getting data summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/visualizations/frequency-curve/{distribution}")
def get_frequency_curve_plot(
    distribution: str,
    agg_func: str = Query("max", description="Hàm tổng hợp"),
    visualization_service: VisualizationService = Depends(get_visualization_service)
):
    """
    Tạo biểu đồ đường cong tần suất cho phân phối cụ thể
    """
    try:
        result = visualization_service.create_frequency_curve_plot(distribution, agg_func)
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
        
    except Exception as e:
        logging.error(f"Error creating frequency curve plot: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/visualizations/qq-pp/{distribution}")
def get_qq_pp_plots(
    distribution: str,
    agg_func: str = Query("max", description="Hàm tổng hợp"),
    visualization_service: VisualizationService = Depends(get_visualization_service)
):
    """
    Tạo QQ và PP plots cho phân phối cụ thể
    """
    try:
        result = visualization_service.create_qq_pp_plots(distribution, agg_func)
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
        
    except Exception as e:
        logging.error(f"Error creating QQ/PP plots: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/visualizations/distribution-comparison")
def get_distribution_comparison_plot(
    agg_func: str = Query("max", description="Hàm tổng hợp"),
    visualization_service: VisualizationService = Depends(get_visualization_service)
):
    """
    Tạo biểu đồ so sánh các phân phối
    """
    try:
        result = visualization_service.create_distribution_comparison_plot(agg_func)
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
        
    except Exception as e:
        logging.error(f"Error creating distribution comparison plot: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/visualizations/histogram-fitted")
def get_histogram_with_fitted_distributions(
    agg_func: str = Query("max", description="Hàm tổng hợp"),
    top_n: int = Query(3, description="Số phân phối tốt nhất để hiển thị"),
    visualization_service: VisualizationService = Depends(get_visualization_service)
):
    """
    Tạo histogram với các phân phối fitted overlay
    """
    try:
        result = visualization_service.create_histogram_with_fitted_distributions(agg_func, top_n)
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
        
    except Exception as e:
        logging.error(f"Error creating histogram plot: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/visualizations/return-period-table/{distribution}")
def get_return_period_table_plot(
    distribution: str,
    agg_func: str = Query("max", description="Hàm tổng hợp"),
    visualization_service: VisualizationService = Depends(get_visualization_service)
):
    """
    Tạo bảng chu kỳ lặp lại dạng biểu đồ
    """
    try:
        result = visualization_service.create_return_period_table_plot(distribution, agg_func)
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
        
    except Exception as e:
        logging.error(f"Error creating return period table: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/visualizations/all-plots")
def get_all_visualization_plots(
    agg_func: str = Query("max", description="Hàm tổng hợp"),
    visualization_service: VisualizationService = Depends(get_visualization_service)
):
    """
    Tạo tất cả biểu đồ cho báo cáo toàn diện
    """
    try:
        result = visualization_service.generate_comprehensive_report_plots(agg_func)
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
        
    except Exception as e:
        logging.error(f"Error generating all plots: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/quick-analysis")
async def quick_comprehensive_analysis(
    agg_func: str = Query("max", description="Hàm tổng hợp"),
    include_visualizations: bool = Query(True, description="Có tạo biểu đồ không"),
    comprehensive_service: ComprehensiveAnalysisService = Depends(get_comprehensive_service)
):
    """
    Phân tích nhanh với các kết quả cốt lõi (không bao gồm toàn bộ detail)
    """
    try:
        # Thực hiện phân tích đầy đủ
        full_result = comprehensive_service.perform_comprehensive_frequency_analysis(agg_func)
        
        if "error" in full_result:
            raise HTTPException(status_code=400, detail=full_result["error"])
        
        # Tạo kết quả rút gọn cho quick analysis
        quick_result = {
            "status": "success",
            "metadata": full_result["metadata"],
            "best_distribution": full_result["statistical_analysis"]["statistical_summary"]["best_distribution"],
            "return_periods": full_result["frequency_analysis"]["return_periods_analysis"],
            "data_quality": {
                "grade": full_result["quality_assessment"]["data_quality_grade"],
                "uncertainty": full_result["quality_assessment"]["uncertainty_level"],
                "sample_size": full_result["quality_assessment"]["sample_size"]
            },
            "recommendations": full_result["metadata"]["recommendations"]
        }
        
        # Thêm visualizations nếu yêu cầu
        if include_visualizations:
            quick_result["key_visualizations"] = {
                "frequency_curve": full_result["visualizations"].get("frequency_curve"),
                "distribution_comparison": full_result["visualizations"].get("distribution_comparison")
            }
        
        return quick_result
        
    except Exception as e:
        logging.error(f"Error in quick comprehensive analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/export/excel")
async def export_to_excel(
    agg_func: str = Query("max", description="Hàm tổng hợp"),
    filename: str = Query("frequency_analysis_report", description="Tên file (không cần extension)"),
    comprehensive_service: ComprehensiveAnalysisService = Depends(get_comprehensive_service),
    export_service: ExportService = Depends(get_export_service)
):
    """
    Export kết quả phân tích ra file Excel
    """
    try:
        # Thực hiện phân tích
        comprehensive_result = comprehensive_service.perform_comprehensive_frequency_analysis(agg_func)
        
        if "error" in comprehensive_result:
            raise HTTPException(status_code=400, detail=comprehensive_result["error"])
        
        # Export to Excel
        excel_data = export_service.export_to_excel(comprehensive_result, filename)
        
        # Return as streaming response
        return StreamingResponse(
            io.BytesIO(excel_data),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}.xlsx"}
        )
        
    except Exception as e:
        logging.error(f"Error exporting to Excel: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/export/pdf")
async def export_to_pdf(
    agg_func: str = Query("max", description="Hàm tổng hợp"),
    filename: str = Query("frequency_analysis_report", description="Tên file (không cần extension)"),
    comprehensive_service: ComprehensiveAnalysisService = Depends(get_comprehensive_service),
    export_service: ExportService = Depends(get_export_service)
):
    """
    Export kết quả phân tích ra file PDF
    """
    try:
        # Thực hiện phân tích
        comprehensive_result = comprehensive_service.perform_comprehensive_frequency_analysis(agg_func)
        
        if "error" in comprehensive_result:
            raise HTTPException(status_code=400, detail=comprehensive_result["error"])
        
        # Export to PDF
        pdf_data = export_service.export_to_pdf(comprehensive_result, filename)
        
        # Return as streaming response
        return StreamingResponse(
            io.BytesIO(pdf_data),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}.pdf"}
        )
        
    except Exception as e:
        logging.error(f"Error exporting to PDF: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/export/charts-png")
async def export_charts_as_png(
    agg_func: str = Query("max", description="Hàm tổng hợp"),
    visualization_service: VisualizationService = Depends(get_visualization_service)
):
    """
    Export tất cả biểu đồ dưới dạng base64 PNG để download
    """
    try:
        plots = visualization_service.generate_comprehensive_report_plots(agg_func)
        
        if "error" in plots:
            raise HTTPException(status_code=400, detail=plots["error"])
        
        # Extract all plot base64 data
        charts = {}
        
        chart_mappings = {
            'frequency_curve': 'Đường cong tần suất',
            'qq_pp_plots': 'QQ-PP Plots',
            'distribution_comparison': 'So sánh phân phối',
            'histogram_fitted': 'Histogram với fitted distributions',
            'return_period_table': 'Bảng chu kỳ lặp lại'
        }
        
        for key, display_name in chart_mappings.items():
            if key in plots and plots[key].get('plot_base64'):
                charts[display_name] = plots[key]['plot_base64']
        
        return {
            "status": "success",
            "charts": charts,
            "metadata": plots.get('metadata', {}),
            "total_charts": len(charts)
        }
        
    except Exception as e:
        logging.error(f"Error exporting charts as PNG: {e}")
        raise HTTPException(status_code=500, detail=str(e))