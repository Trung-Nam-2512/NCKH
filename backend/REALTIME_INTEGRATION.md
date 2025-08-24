# Tích hợp Dữ liệu Realtime với Phân tích Tần suất

## Tổng quan

Hệ thống đã được mở rộng để tích hợp dữ liệu realtime từ API thủy văn vào mô hình phân tích tần suất. Dữ liệu được lưu trữ trong MongoDB và có thể được sử dụng cho phân tích tần suất dài hạn.

## Tính năng chính

### 1. Realtime Service (`/realtime`)

- **Fetch dữ liệu realtime**: Lấy dữ liệu từ API thủy văn
- **Auto-poll**: Tự động fetch dữ liệu mỗi 10 phút
- **Lưu trữ MongoDB**: Tích lũy dữ liệu lịch sử
- **Thống kê**: Theo dõi tình trạng dữ liệu

### 2. Integration Service (`/integration`)

- **Phân tích tức thì**: Fetch và phân tích ngay lập tức
- **Phân tích lịch sử**: Sử dụng dữ liệu đã tích lũy
- **Phân tích liên tục**: Thiết lập phân tích định kỳ
- **Khuyến nghị**: Đánh giá chất lượng dữ liệu

## API Endpoints

### Realtime Endpoints

#### GET `/realtime/stations`

Lấy danh sách tất cả trạm đo

```bash
curl -X GET "http://localhost:8000/realtime/stations"
```

#### POST `/realtime/fetch`

Fetch dữ liệu realtime theo query

```bash
curl -X POST "http://localhost:8000/realtime/fetch" \
  -H "Content-Type: application/json" \
  -d '{
    "start_time": "2024-01-01 00:00:00",
    "end_time": "2024-01-31 23:59:59",
    "station_id": "optional_station_id"
  }'
```

#### GET `/realtime/stats`

Lấy thống kê dữ liệu realtime

```bash
curl -X GET "http://localhost:8000/realtime/stats"
```

#### GET `/realtime/frequency-data`

Lấy dữ liệu sẵn sàng cho phân tích tần suất

```bash
curl -X GET "http://localhost:8000/realtime/frequency-data?min_years=5&station_id=optional"
```

#### POST `/realtime/load-frequency-data`

Load dữ liệu vào hệ thống phân tích

```bash
curl -X POST "http://localhost:8000/realtime/load-frequency-data?min_years=5"
```

### Integration Endpoints

#### POST `/integration/fetch-and-analyze`

Fetch và phân tích tức thì

```bash
curl -X POST "http://localhost:8000/integration/fetch-and-analyze?distribution_name=gumbel&agg_func=max" \
  -H "Content-Type: application/json" \
  -d '{
    "start_time": "2024-01-01 00:00:00",
    "end_time": "2024-01-31 23:59:59"
  }'
```

#### POST `/integration/analyze-historical`

Phân tích dữ liệu lịch sử

```bash
curl -X POST "http://localhost:8000/integration/analyze-historical?min_years=5&distribution_name=gumbel"
```

#### GET `/integration/summary`

Tổng quan khả năng phân tích

```bash
curl -X GET "http://localhost:8000/integration/summary"
```

#### POST `/integration/setup-continuous`

Thiết lập phân tích liên tục

```bash
curl -X POST "http://localhost:8000/integration/setup-continuous?analysis_interval_hours=24"
```

## Cấu hình

### Environment Variables

Tạo file `.env` trong thư mục `backend/`:

```env
# MongoDB
MONGO_URI=mongodb://localhost:27017

# API Configuration
STATIONS_API_BASE_URL=https://api.example.com/v1/stations
STATS_API_BASE_URL=https://api.example.com/v1/stations/stats
API_KEY=your_api_key_here

# Thresholds
DEPTH_THRESHOLD=2.0
```

### Cài đặt Dependencies

```bash
cd backend
pip install -r requirements.txt
```

## Sử dụng

### 1. Khởi động hệ thống

```bash
cd backend
uvicorn app.main:app --reload
```

### 2. Test API

Chạy script test để kiểm tra API:

```bash
python test_realtime_api.py
```

### 3. Bắt đầu tích lũy dữ liệu

```bash
# Bắt đầu auto-poll
curl -X POST "http://localhost:8000/realtime/start-auto-poll"

# Fetch dữ liệu ban đầu (2 tháng)
curl -X POST "http://localhost:8000/realtime/fetch" \
  -H "Content-Type: application/json" \
  -d '{
    "start_time": "2024-01-01 00:00:00",
    "end_time": "2024-03-01 00:00:00"
  }'
```

### 4. Phân tích tần suất

```bash
# Phân tích với dữ liệu lịch sử
curl -X POST "http://localhost:8000/integration/analyze-historical?min_years=5"

# Thiết lập phân tích liên tục
curl -X POST "http://localhost:8000/integration/setup-continuous"
```

## Đánh giá Tính khả thi

### Ưu điểm

1. **Tích lũy dữ liệu dài hạn**: MongoDB lưu trữ dữ liệu lịch sử
2. **Phân tích realtime**: Có thể phân tích ngay khi có dữ liệu mới
3. **Tự động hóa**: Auto-poll và phân tích định kỳ
4. **Linh hoạt**: Hỗ trợ nhiều trạm và nhiều phân phối
5. **Khuyến nghị thông minh**: Đánh giá chất lượng dữ liệu

### Hạn chế

1. **Phụ thuộc API**: Cần API ổn định và có sẵn
2. **Dữ liệu ngắn hạn**: API chỉ cung cấp 2 tháng dữ liệu
3. **Thời gian tích lũy**: Cần thời gian để có đủ dữ liệu cho phân tích tần suất
4. **Tần suất đo**: Phụ thuộc vào tần suất đo của trạm

### Khuyến nghị

1. **Tích lũy dữ liệu**: Chạy auto-poll liên tục để tích lũy dữ liệu
2. **Kiểm tra định kỳ**: Sử dụng `/integration/summary` để theo dõi
3. **Backup dữ liệu**: Sao lưu MongoDB định kỳ
4. **Mở rộng API**: Tìm cách lấy dữ liệu lịch sử dài hơn

## Monitoring

### Health Check

```bash
curl -X GET "http://localhost:8000/realtime/health"
```

### Thống kê

```bash
curl -X GET "http://localhost:8000/realtime/stats"
```

### Khuyến nghị

```bash
curl -X GET "http://localhost:8000/integration/recommendations"
```

## Troubleshooting

### Lỗi thường gặp

1. **API không khả dụng**: Kiểm tra cấu hình API và API_KEY
2. **MongoDB không kết nối**: Kiểm tra MONGO_URI
3. **Dữ liệu không đủ**: Chờ tích lũy thêm dữ liệu
4. **Scheduler không chạy**: Kiểm tra logs và restart service

### Logs

```bash
# Xem logs realtime
tail -f logs/realtime.log

# Kiểm tra MongoDB
mongo hydro_db --eval "db.realtime_depth.count()"
```

## Phát triển tiếp theo

1. **WebSocket**: Real-time updates cho frontend
2. **Alert System**: Cảnh báo khi có dữ liệu bất thường
3. **Data Quality**: Kiểm tra chất lượng dữ liệu tự động
4. **Machine Learning**: Dự đoán dựa trên dữ liệu realtime
5. **Multi-station Analysis**: Phân tích so sánh nhiều trạm
