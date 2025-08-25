# HƯỚNG DẪN HỆ THỐNG SCHEDULER VÀ THU THẬP DỮ LIỆU TỰ ĐỘNG

## 📋 TỔNG QUAN

Hệ thống scheduler mới được thiết kế để giải quyết bài toán thu thập dữ liệu hàng ngày từ các API chỉ cung cấp dữ liệu ngày hiện tại. Hệ thống đảm bảo:

- ✅ **Không mất dữ liệu**: Thu thập và lưu trữ dữ liệu lịch sử cho phân tích tần suất
- ✅ **Tránh trùng lặp**: Sử dụng upsert operations thay vì delete + insert
- ✅ **Tự động hóa**: Scheduler chạy ngầm thu thập dữ liệu theo lịch trình
- ✅ **Monitoring**: API endpoints và dashboard để theo dõi
- ✅ **Recovery**: Error handling và retry logic

## 🏗️ KIẾN TRÚC HỆ THỐNG

### 1. Components Chính

```
┌─────────────────────────────────────────────────────────────────┐
│                     SCHEDULER SYSTEM                            │
├─────────────────────────────────────────────────────────────────┤
│  🕐 SchedulerService                                           │
│  ├── APScheduler (Advanced Python Scheduler)                   │
│  ├── Multiple daily collection times                           │
│  ├── Health monitoring                                         │
│  └── Error recovery & retry logic                              │
├─────────────────────────────────────────────────────────────────┤
│  📊 DailyDataCollector                                         │
│  ├── API data fetching (nokttv + kttv)                        │
│  ├── Data processing & validation                              │
│  ├── Deduplication via upsert operations                       │
│  └── Historical data storage                                   │
├─────────────────────────────────────────────────────────────────┤
│  🌐 SchedulerRouter (/scheduler/*)                             │
│  ├── Management API endpoints                                  │
│  ├── Manual collection triggers                                │
│  ├── System health monitoring                                  │
│  └── Logs and statistics                                       │
└─────────────────────────────────────────────────────────────────┘
```

### 2. Database Collections

```
📚 MongoDB Collections:
├── 📖 historical_realtime_data     # Dữ liệu lịch sử cho phân tích tần suất
├── 📖 realtime_depth              # Dữ liệu hiện tại cho display (giữ nguyên)
├── 📖 data_collection_logs        # Logs của collection process
└── 📖 historical_backup           # Backup dữ liệu để recovery
```

## 🚀 TRIỂN KHAI VÀ CHẠY HỆ THỐNG

### 1. Cài Đặt Dependencies

```bash
# Cài đặt thêm packages cho scheduler
cd backend
pip install -r requirements_scheduler.txt

# Hoặc cài từng package:
pip install apscheduler==3.10.4 motor pymongo httpx pydantic
```

### 2. Cấu Hình Environment Variables

Đảm bảo file `.env` có đầy đủ:

```env
# MongoDB
MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net/database_name

# API Configuration
STATIONS_API_BASE_URL_NOKTTV=https://api.nokttv.example.com/stations
STATS_API_BASE_URL_NOKTTV=https://api.nokttv.example.com/stats
STATIONS_API_BASE_URL_KTTV=https://api.kttv.example.com/stations
STATS_API_BASE_URL_KTTV=https://api.kttv.example.com/stats
API_KEY=your_api_key_here

# Database name
DATABASE_NAME=your_database_name
```

### 3. Test Hệ Thống

```bash
# Test comprehensive tất cả components
cd backend
python test_daily_collector.py

# Test manual collection
python run_scheduler.py --test

# Test specific date collection
python run_scheduler.py --manual-collect --date 2024-01-15
```

### 4. Chạy Scheduler

#### Option 1: Foreground (Development)
```bash
cd backend
python run_scheduler.py
```

#### Option 2: Background (Production)
```bash
# Chạy trong background
cd backend
nohup python run_scheduler.py > scheduler.log 2>&1 &

# Hoặc sử dụng screen/tmux
screen -S scheduler
python run_scheduler.py
# Ctrl+A, D để detach
```

