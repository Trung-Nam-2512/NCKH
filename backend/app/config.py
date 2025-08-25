"""
File cấu hình ứng dụng - Quản lý tất cả các biến môi trường và cài đặt hệ thống
Chức năng:
- Đọc các biến môi trường từ file .env
- Cung cấp cấu hình trung tâm cho toàn bộ ứng dụng
- Đảm bảo tính bảo mật bằng cách không hard-code thông tin nhạy cảm
"""

from dotenv import load_dotenv  # Thư viện để đọc file .env
import os

# Tải các biến môi trường từ file .env trong thư mục gốc
load_dotenv()

class Config:
    """
    Lớp cấu hình chứa tất cả các thiết lập của ứng dụng
    Tất cả giá trị đều được đọc từ biến môi trường để đảm bảo tính linh hoạt
    """
    
    # Cấu hình cơ sở dữ liệu MongoDB
    MONGO_URI = os.getenv("MONGO_URI")  # Connection string MongoDB từ .env
    
    # Cấu hình CORS - danh sách domains được phép truy cập API
    ALLOW_ORIGINS = ["*"]  # Cho phép tất cả origins (nên giới hạn trong production)
    
    # Cấu hình API các dịch vụ bên ngoài
    STATIONS_API_BASE_URL = os.getenv("STATIONS_API_BASE_URL")  # API trạm quan trắc, VD: "https://api.kttv.gov.vn/v1/stations"
    STATS_API_BASE_URL = os.getenv("STATS_API_BASE_URL")  # API thống kê trạm, VD: "https://api.kttv.gov.vn/v1/stations/stats"
    
    # Cấu hình xác thực API
    API_KEY = os.getenv("API_KEY")  # API key cho xác thực với dịch vụ ngoài, VD: "X-API-Key: your_key"
    
    # Cấu hình ngưỡng cảnh báo
    DEPTH_THRESHOLD = float(os.getenv("DEPTH_THRESHOLD", 2.0))  # Ngưỡng cảnh báo mực nước (m), mặc định 2.0m

# Tạo instance duy nhất của Config để sử dụng trong toàn bộ ứng dụng (Singleton pattern)
config = Config()