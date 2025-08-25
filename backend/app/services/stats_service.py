"""
DỊCH VỤ THỐNG KÊ MÔ TẢ (STATS SERVICE) - Tính toán các chỉ số thống kê cơ bản

Chức năng chính:
- Thống kê mô tả cơ bản: mean, median, std, min, max, count
- Thống kê theo tháng cho dữ liệu time series
- Thống kê theo năm với các hàm tổng hợp khác nhau
- Validation và error handling cho dữ liệu không hợp lệ

Hỗ trợ các hàm tổng hợp:
- max: Giá trị lớn nhất (thường dùng cho lũ lớn nhất)
- min: Giá trị nhỏ nhất (thường dùng cho hạn hán)  
- mean: Giá trị trung bình
- sum: Tổng các giá trị (thường dùng cho lượng mưa năm)
"""

import pandas as pd
from fastapi import HTTPException
from .data_service import DataService
from typing import Dict, Any
from ..utils.helpers import validate_agg_func  # Hàm validate hàm tổng hợp hợp lệ

class StatsService:
    """
    DỊCH VỤ THỐNG KÊ MÔ TẢ
    
    Service này cung cấp các phép tính thống kê mô tả cơ bản cho dữ liệu thủy văn.
    Thiết kế stateless - không lưu trữ dữ liệu, chỉ xử lý thông qua DataService.
    
    Dependencies:
        data_service: DataService instance để truy cập dữ liệu đã load
    """
    
    def __init__(self, data_service: DataService):
        """
        Khởi tạo StatsService với dependency injection
        
        Args:
            data_service: Instance của DataService chứa dữ liệu để phân tích
        """
        self.data_service = data_service

    def get_basic_stats(self, agg_func: str = 'max') -> Dict[str, Any]:
        """
        Tính toán các chỉ số thống kê mô tả cơ bản cho dữ liệu hàng năm
        
        Quy trình:
        1. Validate hàm tổng hợp (max, min, mean, sum)
        2. Group dữ liệu theo năm và apply hàm tổng hợp
        3. Tính các chỉ số thống kê từ dữ liệu đã aggregate
        4. Return kết quả dưới dạng dictionary
        
        Args:
            agg_func: Hàm tổng hợp ('max', 'min', 'mean', 'sum')
                     - 'max': Lũ lớn nhất hàng năm
                     - 'min': Lưu lượng nhỏ nhất hàng năm
                     - 'mean': Giá trị trung bình hàng năm
                     - 'sum': Tổng lượng mưa hàng năm
        
        Returns:
            Dict[str, Any]: Dictionary chứa các chỉ số thống kê:
                - count: Số năm có dữ liệu
                - min: Giá trị nhỏ nhất trong chuỗi
                - max: Giá trị lớn nhất trong chuỗi  
                - mean: Giá trị trung bình
                - std: Độ lệch chuẩn
                - median: Trung vị
        
        Raises:
            HTTPException: 
                - 404: Khi chưa có dữ liệu được load
                - 400: Khi hàm tổng hợp không hợp lệ
        """
        # Validate hàm tổng hợp có trong danh sách cho phép
        validate_agg_func(agg_func)
        
        # Lấy dữ liệu từ DataService
        df = self.data_service.data
        main_column = self.data_service.main_column
        
        if df is None:
            raise HTTPException(
                status_code=404, 
                detail="Dữ liệu chưa được tải. Vui lòng upload dữ liệu trước khi thực hiện thống kê."
            )
        
        # Tổng hợp dữ liệu theo năm với hàm được chỉ định
        aggregated = df.groupby('Year')[main_column].agg(agg_func)
        
        # Tính các chỉ số thống kê mô tả
        stats = {
            "count": len(aggregated),                    # Số năm có dữ liệu
            "min": float(aggregated.min()),              # Giá trị nhỏ nhất
            "max": float(aggregated.max()),              # Giá trị lớn nhất
            "mean": float(aggregated.mean()),            # Giá trị trung bình
            "std": float(aggregated.std()),              # Độ lệch chuẩn
            "median": float(aggregated.median())         # Trung vị
        }
        
        return stats

    def get_monthly_stats(self) -> Dict[str, Any]:
        """
        Tính toán thống kê mô tả theo từng tháng trong năm
        
        Chức năng này hữu ích để:
        - Phân tích tính mùa vụ của dữ liệu
        - Xác định tháng có giá trị cao/thấp nhất
        - So sánh biến động giữa các tháng
        - Hỗ trợ phân tích chu kỳ hàng năm
        
        Returns:
            Dict[str, Any]: Dictionary chứa:
                - monthly_stats: List các object với thống kê từng tháng
                - has_month: Flag cho biết dữ liệu có thông tin tháng
        
        Raises:
            HTTPException:
                - 404: Khi chưa có dữ liệu được load
                - 400: Khi dữ liệu không có cột Month (dữ liệu hàng năm)
        """
        # Lấy dữ liệu từ DataService
        df = self.data_service.data
        main_column = self.data_service.main_column
        
        if df is None:
            raise HTTPException(
                status_code=404, 
                detail="Dữ liệu chưa được tải. Vui lòng upload dữ liệu trước khi thực hiện thống kê."
            )
        
        # Kiểm tra xem dữ liệu có thông tin tháng không
        if 'Month' not in df.columns:
            raise HTTPException(
                status_code=400, 
                detail="Dữ liệu không có cột Month. Chỉ áp dụng cho dữ liệu hàng tháng."
            )
        
        # Tính thống kê mô tả cho từng tháng
        monthly_stats = df.groupby('Month')[main_column].agg(['min', 'max', 'mean', 'std']).reset_index()
        return monthly_stats.to_dict(orient="records")

    def get_annual_stats(self, agg_func: str = 'max') -> Dict[str, Any]:
        """Lấy thống kê theo năm"""
        validate_agg_func(agg_func)
        df = self.data_service.data
        main_column = self.data_service.main_column
        if df is None:
            raise HTTPException(status_code=404, detail="Dữ liệu chưa được tải")
        
        if 'Month' in df.columns:
            # Nếu có cột Month, tính thống kê theo năm với các hàm tổng hợp
            annual_stats = df.groupby('Year')[main_column].agg(['min', 'max', 'mean', 'sum']).reset_index()
            annual_stats.columns = ['Year', 'min', 'max', 'mean', 'sum']
        else:
            # Nếu không có cột Month, sử dụng giá trị duy nhất cho mỗi năm
            annual_stats = df.groupby('Year')[main_column].agg(agg_func).reset_index()
            annual_stats.columns = ['Year', 'Value']
            annual_stats['min'] = annual_stats['Value']
            annual_stats['max'] = annual_stats['Value']
            annual_stats['mean'] = annual_stats['Value']
            annual_stats['sum'] = annual_stats['Value']
            annual_stats = annual_stats[['Year', 'min', 'max', 'mean', 'sum']]
        
        return annual_stats.to_dict(orient="records")

    def get_descriptive_stats(self) -> Dict[str, Any]:
        """
        Tính stats descriptive (min/max/mean/sum) group by Month nếu có, hoặc overall.
        - Fix: Nếu no Month, wrap stats dict thành list[{"overall": ...}] để consistent với has_month (luôn list).
        - Lý do: Client dễ parse (expect list records), tránh inconsistency.
        """
        df = self.data_service.data
        main_column = self.data_service.main_column
        if df is None:
            raise HTTPException(status_code=404, detail="Dữ liệu chưa được tải")
        has_month = 'Month' in df.columns
        if has_month:
            grouped_data = df.groupby('Month')[main_column].agg(['min', 'max', 'mean', 'sum']).reset_index()
            stats = grouped_data.to_dict(orient="records")
        else:
            agg = df[main_column].agg(['min', 'max', 'mean', 'sum']).to_dict()
            stats = [{"overall": agg}]
        return {"stats": stats, "has_month": has_month}