#### Option 3: Systemd Service (Linux Production)
```bash
# Tạo systemd service file
sudo python run_scheduler.py --create-service

# Enable và start service
sudo systemctl daemon-reload
sudo systemctl enable nckh-scheduler
sudo systemctl start nckh-scheduler

# Check status
sudo systemctl status nckh-scheduler
sudo journalctl -u nckh-scheduler -f
```

## 📊 MONITORING VÀ QUẢN LÝ

### 1. API Endpoints

Sau khi khởi động FastAPI server với scheduler router:

#### Kiểm Tra Trạng Thái
```bash
curl http://localhost:8000/scheduler/status
```

#### Manual Collection
```bash
# Trigger manual collection cho hôm nay
curl -X POST http://localhost:8000/scheduler/manual-collect

# Collection cho ngày cụ thể
curl -X POST http://localhost:8000/scheduler/manual-collect \
  -H "Content-Type: application/json" \
  -d '{"target_date": "2024-01-15"}'
```

#### Xem Logs
```bash
curl http://localhost:8000/scheduler/logs?limit=20&days=7
```

#### Health Check
```bash
curl http://localhost:8000/scheduler/health
```

#### Xem Job Schedule
```bash
curl http://localhost:8000/scheduler/jobs
```

### 2. Log Files

```bash
# Scheduler logs
tail -f scheduler_production.log

# Collection logs
tail -f daily_collector.log

# FastAPI logs
tail -f uvicorn.log  # Nếu có
```

## ⏰ LỊCH TRÌNH COLLECTION

### Default Schedule

Scheduler được cấu hình chạy **3 lần mỗi ngày** để đảm bảo có dữ liệu:

- 🌅 **06:30 UTC** (14:30 VN time) - Sáng
- 🌞 **14:30 UTC** (22:30 VN time) - Chiều  
- 🌙 **22:30 UTC** (06:30+1 VN time) - Tối

### Tại Sao 3 Lần?

1. **API Reliability**: APIs có thể tạm thời unavailable
2. **Data Availability**: Dữ liệu có thể được cập nhật vào các thời điểm khác nhau trong ngày
3. **Fault Tolerance**: Nếu 1-2 lần failed, vẫn có cơ hội thu thập được dữ liệu

### Customization

Có thể thay đổi trong `SchedulerService.__init__()`:

```python
'collection_times': [
    {'hour': 6, 'minute': 30},    # 6:30 AM UTC
    {'hour': 14, 'minute': 30},   # 2:30 PM UTC  
    {'hour': 22, 'minute': 30}    # 10:30 PM UTC
]
```

## 🔧 TROUBLESHOOTING

### 1. Common Issues

#### Database Connection Failed
```bash
# Check MongoDB URI
echo $MONGO_URI

# Test connection manually
python -c "
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
async def test():
    client = AsyncIOMotorClient('your_uri')
    await client.admin.command('ismaster')
    print('✅ Connection successful')
asyncio.run(test())
"
```

#### API Authentication Failed
```bash
# Check API key
echo $API_KEY

# Test API manually
curl -H "x-api-key: $API_KEY" https://your-api-endpoint.com/stations
```

#### No Data Collected
```bash
# Check API responses
python run_scheduler.py --test --log-level DEBUG

# Check database
mongo "your_connection_string" --eval "
db.historical_realtime_data.find().limit(5).pretty()
"
```

### 2. Performance Issues

#### High Memory Usage
- Giảm `batch_size` trong collection process
- Implement data streaming for large datasets
- Add memory monitoring

#### Slow Collection
- Check network latency to APIs
- Implement parallel API calls
- Add connection pooling

### 3. Data Issues

#### Duplicate Records
- Verify unique indexes created
- Check upsert logic
- Review collection logs

#### Missing Data
- Check API availability during collection times
- Review error logs
- Implement backfill script

## 📈 DATA FLOW CHO FREQUENCY ANALYSIS

