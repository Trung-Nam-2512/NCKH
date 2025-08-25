"""
FILE QUẢN LÝ DEPENDENCY INJECTION - Cung cấp các service instances cho FastAPI

Dependency Injection (DI) là pattern quan trọng giúp:
- Tách biệt việc tạo object với việc sử dụng object
- Dễ dàng test bằng cách inject mock objects
- Quản lý lifecycle của các service instances
- Đảm bảo single responsibility principle

Pattern sử dụng:
- Singleton pattern cho các service cần persist state
- Factory pattern cho các service stateless
- Lazy initialization để tối ưu hiệu năng
"""

from fastapi import Depends
# Import các service classes
from .services.data_service import DataService           # CRUD và xử lý dữ liệu cơ bản
from .services.stats_service import StatsService         # Thống kê mô tả
from .services.analysis_service import AnalysisService   # Phân tích tần suất
from .services.mongo_service import MongoService         # Tương tác MongoDB
from .services.integration_service import IntegrationService  # Tích hợp API ngoài

# ===================== SINGLETON INSTANCES =====================
# Các service được khởi tạo một lần duy nhất và tái sử dụng

# Global variable để lưu singleton instance của DataService
_data_service_instance = None
_mongo_service_instance = None

def get_data_service() -> DataService:
    """
    Dependency provider cho DataService - Singleton pattern
    
    DataService là core service xử lý CRUD operations và data management.
    Sử dụng singleton vì:
    - Cần maintain internal state (cached data, connections)
    - Tiết kiệm memory và tối ưu hiệu năng
    - Đảm bảo consistency của dữ liệu across requests
    
    Returns:
        DataService: Instance duy nhất của DataService
    """
    global _data_service_instance
    if _data_service_instance is None:
        # Khởi tạo lần đầu tiên - lazy initialization
        _data_service_instance = DataService()
    return _data_service_instance

def get_stats_service() -> StatsService:
    """
    Dependency provider cho StatsService - Factory pattern
    
    StatsService xử lý các tính toán thống kê mô tả.
    Không sử dụng singleton vì:
    - Stateless service, không cần persist state
    - Depend on DataService cho data access
    - Lightweight, tạo mới mỗi request không ảnh hưởng hiệu năng
    
    Returns:
        StatsService: New instance với DataService dependency injected
    """
    data_service = get_data_service()  # Inject DataService dependency
    return StatsService(data_service)

def get_analysis_service() -> AnalysisService:
    """
    Dependency provider cho AnalysisService - Factory pattern
    
    AnalysisService thực hiện các phân tích thống kê phức tạp.
    Sử dụng factory pattern vì:
    - Cần fresh state cho mỗi analysis session
    - Depend on DataService để truy cập dữ liệu
    - Computational intensive, cần isolated environment
    
    Returns:
        AnalysisService: New instance với dependencies injected
    """
    data_service = get_data_service()  # Inject DataService dependency
    return AnalysisService(data_service)

def get_mongo_service() -> MongoService:
    """
    Dependency provider cho MongoService - Singleton pattern
    
    MongoService quản lý kết nối và operations với MongoDB.
    Sử dụng singleton vì:
    - Connection pooling cần được maintain
    - Expensive to create new connections
    - Cần persist connection state và configuration
    
    Returns:
        MongoService: Instance duy nhất của MongoService
    """
    global _mongo_service_instance
    if _mongo_service_instance is None:
        # Khởi tạo lần đầu với database connection setup
        _mongo_service_instance = MongoService()
    return _mongo_service_instance

def get_integration_service(data_service: DataService = Depends(get_data_service)) -> IntegrationService:
    """
    Dependency provider cho IntegrationService - Factory pattern với dependency injection
    
    IntegrationService xử lý tích hợp với API bên ngoài.
    Pattern đặc biệt:
    - Sử dụng FastAPI Depends() để inject DataService
    - Factory pattern cho flexibility trong testing
    - Cần DataService để lưu trữ dữ liệu fetch từ external APIs
    
    Args:
        data_service: DataService instance được inject tự động bởi FastAPI
        
    Returns:
        IntegrationService: New instance với DataService dependency
    """
    return IntegrationService(data_service)

# ===================== FUTURE EXTENSIONS =====================
# Có thể thêm các dependency providers khác:
# - get_notification_service() cho email/SMS notifications
# - get_cache_service() cho Redis caching
# - get_auth_service() cho authentication/authorization
# - get_export_service() cho PDF/Excel exports

