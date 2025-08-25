"""
File định nghĩa các data models - Cấu trúc dữ liệu chuẩn cho API requests/responses
Sử dụng Pydantic BaseModel để:
- Tự động validate dữ liệu đầu vào
- Serialize/deserialize JSON
- Generate API documentation tự động
- Type checking và IDE support
"""

from pydantic import BaseModel
from typing import List, Dict, Any, Optional, Union

# ===================== MODELS CHO PHÂN TÍCH DỮ LIỆU =====================

class UploadManualPayload(BaseModel):
    """
    Model cho dữ liệu upload manual từ frontend
    Dùng khi người dùng nhập dữ liệu trực tiếp hoặc upload file CSV/Excel
    """
    data: List[Dict[str, Any]]  # Danh sách các bản ghi dữ liệu, mỗi bản ghi là dict

class StatsResponse(BaseModel):
    """
    Model cho response của các API thống kê mô tả
    Trả về kết quả thống kê như mean, median, std, min, max, v.v.
    """
    stats: Union[List[Dict[str, Any]], Dict[str, Any]]  # Có thể là list hoặc dict tùy loại thống kê
    has_month: Optional[bool] = None  # Flag cho biết dữ liệu có thông tin tháng không

class FrequencyCurveResponse(BaseModel):
    """
    Model cho response của API phân tích tần suất
    Chứa đường cong tần suất lý thuyết và các điểm empirical
    """
    theoretical_curve: List[Dict[str, Any]]  # Đường cong lý thuyết (Gumbel, Log-Normal, etc.)
    empirical_points: List[Dict[str, Any]]   # Các điểm thực nghiệm từ dữ liệu quan sát

class QQPPResponse(BaseModel):
    """
    Model cho response của QQ-plot và PP-plot
    Dùng để kiểm tra độ phù hợp của phân phối lý thuyết với dữ liệu thực
    """
    qq: List[Dict[str, Any]]  # Quantile-Quantile plot data
    pp: List[Dict[str, Any]]  # Probability-Probability plot data

class QuantileDataResponse(BaseModel):
    """
    Model cho response dữ liệu quantile và histogram
    Chứa thông tin về phân bố dữ liệu và giá trị cực trị theo năm
    """
    years: List[int]  # Danh sách các năm có dữ liệu
    qmax_values: List[float]  # Giá trị lũ lớn nhất (Qmax) theo từng năm
    histogram: Dict[str, List[Any]]  # Dữ liệu histogram để vẽ biểu đồ phân bố
    theoretical_curve: Dict[str, List[float]]  # Đường cong lý thuyết tương ứng

# ===================== MODELS CHO DỮ LIỆU THỜI GIAN THỰC =====================

class Station(BaseModel):
    """
    Model cho thông tin trạm quan trắc khí tượng thủy văn
    Chứa metadata đầy đủ về vị trí và thông số kỹ thuật của trạm
    """
    uuid: str  # ID duy nhất của trạm trong hệ thống
    code: str  # Mã trạm theo quy định (ví dụ: HN001)
    name: str  # Tên đầy đủ của trạm quan trắc
    number: str  # Số hiệu trạm
    latitude: float  # Vĩ độ (độ thập phân)
    longitude: float  # Kinh độ (độ thập phân)
    area: str  # Khu vực địa lý (tỉnh/thành)
    city: str  # Thành phố/huyện
    address: str  # Địa chỉ cụ thể của trạm
    altitude: Optional[float] = None  # Độ cao so với mực nước biển (m) - có thể null
    waterStationType: Optional[str] = None  # Loại trạm thủy văn (mực nước, lưu lượng, v.v.)

class RealTimeMeasurement(BaseModel):
    """
    Model cho một lần đo dữ liệu thời gian thực
    Mỗi measurement chứa giá trị đo và thời điểm đo
    """
    depth: float  # Mực nước (m) hoặc giá trị đo khác
    time_point: str  # Thời điểm đo (ISO format: YYYY-MM-DD HH:mm:ss)

class RealTimeStationData(BaseModel):
    """
    Model cho dữ liệu thời gian thực của một trạm
    Chứa danh sách các lần đo và ID trạm tương ứng
    """
    value: List[RealTimeMeasurement]  # Danh sách các lần đo
    station_id: str  # ID của trạm thực hiện các lần đo này

class RealTimeResponse(BaseModel):
    """
    Model cho response của API dữ liệu thời gian thực
    Cấu trúc response từ API bên ngoài (KTTV, DHKTTV)
    """
    id: str  # ID của request/response
    Data: List[RealTimeStationData]  # Dữ liệu từ các trạm (có thể nhiều trạm cùng lúc)

class RealTimeQuery(BaseModel):
    """
    Model cho request query dữ liệu thời gian thực
    Định nghĩa các tham số cần thiết để lấy dữ liệu từ API ngoài
    """
    start_time: str  # Thời gian bắt đầu (ISO format)
    end_time: str    # Thời gian kết thúc (ISO format)
    station_id: Optional[str] = None  # ID trạm cụ thể (nếu null thì lấy tất cả trạm)