### 1. Data Storage Strategy

```
🔄 Daily Collection Flow:
├── 📥 Fetch từ APIs (nokttv + kttv)
├── 🔄 Process & validate data  
├── 💾 Upsert vào historical_realtime_data (with deduplication)
├── 🔄 Update realtime_depth (for current display)
└── 📝 Log collection results
```

### 2. Historical Data Structure

```json
{
  "_id": "ObjectId(...)",
  "station_id": "056882",
  "code": "056882", 
  "name": "Trạm Thủ Đức",
  "latitude": 10.8721,
  "longitude": 106.7674,
  "api_type": "nokttv",
  "time_point": "2024-01-15T14:30:00Z",
  "depth": 1.25,
  "collection_date": "2024-01-15",
  "created_at": "2024-01-15T22:30:45Z"
}
```

### 3. Frequency Analysis Integration

```javascript
// Frontend có thể query historical data
const response = await fetch('/api/data/historical', {
  method: 'POST',
  body: JSON.stringify({
    station_id: '056882',
    start_date: '2023-01-01',
    end_date: '2024-01-15',
    aggregation: 'daily_max'  // Lấy max depth per day
  })
});
```

## 🛡️ BACKUP VÀ RECOVERY

### 1. Automatic Backups

Hệ thống tự động backup dữ liệu trước khi collection:

- Backup stored trong `historical_backup` collection
- Retention: 7 days (configurable)
- Automatic cleanup via scheduler

### 2. Manual Backup

```bash
# Export collection
mongoexport --uri="your_connection_string" \
  --collection=historical_realtime_data \
  --out=backup_$(date +%Y%m%d).json

# Import back
mongoimport --uri="your_connection_string" \
  --collection=historical_realtime_data \
  --file=backup_20240115.json
```

### 3. Data Recovery

```python
# Script để recover từ backup
from app.services.daily_data_collector import DailyDataCollector
import asyncio

async def recover_data(backup_date):
    collector = DailyDataCollector()
    await collector.initialize_database()
    
    # Find backup
    backup = await collector.db.historical_backup.find_one({
        'target_date': backup_date
    })
    
    if backup:
        # Restore data
        await collector.db.historical_realtime_data.insert_many(backup['data'])
        print(f"✅ Recovered {len(backup['data'])} records")

# Usage
asyncio.run(recover_data('2024-01-15'))
```

## 🔮 FUTURE ENHANCEMENTS

### 1. Advanced Features

- **Real-time Alerting**: Email/SMS alerts khi collection failed
- **Data Validation**: Advanced QC checks cho dữ liệu
- **Predictive Collection**: Machine learning để predict optimal collection times
- **Multi-region**: Support multiple geographic regions
- **API Versioning**: Handle API changes gracefully

### 2. Performance Optimizations

- **Caching Layer**: Redis cache cho frequently accessed data
- **Data Compression**: Compress historical data
- **Partitioning**: Time-based partitioning for large datasets
- **Indexing**: Advanced indexing strategies

### 3. Integration Improvements

- **Grafana Dashboard**: Visual monitoring dashboard
- **Prometheus Metrics**: Detailed metrics collection
- **Docker Support**: Containerized deployment
- **Kubernetes**: Scalable container orchestration

## 📞 SUPPORT

### 1. Logs Location

- **Scheduler**: `scheduler_production.log`
- **Collection**: `daily_collector.log`
- **FastAPI**: Check uvicorn logs

### 2. Debug Mode

```bash
python run_scheduler.py --test --log-level DEBUG
```

### 3. Health Monitoring

Thường xuyên check health endpoint:

```bash
curl http://localhost:8000/scheduler/health | jq
```

---

**🎯 Kết luận**: Hệ thống scheduler này giải quyết hoàn toàn bài toán thu thập dữ liệu hàng ngày từ APIs chỉ cung cấp dữ liệu ngày hiện tại, đảm bảo có đủ dữ liệu lịch sử cho phân tích tần suất mà không gây trùng lặp hay mất dữ liệu.