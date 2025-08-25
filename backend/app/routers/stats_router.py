"""
STATS ROUTER - API endpoints cho các phép tính thống kê mô tả

Module này cung cấp REST API endpoints để:
- Thống kê cơ bản (mean, median, std, min, max) của dữ liệu hàng năm
- Thống kê theo tháng cho dữ liệu time series
- Thống kê theo năm với các hàm tổng hợp khác nhau
- Hỗ trợ multiple aggregation functions (max, min, mean, sum)

Đây là module cơ bản nhất trong analysis pipeline, cung cấp
descriptive statistics trước khi thực hiện các phân tích nâng cao hơn
như frequency analysis, probability distributions, v.v.

Use cases:
- Khám phá dữ liệu ban đầu (Exploratory Data Analysis)
- Validate data quality và detect outliers
- So sánh xu hướng theo thời gian (seasonal patterns)
- Chuẩn bị data cho các phân tích statistcal phức tạp hơn
"""

from fastapi import APIRouter, Depends, Query
from ..dependencies import get_stats_service
from ..services.stats_service import StatsService

# Tạo router với prefix "/stats" cho tất cả statistics endpoints
# Tags="stats" để group trong FastAPI auto docs
router = APIRouter(prefix="/stats", tags=["stats"])

@router.get("/basic")
def get_basic_stats(agg_func: str = Query('max'), stats_service: StatsService = Depends(get_stats_service)):
    """
    ENDPOINT THỐNG KÊ MÔ TẢ CƠ BẢN
    
    Endpoint này tính toán các chỉ số thống kê mô tả cơ bản cho dữ liệu
    hàng năm sau khi đã được aggregate theo hàm được chỉ định.
    
    Quy trình xử lý:
    1. Group dữ liệu theo Year
    2. Apply hàm tổng hợp (agg_func) lên main_column 
    3. Tính các chỉ số thống kê từ kết quả aggregated
    4. Trả về comprehensive stats cho EDA
    
    Args:
        agg_func: Hàm tổng hợp để áp dụng cho dữ liệu hàng năm
            - 'max': Lũ lớn nhất hàng năm (Annual Maximum Series)
            - 'min': Lưu lượng nhỏ nhất hàng năm (drought analysis)
            - 'mean': Giá trị trung bình hàng năm
            - 'sum': Tổng lượng mưa hàng năm (annual precipitation)
        stats_service: StatsService instance từ dependency injection
        
    Returns:
        Dict: {
            "count": int - Số năm có dữ liệu,
            "min": float - Giá trị nhỏ nhất trong chuỗi,
            "max": float - Giá trị lớn nhất trong chuỗi,
            "mean": float - Giá trị trung bình,
            "std": float - Độ lệch chuẩn,
            "median": float - Trung vị
        }
        
    Raises:
        HTTPException 404: Chưa có dữ liệu được load
        HTTPException 400: agg_func không hợp lệ
        
    Examples:
        GET /stats/basic?agg_func=max
        → Thống kê lũ lớn nhất hàng năm
        
        GET /stats/basic?agg_func=sum  
        → Thống kê tổng lượng mưa hàng năm
    """
    return stats_service.get_basic_stats(agg_func)

@router.get("/monthly")
def get_monthly_stats(stats_service: StatsService = Depends(get_stats_service)):
    """
    ENDPOINT THỐNG KÊ THEO THÁNG
    
    Endpoint này tính toán thống kê mô tả cho từng tháng trong năm,
    hữu ích để phân tích tính mùa vụ (seasonality) của dữ liệu thủy văn.
    
    Ứng dụng:
    - Phân tích chu kỳ mùa mưa (wet/dry season patterns)
    - Xác định tháng có lũ/hạn hán thường xuyên nhất
    - So sánh biến động giữa các tháng trong năm
    - Planning và design cho các công trình thủy lợi
    - Dự báo và early warning systems
    
    Quy trình xử lý:
    1. Kiểm tra dữ liệu có cột Month không (monthly time series)
    2. Group dữ liệu theo Month (1-12)
    3. Tính min, max, mean, std cho mỗi tháng
    4. Return array of monthly statistics
    
    Args:
        stats_service: StatsService instance từ dependency injection
        
    Returns:
        List[Dict]: Array objects, mỗi object chứa thống kê của 1 tháng:
        [
            {
                "Month": 1,
                "min": float,
                "max": float, 
                "mean": float,
                "std": float
            },
            ...
        ]
        
    Raises:
        HTTPException 404: Chưa có dữ liệu được load
        HTTPException 400: Dữ liệu không có cột Month (chỉ yearly data)
        
    Examples:
        GET /stats/monthly
        → Thống kê lượng mưa/lưu lượng theo 12 tháng
        
        Use case: Xác định tháng 7-9 là mùa mưa lũ,
                  tháng 12-2 là mùa khô hạn
    """
    return stats_service.get_monthly_stats()

@router.get("/annual")
def get_annual_stats(agg_func: str = Query('max'), stats_service: StatsService = Depends(get_stats_service)):
    """
    ENDPOINT THỐNG KÊ THEO NĂM
    
    Endpoint này cung cấp thống kê chi tiết theo từng năm trong dataset,
    cho phép phân tích xu hướng dài hạn và biến động giữa các năm.
    
    Ứng dụng:
    - Phân tích xu hướng biến đổi khí hậu (climate change trends)
    - Xác định các năm có sự kiện cực trị (extreme events)
    - So sánh hiệu suất giữa các năm (wet years vs dry years)
    - Validate data quality và detect anomalies
    - Chuẩn bị data cho time series analysis
    
    Logic xử lý:
    - Nếu có cột Month: aggregate theo Year với nhiều functions
    - Nếu không có Month: sử dụng giá trị yearly trực tiếp
    
    Args:
        agg_func: Hàm tổng hợp (chỉ áp dụng khi không có Month data)
            - 'max': Lũ lớn nhất năm
            - 'min': Hạn hán nghiêm trọng nhất  
            - 'mean': Giá trị trung bình năm
            - 'sum': Tổng lượng mưa năm
        stats_service: StatsService instance từ dependency injection
        
    Returns:
        List[Dict]: Array records cho từng năm:
        [
            {
                "Year": 2020,
                "min": float,
                "max": float,
                "mean": float, 
                "sum": float
            },
            ...
        ]
        
    Raises:
        HTTPException 404: Chưa có dữ liệu được load
        HTTPException 400: agg_func không hợp lệ (khi cần sử dụng)
        
    Examples:
        GET /stats/annual?agg_func=max
        → Chi tiết lũ lớn nhất từng năm qua các thập kỷ
        
        Use case: Phát hiện năm 1999, 2020 có lũ lịch sử,
                  năm 2010, 2016 có hạn hán nghiêm trọng
    """
    return stats_service.get_annual_stats(agg_func)
