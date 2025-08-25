"""
ROUTER PHÂN TÍCH TẦN SUẤT - API endpoints cho các chức năng phân tích thống kê
Module này cung cấp các API endpoint để:
- Phân tích phân phối xác suất của dữ liệu thủy văn
- Tính toán đường cong tần suất cho các phân phối khác nhau
- Trích xuất dữ liệu quantile và thông số thống kê
- Hỗ trợ nhiều loại phân phối: Gumbel, Log-Normal, Gamma, v.v.
"""

# Import các thư viện cần thiết
from fastapi import APIRouter, Depends, Query, Path, UploadFile, File, HTTPException, Form
from ..dependencies import get_analysis_service, get_data_service  # Dependency injection
from ..services.analysis_service import AnalysisService
from ..services.data_service import DataService
import pandas as pd
import io

# Khởi tạo router với prefix và tag để nhóm các endpoint
router = APIRouter(prefix="/analysis", tags=["analysis"])

@router.get("/distribution")
def get_distribution_analysis(
    agg_func: str = Query('max'),  # Hàm tổng hợp: 'max', 'min', 'mean'
    analysis_service: AnalysisService = Depends(get_analysis_service)
):
    """
    API phân tích phân phối dữ liệu
    
    Chức năng:
    - Tính toán các thông số thống kê mô tả
    - Phân tích xu hướng và tính dừng của dữ liệu
    - Đánh giá sự phù hợp của các phân phối lý thuyết
    
    Args:
        agg_func: Hàm tổng hợp dữ liệu ('max' cho lũ lớn nhất, 'min' cho hạn hán)
        
    Returns:
        Dict chứa kết quả phân tích phân phối
    """
    return analysis_service.get_distribution_analysis(agg_func)

@router.get("/quantile_data/{model}")
def call_get_quantile_data(
    model: str = Path(...),  # Loại phân phối: gumbel, lognorm, gamma, etc.
    agg_func: str = Query('max'), 
    analysis_service: AnalysisService = Depends(get_analysis_service)
):
    """
    API trích xuất dữ liệu quantile theo mô hình phân phối
    
    Chức năng:
    - Tính toán giá trị quantile cho các chu kỳ tái diễn khác nhau
    - Tạo histogram phân bố dữ liệu
    - Tính đường cong lý thuyết tương ứng
    
    Args:
        model: Tên mô hình phân phối (gumbel, lognorm, gamma, logistic, etc.)
        agg_func: Hàm tổng hợp dữ liệu
        
    Returns:
        Dict chứa quantile data, histogram, và đường cong lý thuyết
    """
    return analysis_service.get_quantile_data(model, agg_func)

@router.get("/frequency_curve_gumbel")
def get_frequency_curve_gumbel(
    agg_func: str = Query('max'), 
    analysis_service: AnalysisService = Depends(get_analysis_service)
):
    """
    API tính đường cong tần suất Gumbel
    
    Phân phối Gumbel (Extreme Value Type I):
    - Được sử dụng rộng rãi nhất trong thủy văn
    - Phù hợp với dữ liệu lũ lớn nhất hàng năm
    - Có dạng toán học đơn giản, dễ tính toán
    
    Returns:
        Dict chứa đường cong lý thuyết và điểm empirical
    """
    return analysis_service.compute_frequency_curve("gumbel", agg_func)

@router.get("/frequency_curve_lognorm")
def get_frequency_curve_lognorm(
    agg_func: str = Query('max'), 
    analysis_service: AnalysisService = Depends(get_analysis_service)
):
    """
    API tính đường cong tần suất Log-Normal
    
    Phân phối Log-Normal:
    - Phù hợp khi dữ liệu có phân bố lệch phải
    - Thường dùng cho lưu lượng và lượng mưa
    - Logarithm của dữ liệu có phân phối chuẩn
    
    Returns:
        Dict chứa đường cong lý thuyết và điểm empirical
    """
    return analysis_service.compute_frequency_curve("lognorm", agg_func)

@router.get("/frequency_curve_gamma")
def get_frequency_curve_gamma(
    agg_func: str = Query('max'), 
    analysis_service: AnalysisService = Depends(get_analysis_service)
):
    """
    API tính đường cong tần suất Gamma
    
    Phân phối Gamma:
    - Linh hoạt với nhiều dạng phân bố khác nhau
    - Phù hợp với dữ liệu có giá trị dương
    - Có thể mô tả cả phân bố đối xứng và lệch
    
    Returns:
        Dict chứa đường cong lý thuyết và điểm empirical
    """
    return analysis_service.compute_frequency_curve("gamma", agg_func)

