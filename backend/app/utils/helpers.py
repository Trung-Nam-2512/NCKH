"""
UTILITIES VÀ HELPER FUNCTIONS - Các hàm tiện ích được sử dụng chung trong hệ thống

Module này chứa các utility functions được sử dụng bởi multiple services:
- Xử lý tham số từ scipy.stats distributions
- Validation functions cho input data
- Common transformations và conversions
- Error handling helpers

Nguyên tắc thiết kế:
- DRY (Don't Repeat Yourself): Avoid duplicate code
- Single Responsibility: Mỗi function làm một việc specific
- Pure Functions: No side effects, predictable outputs
- Type Hints: Clear input/output types
"""

from typing import Dict, Tuple, Any
from fastapi import HTTPException

def extract_params(params: Tuple) -> Dict[str, Any]:
    """
    Trích xuất và chuẩn hóa tham số từ scipy.stats distribution fitting results
    
    Scipy.stats.fit() trả về tuple parameters với format khác nhau tùy theo
    loại phân phối:
    - Gumbel: (loc, scale) - 2 parameters
    - Log-Normal: (shape, loc, scale) - 3 parameters  
    - Generalized: (shape1, shape2, ..., loc, scale) - >3 parameters
    
    Function này chuẩn hóa tất cả về format: {shape, loc, scale}
    
    Args:
        params: Tuple parameters từ scipy.stats.distribution.fit()
        
    Returns:
        Dict[str, Any]: Standardized parameter dictionary với keys:
            - shape: Shape parameter(s) - None nếu không có
            - loc: Location parameter (mean cho normal distributions)
            - scale: Scale parameter (standard deviation cho normal)
    
    Examples:
        >>> extract_params((2.5, 1.2))  # Gumbel distribution
        {"shape": None, "loc": 2.5, "scale": 1.2}
        
        >>> extract_params((0.8, 1.0, 2.5))  # Log-Normal distribution  
        {"shape": 0.8, "loc": 1.0, "scale": 2.5}
        
        >>> extract_params((0.1, 0.2, 1.0, 2.5))  # Generalized distribution
        {"shape": (0.1, 0.2), "loc": 1.0, "scale": 2.5}
    """
    if len(params) == 2:
        # Phân phối 2 tham số (Gumbel, Exponential, etc.)
        return {
            "shape": None,      # Không có shape parameter
            "loc": params[0],   # Location parameter
            "scale": params[1]  # Scale parameter
        }
    elif len(params) == 3:
        # Phân phối 3 tham số (Log-Normal, Gamma, Weibull, etc.)
        return {
            "shape": params[0], # Shape parameter (single value)
            "loc": params[1],   # Location parameter  
            "scale": params[2]  # Scale parameter
        }
    else:
        # Phân phối nhiều tham số (Generalized distributions)
        # Quy ước: các shape parameters đầu, loc và scale cuối
        return {
            "shape": params[:-2],  # Tuple các shape parameters
            "loc": params[-2],     # Location parameter (second-to-last)
            "scale": params[-1]    # Scale parameter (last)
        }

def validate_agg_func(agg_func: str):
    """
    Validate hàm tổng hợp (aggregation function) để đảm bảo tính hợp lệ
    
    Chỉ chấp nhận các hàm tổng hợp phổ biến trong phân tích thủy văn:
    - "max": Giá trị lớn nhất (lũ lớn nhất hàng năm, mưa lớn nhất)
    - "min": Giá trị nhỏ nhất (lưu lượng kiệt, hạn hán)  
    - "sum": Tổng giá trị (tổng lượng mưa năm, tổng thể tích)
    - "mean": Giá trị trung bình (lưu lượng trung bình, nhiệt độ trung bình)
    
    Args:
        agg_func: String tên hàm tổng hợp cần validate
        
    Raises:
        HTTPException: 
            - Status 400 (Bad Request) nếu agg_func không hợp lệ
            - Detail message liệt kê các options hợp lệ
    
    Examples:
        >>> validate_agg_func("max")    # OK - không raise exception
        >>> validate_agg_func("median") # Raises HTTPException
        HTTPException(status_code=400, detail="Invalid agg_func: must be one of {'max', 'min', 'sum', 'mean'}")
    """
    # Set các hàm tổng hợp được chấp nhận
    valid_agg_funcs = {"max", "min", "sum", "mean"}
    
    if agg_func not in valid_agg_funcs:
        raise HTTPException(
            status_code=400,  # Bad Request
            detail=f"Hàm tổng hợp không hợp lệ '{agg_func}'. Chỉ chấp nhận: {valid_agg_funcs}"
        )

# ===================== FUTURE UTILITY FUNCTIONS =====================
# Có thể thêm các helper functions khác:

def convert_to_json_serializable(obj: Any) -> Any:
    """
    Convert numpy/pandas objects sang JSON serializable types
    Cần thiết vì numpy.float64, numpy.int64 không serialize được
    """
    import numpy as np
    import pandas as pd
    
    if isinstance(obj, (np.integer, np.floating)):
        return obj.item()  # Convert to native Python type
    elif isinstance(obj, np.ndarray):
        return obj.tolist()  # Convert to Python list
    elif isinstance(obj, pd.Series):
        return obj.tolist()  # Convert pandas Series to list
    elif isinstance(obj, pd.DataFrame):
        return obj.to_dict('records')  # Convert DataFrame to list of dicts
    else:
        return obj  # Return as-is for other types

def format_number_for_display(number: float, decimal_places: int = 2) -> str:
    """
    Format số cho hiển thị với proper decimal places và thousand separators
    """
    if number is None:
        return "N/A"
    return f"{number:,.{decimal_places}f}"

def validate_date_range(start_date: str, end_date: str) -> bool:
    """
    Validate date range input từ frontend
    Đảm bảo start_date <= end_date và format hợp lệ
    """
    from datetime import datetime
    
    try:
        start = datetime.fromisoformat(start_date)
        end = datetime.fromisoformat(end_date)
        return start <= end
    except ValueError:
        return False