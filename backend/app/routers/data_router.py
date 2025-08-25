"""
DATA ROUTER - API endpoints cho việc quản lý và xử lý dữ liệu thủy văn

Module này chứa các REST API endpoints để:
- Upload dữ liệu từ file CSV/Excel
- Nhập dữ liệu thủ công qua JSON payload
- Truy xuất dữ liệu hiện tại đang được xử lý
- Xóa/reset dữ liệu trong hệ thống

Các loại dữ liệu được hỗ trợ:
- Time series hàng năm: [Year, Value]
- Time series hàng tháng: [Year, Month, Value]
- Dữ liệu thủ công từ form frontend

Design pattern:
- RESTful API với HTTP verbs chuẩn (GET, POST, DELETE)
- Dependency injection cho loose coupling
- Centralized error handling với HTTPException
- Async operations cho file upload (I/O bound tasks)
"""

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from ..dependencies import get_data_service
from ..services.data_service import DataService
from ..models.data_models import UploadManualPayload

# Tạo router với prefix "/data" để group tất cả data-related endpoints
# Tags giúp organize API documentation trong FastAPI auto-generated docs
router = APIRouter(prefix="/data", tags=["data"])

@router.post("/upload")
async def upload_file(file: UploadFile = File(...), data_service: DataService = Depends(get_data_service)):
    """
    ENDPOINT UPLOAD FILE DỮ LIỆU THỦY VĂN
    
    Endpoint này cho phép user upload file dữ liệu (CSV hoặc Excel) để phân tích.
    Hệ thống sẽ tự động detect format và validate dữ liệu.
    
    Flow xử lý:
    1. Nhận file từ multipart/form-data request
    2. Validate file extension (.csv hoặc .xlsx)
    3. Parse file content thành DataFrame
    4. Auto-detect main data column (không phải Year/Month)
    5. Normalize và clean data (remove invalid values)
    6. Cache data trong memory để sử dụng cho các analysis endpoints
    
    Args:
        file: UploadFile object từ FastAPI
            - Hỗ trợ: .csv, .xlsx
            - Max file size được control ở middleware level
        data_service: DataService instance qua dependency injection
    
    Returns:
        Dict: {"status": "success", "data": processed_records}
    
    Raises:
        HTTPException 400: File format không hợp lệ hoặc dữ liệu invalid
        HTTPException 500: Lỗi xử lý file (corrupted, memory issues, etc.)
    
    Examples:
        curl -X POST "http://localhost:8000/data/upload" \
             -H "Content-Type: multipart/form-data" \
             -F "file=@rainfall_data.csv"
    """
    return await data_service.upload_file(file)

@router.post("/upload_manual")
def upload_manual(payload: UploadManualPayload, data_service: DataService = Depends(get_data_service)):
    """
    ENDPOINT NHẬP DỮ LIỆU THỦ CÔNG
    
    Endpoint này cho phép user nhập dữ liệu trực tiếp từ frontend form
    thay vì upload file. Hữu ích khi:
    - Dữ liệu ít, nhập manual nhanh hơn
    - Không có sẵn file, user muốn input trực tiếp
    - Testing với sample data
    - Bổ sung/chỉnh sửa data points cụ thể
    
    Flow xử lý:
    1. Nhận JSON payload qua POST request body
    2. Validate payload structure với Pydantic model
    3. Convert JSON data thành DataFrame
    4. Apply cùng logic validation như upload file
    5. Detect main column và normalize data
    6. Cache processed data trong memory
    
    Args:
        payload: UploadManualPayload object chứa:
            - data: List[Dict] - Array các record dữ liệu
            - Format có thể: [{"Year": 2020, "Value": 123.5}, ...]
                       hoặc: [{"Year": 2020, "Month": 1, "Rainfall": 45.2}, ...]
        data_service: DataService instance từ dependency injection
    
    Returns:
        Dict: {"status": "success", "data": processed_records}
        
    Raises:
        HTTPException 400: 
            - Payload structure không hợp lệ
            - Missing required fields (Year)
            - Invalid data types
        HTTPException 500: Lỗi xử lý dữ liệu
        
    Examples:
        POST /data/upload_manual
        {
            "data": [
                {"Year": 2020, "Rainfall": 1200.5},
                {"Year": 2021, "Rainfall": 1150.8},
                {"Year": 2022, "Rainfall": 1300.2}
            ]
        }
    """
    return data_service.upload_manual(payload)

@router.get("/current")
def get_current_data(data_service: DataService = Depends(get_data_service)):
    """
    ENDPOINT LẤY DỮ LIỆU HIỆN TẠI
    
    Endpoint này trả về dữ liệu đang được cache trong memory sau khi
    user đã upload hoặc input manual data. Frontend sử dụng endpoint này để:
    - Display data preview table cho user xem
    - Validate dữ liệu trước khi thực hiện analysis
    - Debug và troubleshoot data issues
    - Show data summary và basic info
    
    Response bao gồm:
    - data: Array of records (JSON format của DataFrame)
    - main_column: Tên của cột chứa dữ liệu chính để phân tích
    - shape: Tuple [rows, columns] cho biết kích thước dataset
    
    Args:
        data_service: DataService instance từ dependency injection
    
    Returns:
        Dict: {
            "data": List[Dict] - Dữ liệu dạng records,
            "main_column": str - Tên cột dữ liệu chính,  
            "shape": Tuple[int, int] - (số rows, số columns)
        }
    
    Raises:
        HTTPException 404: Chưa có dữ liệu nào được load vào hệ thống
        
    Examples:
        GET /data/current
        Response:
        {
            "data": [
                {"Year": 2020, "Month": 1, "Rainfall": 45.2},
                {"Year": 2020, "Month": 2, "Rainfall": 38.7}
            ],
            "main_column": "Rainfall",
            "shape": [24, 3]
        }
    """
    if data_service.data is None:
        raise HTTPException(status_code=404, detail="Chưa có dữ liệu được tải")
    return {
        "data": data_service.data.to_dict(orient="records"),
        "main_column": data_service.main_column,
        "shape": data_service.data.shape
    }

@router.delete("/clear")
def clear_data(data_service: DataService = Depends(get_data_service)):
    """
    ENDPOINT XÓA/RESET DỮ LIỆU
    
    Endpoint này xóa toàn bộ dữ liệu đang được cache trong memory,
    đưa hệ thống về trạng thái ban đầu. Sử dụng khi:
    - User muốn upload dataset mới
    - Clear cache để free memory
    - Reset hệ thống sau khi analysis xong
    - Dev/debug cần clean state
    
    Các thao tác được thực hiện:
    1. Set data DataFrame = None (giải phóng memory)
    2. Set main_column = None (reset metadata)
    3. Garbage collection sẽ tự động clean up memory
    4. Tất cả analysis results sẽ không còn valid
    
    Lưu ý: Thao tác này KHÔNG thể undo. User sẽ phải upload
    dữ liệu lại nếu muốn tiếp tục phân tích.
    
    Args:
        data_service: DataService instance từ dependency injection
        
    Returns:
        Dict: {"message": "Dữ liệu đã được xóa"}
        
    Side Effects:
        - Toàn bộ cached data bị xóa khỏi memory
        - Các analysis endpoints sẽ return 404 error
        - Frontend cần handle state reset
        
    Examples:
        DELETE /data/clear
        Response: {"message": "Dữ liệu đã được xóa"}
        
        Sau đó:
        GET /data/current → 404 Error
        POST /analysis/basic_stats → 404 Error  
    """
    # Reset data và metadata về None
    data_service.data = None
    data_service.main_column = None
    
    return {"message": "Dữ liệu đã được xóa"}