@router.get("/frequency_curve_logistic")
def get_frequency_curve_logistic(
    agg_func: str = Query('max'), 
    analysis_service: AnalysisService = Depends(get_analysis_service)
):
    """
    API tính đường cong tần suất Logistic
    
    Phân phối Logistic:
    - Tương tự phân phối chuẩn nhưng có đuôi dày hơn
    - Phù hợp cho dữ liệu có biến động cao
    - Thường dùng trong mô hình hồi quy logistic
    
    Returns:
        Dict chứa đường cong lý thuyết và điểm empirical
    """
    return analysis_service.compute_frequency_curve("logistic", agg_func)

@router.get("/frequency_curve_exponential")
def get_frequency_curve_exponential(
    agg_func: str = Query('max'), 
    analysis_service: AnalysisService = Depends(get_analysis_service)
):
    """
    API tính đường cong tần suất Exponential
    
    Phân phối Exponential:
    - Mô hình đơn giản với một tham số
    - Phù hợp cho quá trình Poisson
    - Thường dùng cho thời gian giữa các sự kiện
    
    Returns:
        Dict chứa đường cong lý thuyết và điểm empirical
    """
    return analysis_service.compute_frequency_curve("expon", agg_func)

@router.get("/frequency_curve_gpd")
def get_frequency_curve_gpd(
    agg_func: str = Query('max'), 
    analysis_service: AnalysisService = Depends(get_analysis_service)
):
    """
    API tính đường cong tần suất Generalized Pareto Distribution
    
    Phân phối Generalized Pareto (GPD):
    - Lý thuyết Peak Over Threshold (POT)
    - Phù hợp cho phân tích giá trị cực trị
    - Mô hình hóa đuôi của phân phối
    
    Returns:
        Dict chứa đường cong lý thuyết và điểm empirical
    """
    return analysis_service.compute_frequency_curve("genpareto", agg_func)

@router.get("/frequency_curve_frechet")
def get_frequency_curve_frechet(agg_func: str = Query('max'), analysis_service: AnalysisService = Depends(get_analysis_service)):
    return analysis_service.compute_frequency_curve("frechet", agg_func)

@router.get("/frequency_curve_pearson3")
def get_frequency_curve_pearson3(agg_func: str = Query('max'), analysis_service: AnalysisService = Depends(get_analysis_service)):
    return analysis_service.compute_frequency_curve("pearson3", agg_func)

@router.get("/frequency_curve_genextreme")
def get_frequency_curve_genextreme(agg_func: str = Query('max'), analysis_service: AnalysisService = Depends(get_analysis_service)):
    return analysis_service.compute_frequency_curve("genextreme", agg_func)

@router.get("/qq_pp/{model}")
def get_qq_pp_plot_data(model: str = Path(...), agg_func: str = Query('max'), analysis_service: AnalysisService = Depends(get_analysis_service)):
    return analysis_service.compute_qq_pp(model, agg_func)

@router.get("/frequency")
def get_frequency_analysis(analysis_service: AnalysisService = Depends(get_analysis_service)):
    return analysis_service.get_frequency_analysis()

@router.get("/frequency_by_model")
def get_frequency_by_model(distribution_name: str = Query(...), agg_func: str = Query('max'), analysis_service: AnalysisService = Depends(get_analysis_service)):
    return analysis_service.get_frequency_by_model(distribution_name, agg_func)

@router.get("/histogram")
def get_histogram_analysis(distribution_name: str = Query('gumbel'), agg_func: str = Query('max'), analysis_service: AnalysisService = Depends(get_analysis_service)):
    """
    Lấy dữ liệu histogram và đường cong lý thuyết để vẽ biểu đồ tần số
    """
    return analysis_service.get_quantile_data(distribution_name, agg_func)

@router.post("/analyze-file")
async def analyze_uploaded_file(
    file: UploadFile = File(...),
    distribution_name: str = Form("gumbel"),
    agg_func: str = Form("max"),
    data_service: DataService = Depends(get_data_service),
    analysis_service: AnalysisService = Depends(get_analysis_service)
):
    """
    Upload CSV file and perform frequency analysis
    """
    try:
        # Read the uploaded file
        content = await file.read()
        
        # Parse CSV
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.StringIO(content.decode('utf-8')))
        else:
            raise HTTPException(status_code=400, detail="Only CSV files are supported")
        
        # Validate data format
        if df.empty:
            raise HTTPException(status_code=400, detail="File is empty")
        
        # Load data into service
        data_service.data = df
        if 'Q' in df.columns:
            data_service.main_column = 'Q'
        elif 'depth' in df.columns:
            data_service.main_column = 'depth'
        else:
            # Use the last numeric column
            numeric_cols = df.select_dtypes(include=['number']).columns
            if len(numeric_cols) == 0:
                raise HTTPException(status_code=400, detail="No numeric data found in file")
            data_service.main_column = numeric_cols[-1]
        
        # Perform analysis
        result = analysis_service.get_distribution_analysis(agg_func)
        
        return {
            "status": "success",
            "message": "File analyzed successfully",
            "data_info": {
                "rows": len(df),
                "columns": list(df.columns),
                "main_column": data_service.main_column
            },
            "analysis": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")