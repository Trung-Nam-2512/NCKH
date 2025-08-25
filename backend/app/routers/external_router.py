"""
EXTERNAL ROUTER - API endpoints cho các services bên ngoài và monitoring

Module này chứa các endpoints không liên quan trực tiếp đến business logic
chính của hệ thống phân tích thủy văn, bao gồm:
- Health check cho monitoring và load balancer
- Visit tracking cho analytics và usage statistics  
- External integrations và third-party services
- System monitoring và operational endpoints

Đây là module "utility" cung cấp supporting functionalities
để maintain và monitor hệ thống trong production environment.

Design principles:
- Lightweight endpoints với minimal dependencies
- Graceful error handling (không crash main system)
- Async operations cho I/O bound tasks (database writes)
- Comprehensive logging cho monitoring và debugging
"""

from fastapi import APIRouter, Depends
from datetime import datetime, date
from ..services.mongo_service import MongoService
from ..dependencies import get_mongo_service

# Router với prefix "/external" cho các external-facing endpoints
# Tags="external" để phân biệt với core business endpoints
router = APIRouter(prefix="/external", tags=["external"])

@router.get("/health")
def health_check():
    """
    ENDPOINT HEALTH CHECK - Kiểm tra tình trạng sức khỏe hệ thống
    
    Endpoint này được sử dụng bởi:
    - Load balancer để kiểm tra server có alive không
    - Monitoring tools (Prometheus, Nagios, etc.) để alert
    - Container orchestration (Kubernetes, Docker) cho liveness probe  
    - CI/CD pipeline để verify deployment thành công
    - Manual testing và debugging
    
    Đây là simple endpoint không dependency vào:
    - Database connections (MongoDB)
    - External services (APIs)  
    - Heavy computations
    - File I/O operations
    
    Nếu endpoint này return 200 OK, có nghĩa:
    - FastAPI server đang chạy bình thường
    - Python runtime environment healthy
    - Basic HTTP handling functioning
    - Server có thể accept và process requests
    
    Returns:
        Dict: {
            "status": "healthy",
            "message": "Backend is running"
        }
        
    Response Codes:
        200: System is healthy và ready to serve requests
        5xx: System có vấn đề (unlikely do không có dependencies)
        
    Examples:
        GET /external/health
        → {"status": "healthy", "message": "Backend is running"}
        
        Monitoring scripts:
        curl -f http://localhost:8000/external/health || exit 1
    """
    return {"status": "healthy", "message": "Backend is running"}

@router.post("/visit")
async def record_visit(mongo_service: MongoService = Depends(get_mongo_service)):
    """
    ENDPOINT GHI NHẬN LƯỢT TRUY CẬP - Analytics và usage tracking
    
    Endpoint này được gọi bởi frontend mỗi khi user truy cập hệ thống
    để thu thập statistics về usage patterns và monitor activity.
    
    Mục đích tracking:
    - Business intelligence: hiểu user behavior và usage patterns
    - Performance monitoring: detect traffic spikes và optimize
    - Compliance: audit trails cho security và regulatory  
    - Product analytics: measure adoption và user engagement
    - Cost optimization: understand resource usage patterns
    
    Data được lưu:
    - Timestamp (UTC): thời điểm truy cập chính xác
    - Auto-generated ObjectId: unique identifier cho mỗi visit
    - Có thể mở rộng: IP, User-Agent, geolocation, session info
    
    Async design:
    - Non-blocking cho main request flow
    - Database write được thực hiện async
    - Graceful handling nếu MongoDB không available
    
    Args:
        mongo_service: MongoService instance từ dependency injection
        
    Returns:
        Dict: {
            "status": "success|error",
            "message": "Descriptive message"
        }
        
    Response Codes:
        200: Visit đã được ghi nhận thành công hoặc failed gracefully
        5xx: Server error (unlikely do exception handling)
        
    Examples:
        POST /external/visit
        → {"status": "success", "message": "Visit recorded"}
        
        Frontend integration:
        useEffect(() => {
            fetch('/api/external/visit', {method: 'POST'})
        }, [])
    """
    try:
        success = await mongo_service.record_visit()
        if success:
            return {"status": "success", "message": "Visit recorded"}
        else:
            return {"status": "error", "message": "Failed to record visit"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.get("/stats-visit")
async def get_visit_stats(mongo_service: MongoService = Depends(get_mongo_service)):
    """
    ENDPOINT LẤY THỐNG KÊ LƯỢT TRUY CẬP - Dashboard analytics
    
    Endpoint này cung cấp analytics dashboard về usage patterns
    của hệ thống để admin/stakeholder có thể:
    - Monitor system adoption và user engagement
    - Identify peak usage periods cho capacity planning  
    - Generate reports cho management và funding decisions
    - Detect anomalies trong traffic patterns
    - Measure success metrics của system deployment
    
    Statistics được cung cấp:
    - Total visits: tổng số lượt truy cập từ khi hệ thống launch
    - Daily stats (7 days): breakdown theo ngày trong tuần qua
    - Có thể mở rộng: hourly patterns, geographic distribution, etc.
    
    MongoDB aggregation pipeline:
    - Efficient group by date operations
    - Time-based filtering (7 days window)
    - Sorted results cho visualization
    
    Args:
        mongo_service: MongoService instance từ dependency injection
        
    Returns:
        Dict: {
            "total_visits": int - Tổng số visits,
            "daily_stats": {
                "2024-01-15": 45,
                "2024-01-16": 67,
                ...
            }
        }
        
    Error Response:
        {
            "status": "error", 
            "message": "Error description"
        }
        
    Response Codes:
        200: Stats retrieved thành công hoặc graceful error
        5xx: Server error (unlikely do exception handling)
        
    Examples:
        GET /external/stats-visit
        → Dashboard charts showing daily visitor trends
        
        Admin panel integration:
        - Real-time visitor counter
        - Weekly activity heatmaps  
        - Usage trend graphs
    """
    try:
        stats = await mongo_service.get_visit_stats()
        return stats
    except Exception as e:
        return {"status": "error", "message": str(e)}
