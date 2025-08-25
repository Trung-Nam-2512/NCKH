"""
File chính của ứng dụng FastAPI - Khởi tạo và cấu hình toàn bộ hệ thống backend
Chức năng: 
- Khởi tạo FastAPI app với các middleware cần thiết
- Đăng ký tất cả các router endpoints
- Kết nối đến MongoDB database
- Cấu hình CORS cho phép frontend truy cập
"""

# Import các thư viện cần thiết
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import config  # Import cấu hình ứng dụng
from .routers.data_router import router as data_router  # Router xử lý CRUD dữ liệu
from .routers.stats_router import router as stats_router  # Router thống kê mô tả
from .routers.analysis_router import router as analysis_router  # Router phân tích tần suất
from .routers.external_router import router as external_router  # Router API bên ngoài
from .routers.realtime_router import router as realtime_router  # Router dữ liệu thời gian thực
from .routers.integration_router import router as integration_router  # Router tích hợp
from .routers.comprehensive_analysis_router import router as comprehensive_analysis_router  # Router phân tích toàn diện
from .routers.complete_analysis_router import router as complete_analysis_router  # Router phân tích hoàn chỉnh
import logging
from motor.motor_asyncio import AsyncIOMotorClient  # MongoDB async client

# Cấu hình logging để theo dõi hoạt động của ứng dụng
logging.basicConfig(level=logging.INFO)

# Khởi tạo ứng dụng FastAPI với tên gọi tiếng Việt
app = FastAPI(title="Phần mềm phân tích dữ liệu khí tượng thủy văn")

# Thêm middleware CORS để cho phép frontend (React) truy cập backend
# CORS (Cross-Origin Resource Sharing) cho phép trình duyệt truy cập API từ domain khác
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Cho phép tất cả domains (production nên giới hạn cụ thể)
    allow_credentials=True,  # Cho phép gửi cookies và headers xác thực
    allow_methods=["*"],  # Cho phép tất cả HTTP methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Cho phép tất cả headers
)

# Đăng ký các router - mỗi router xử lý một nhóm chức năng cụ thể
app.include_router(data_router)  # Endpoints: /data/* - CRUD dữ liệu cơ bản
app.include_router(stats_router)  # Endpoints: /stats/* - Thống kê mô tả
app.include_router(analysis_router)  # Endpoints: /analysis/* - Phân tích tần suất
app.include_router(external_router)  # Endpoints: /external/* - Tích hợp API ngoài
app.include_router(realtime_router)  # Endpoints: /realtime/* - Dữ liệu thời gian thực
app.include_router(integration_router)  # Endpoints: /integration/* - Tích hợp tổng hợp
app.include_router(comprehensive_analysis_router)  # Endpoints: /comprehensive/* - Phân tích toàn diện
app.include_router(complete_analysis_router)  # Endpoints: /complete/* - Phân tích hoàn chỉnh

# Import và đăng ký scheduler router
from .routers.scheduler_router import router as scheduler_router
app.include_router(scheduler_router)  # Endpoints: /scheduler/* - Quản lý background tasks

# Khởi tạo kết nối MongoDB - chỉ kết nối nếu có cấu hình URI
if config.MONGO_URI:
    try:
        # Tạo client MongoDB bất đồng bộ và lưu vào state của app
        app.state.mongo_client = AsyncIOMotorClient(config.MONGO_URI)
        logging.info("Kết nối MongoDB thành công")
    except Exception as e:
        # Nếu kết nối thất bại, log warning và đặt client = None
        logging.warning(f"Kết nối MongoDB thất bại: {e}")
        app.state.mongo_client = None
else:
    # Nếu không có URI MongoDB, skip kết nối (dùng cho testing hoặc development)
    logging.info("Không có URI MongoDB, bỏ qua kết nối MongoDB")
    app.state.mongo_client = None