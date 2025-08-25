"""
DỊCH VỤ MONGODB (MONGO SERVICE) - Quản lý kết nối và operations với MongoDB Atlas

Chức năng chính:
- Quản lý kết nối async đến MongoDB Atlas cloud database
- Theo dõi và ghi nhận lượt truy cập hệ thống
- Thống kê usage và analytics
- CRUD operations cho dữ liệu persistent
- Connection pooling và error recovery

Sử dụng Motor driver:
- Async/await support cho non-blocking operations
- Connection pooling tự động
- Retry logic built-in
- Compatible với FastAPI async framework
"""

import motor.motor_asyncio  # MongoDB async driver
from typing import Dict, Any
from datetime import datetime, date
import logging
from ..config import config  # Import cấu hình MONGO_URI

class MongoService:
    """
    DỊCH VỤ QUẢN LÝ MONGODB
    
    Service này quản lý toàn bộ tương tác với MongoDB database.
    Sử dụng Singleton pattern để maintain connection pool và avoid
    multiple connection overhead.
    
    Attributes:
        client: Motor AsyncIOMotorClient instance
        db: Database instance
        visit_collection: Collection để tracking visits
    """
    
    def __init__(self):
        """
        Khởi tạo MongoService và thiết lập kết nối
        
        Automatically connect đến MongoDB khi service được khởi tạo.
        Sử dụng lazy connection - connection sẽ được establish khi cần.
        """
        self.client = None              # MongoDB client instance
        self.db = None                  # Database instance
        self.visit_collection = None    # Collection cho visit tracking
        self._connect()                 # Thiết lập kết nối ngay khi init

    def _connect(self):
        """
        Thiết lập kết nối đến MongoDB Atlas cloud database
        
        Connection process:
        1. Kiểm tra MONGO_URI trong config
        2. Tạo async client với connection string
        3. Chọn database và collection
        4. Log status kết nối
        
        Raises:
            ValueError: Khi MONGO_URI không được cấu hình
            Exception: Khi kết nối thất bại
        """
        try:
            # Kiểm tra xem có MONGO_URI trong config không
            if not config.MONGO_URI:
                raise ValueError(
                    "MONGO_URI không được cấu hình trong file .env. "
                    "Vui lòng thêm MONGO_URI=mongodb+srv://... vào file .env"
                )
            
            # Tạo async MongoDB client với connection pooling
            self.client = motor.motor_asyncio.AsyncIOMotorClient(config.MONGO_URI)
            
            # Chọn database và collection (sử dụng existing database)
            self.db = self.client.visits_db                    # Database name
            self.visit_collection = self.db.visits             # Collection cho visits
            
            logging.info("✅ Kết nối MongoDB Atlas thành công")
            
        except Exception as e:
            logging.error(f"❌ Lỗi kết nối MongoDB: {str(e)}")
            # Re-raise exception để caller có thể handle
            raise

    async def record_visit(self) -> bool:
        """
        Ghi nhận một lượt truy cập hệ thống vào database
        
        Mỗi lần user truy cập hệ thống, một document sẽ được tạo để:
        - Theo dõi usage patterns
        - Analytics và reporting
        - Monitor system activity
        - Compliance và audit trails
        
        Document structure:
        {
            "timestamp": datetime,     # Thời điểm truy cập (UTC)
            "_id": ObjectId           # Auto-generated unique ID
        }
        
        Returns:
            bool: True nếu ghi nhận thành công, False nếu thất bại
        """
        try:
            # Lấy timestamp hiện tại (UTC để consistency across timezones)
            now = datetime.utcnow()
            
            # Tạo và insert document mới cho lượt truy cập
            await self.visit_collection.insert_one({
                "timestamp": now
            })
            
            logging.info(f"📊 Đã ghi nhận lượt truy cập: {now.strftime('%Y-%m-%d %H:%M:%S')} UTC")
            return True
            
        except Exception as e:
            logging.error(f"Lỗi ghi lượt truy cập: {str(e)}")
            return False

    async def get_visit_stats(self) -> Dict[str, Any]:
        """Lấy thống kê lượt truy cập"""
        try:
            # Lấy tổng số lượt truy cập
            total_visits = await self.visit_collection.count_documents({})
            
            # Lấy thống kê theo ngày (7 ngày gần nhất)
            from datetime import timedelta
            seven_days_ago = datetime.utcnow() - timedelta(days=7)
            
            # Pipeline để tính số lượt truy cập theo ngày
            pipeline = [
                {
                    "$match": {
                        "timestamp": {"$gte": seven_days_ago}
                    }
                },
                {
                    "$group": {
                        "_id": {
                            "$dateToString": {
                                "format": "%Y-%m-%d",
                                "date": "$timestamp"
                            }
                        },
                        "daily_visits": {"$sum": 1}
                    }
                },
                {
                    "$sort": {"_id": 1}
                }
            ]
            
            recent_stats = await self.visit_collection.aggregate(pipeline).to_list(7)
            
            # Tạo dict cho daily_stats
            daily_stats = {}
            for stat in recent_stats:
                daily_stats[stat["_id"]] = stat["daily_visits"]
            
            return {
                "total_visits": total_visits,
                "daily_stats": daily_stats
            }
        except Exception as e:
            logging.error(f"Lỗi lấy thống kê lượt truy cập: {str(e)}")
            return {
                "total_visits": 0,
                "daily_stats": {}
            }

    async def close_connection(self):
        """Đóng kết nối MongoDB"""
        if self.client:
            self.client.close()
            logging.info("Đã đóng kết nối MongoDB") 