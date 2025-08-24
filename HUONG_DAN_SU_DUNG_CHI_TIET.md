# HƯỚNG DẪN SỬ DỤNG CHI TIẾT
## Hệ Thống Phân Tích Tần Suất Thủy Văn

---

**Phiên bản:** 2.0  
**Ngày cập nhật:** 24/08/2025  
**Dành cho:** Kỹ sư thủy văn, Nhà nghiên cứu, Sinh viên  
**Cấp độ:** Từ cơ bản đến nâng cao  

---

## MỤC LỤC

1. [Giới Thiệu Tổng Quan](#1-giới-thiệu-tổng-quan)
2. [Cài Đặt và Khởi Động](#2-cài-đặt-và-khởi-động)
3. [Giao Diện Người Dùng](#3-giao-diện-người-dùng)
4. [Nhập Liệu và Chuẩn Bị Dữ Liệu](#4-nhập-liệu-và-chuẩn-bị-dữ-liệu)
5. [Phân Tích Tần Suất Cơ Bản](#5-phân-tích-tần-suất-cơ-bản)
6. [Phân Tích Tần Suất Nâng Cao](#6-phân-tích-tần-suất-nâng-cao)
7. [Kiểm Soát Chất Lượng Dữ Liệu](#7-kiểm-soát-chất-lượng-dữ-liệu)
8. [Xuất Kết Quả và Báo Cáo](#8-xuất-kết-quả-và-báo-cáo)
9. [Xử Lý Sự Cố Thường Gặp](#9-xử-lý-sự-cố-thường-gặp)
10. [Câu Hỏi Thường Gặp](#10-câu-hỏi-thường-gặp)

---

## 1. GIỚI THIỆU TỔNG QUAN

### 1.1 Về Hệ Thống

Hệ thống Phân Tích Tần Suất Thủy Văn là công cụ chuyên nghiệp được thiết kế để:

- **Phân tích tần suất** dữ liệu thủy văn (lưu lượng, lượng mưa, mực nước)
- **Tính toán kỳ tái hiện** cho thiết kế công trình thủy lợi
- **Đánh giá độ tin cậy** của các phân phối xác suất
- **Tuân thủ tiêu chuẩn quốc tế** WMO-168, ISO 14688, ASCE

### 1.2 Đối Tượng Sử Dụng

- **Kỹ sư thủy văn:** Thiết kế đập, hồ chứa, hệ thống thoát nước
- **Nhà quy hoạch:** Quy hoạch tài nguyên nước, quản lý lũ lụt  
- **Nhà nghiên cứu:** Nghiên cứu khí hậu, biến đổi khí hậu
- **Sinh viên:** Học tập và nghiên cứu thủy văn

### 1.3 Tính Năng Chính

✅ **9 mô hình phân phối xác suất:** Gumbel, GEV, Log-normal, Weibull, Gamma, v.v.  
✅ **Kiểm soát chất lượng 9 bước** theo tiêu chuẩn WMO  
✅ **Tính toán kỳ tái hiện** từ 2-10000 năm  
✅ **Đánh giá độ tin cậy** với confidence intervals  
✅ **Xuất báo cáo** đa định dạng (PDF, Excel, PNG)  
✅ **Giao diện tiếng Việt** thân thiện với người dùng  

---

## 2. CÀI ĐẶT VÀ KHỞI ĐỘNG

### 2.1 Yêu Cầu Hệ Thống

**Tối thiểu:**
- CPU: 2 cores, 2.0 GHz
- RAM: 4 GB
- Ổ cứng: 2 GB trống
- Hệ điều hành: Windows 10/11, macOS 10.15+, Ubuntu 18.04+

**Khuyến nghị:**
- CPU: 4+ cores, 3.0+ GHz
- RAM: 8+ GB
- Ổ cứng: SSD với 5+ GB trống
- Kết nối internet: Để cập nhật và tải dữ liệu

### 2.2 Cài Đặt Bằng Docker (Khuyến nghị)

1. **Cài đặt Docker:**
   ```bash
   # Windows: Tải Docker Desktop từ docker.com
   # macOS: brew install --cask docker
   # Ubuntu: sudo apt install docker.io
   ```

2. **Tải và chạy hệ thống:**
   ```bash
   # Clone repository
   git clone https://github.com/hydroanalysis-vietnam/frequency-analysis
   cd frequency-analysis
   
   # Chạy với Docker Compose
   docker-compose up -d
   ```

3. **Truy cập hệ thống:**
   - Mở trình duyệt web
   - Truy cập: `http://localhost:3000`
   - Đăng nhập với tài khoản mặc định

### 2.3 Cài Đặt Thủ Công

**Backend (Python/FastAPI):**
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Database (MongoDB):**
```bash
# Cài MongoDB Community Edition
# Windows: Download từ mongodb.com
# macOS: brew install mongodb-community
# Ubuntu: sudo apt install mongodb

# Khởi động MongoDB
mongod --dbpath ./data/db
```

**Frontend (React):**
```bash
cd frontend
npm install
npm start
```

### 2.4 Kiểm Tra Cài Đặt

1. **Kiểm tra Backend:** `http://localhost:8000/docs`
2. **Kiểm tra Frontend:** `http://localhost:3000`
3. **Kiểm tra Database:** `mongo --eval "db.stats()"`

---

## 3. GIAO DIỆN NGƯỜI DÙNG

### 3.1 Trang Chính

Giao diện trang chính bao gồm:

```
┌─────────────────────────────────────────────────────────┐
│  🏠 Hệ Thống Phân Tích Tần Suất Thủy Văn              │
├─────────────────────────────────────────────────────────┤
│  📊 Dự Án  │  📈 Phân Tích  │  📋 Báo Cáo  │  ⚙️ Cài Đặt │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  🎯 Quick Start:                                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │ Tạo Dự Án  │  │ Nhập Dữ Liệu│  │ Chạy Phân   │    │
│  │    Mới      │  │             │  │    Tích     │    │
│  └─────────────┘  └─────────────┘  └─────────────┘    │
│                                                         │
│  📝 Dự Án Gần Đây:                                    │
│  • Dự án Sông Hồng - 15/08/2025                       │
│  • Phân tích lũ Đồng bằng - 10/08/2025                │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### 3.2 Menu Chính

**📊 Dự Án:**
- Tạo dự án mới
- Mở dự án có sẵn
- Quản lý dự án
- Sao lưu/Phục hồi

**📈 Phân Tích:**
- Phân tích tần suất cơ bản
- Phân tích tần suất nâng cao
- So sánh phân phối
- Kiểm định thống kê

**📋 Báo Cáo:**
- Tạo báo cáo tự động
- Xuất biểu đồ
- Xuất bảng số liệu
- Templates báo cáo

**⚙️ Cài Đặt:**
- Cài đặt hiển thị
- Cài đặt tính toán
- Quản lý người dùng
- Cập nhật hệ thống

### 3.3 Thanh Công Cụ

```
[📁 Mở] [💾 Lưu] [📊 Biểu đồ] [🔍 Phóng to] [🖨️ In] [❓ Trợ giúp]
```

---

## 4. NHẬP LIỆU VÀ CHUẨN BỊ DỮ LIỆU

### 4.1 Định Dạng Dữ Liệu Đầu Vào

Hệ thống hỗ trợ nhiều định dạng:

**CSV/Excel (Khuyến nghị):**
```csv
Nam,Gia_Tri,Don_Vi,Ghi_Chu
1990,1250.5,m3/s,Lưu lượng trung bình năm
1991,1380.2,m3/s,
1992,1470.8,m3/s,Năm có lũ lớn
...
```

**Text file:**
```
# Dữ liệu lưu lượng sông ABC
# Đơn vị: m3/s
# Thời kỳ: 1990-2020
1250.5
1380.2
1470.8
...
```

**JSON:**
```json
{
  "station": "Sông Hồng tại Hà Nội",
  "parameter": "discharge",
  "unit": "m3/s",
  "period": "1990-2020",
  "data": [
    {"year": 1990, "value": 1250.5},
    {"year": 1991, "value": 1380.2}
  ]
}
```

### 4.2 Cách Nhập Dữ Liệu

**Phương pháp 1: Upload file**

1. Nhấn nút **"📁 Nhập Dữ Liệu"**
2. Chọn file từ máy tính (CSV, Excel, TXT, JSON)
3. Xác nhận định dạng cột:
   - Cột năm
   - Cột giá trị  
   - Đơn vị đo
4. Kiểm tra preview dữ liệu
5. Nhấn **"✅ Xác Nhận"**

**Phương pháp 2: Nhập thủ công**

1. Nhấn **"✏️ Nhập Thủ Công"**
2. Điền thông tin trạm:
   ```
   Tên trạm: [Sông Hồng tại Hà Nội]
   Thông số: [Lưu lượng]
   Đơn vị:   [m3/s]
   Thời kỳ:  [1990-2020]
   ```
3. Nhập dữ liệu theo bảng:
   ```
   Năm    │ Giá Trị  │ Ghi Chú
   ───────┼──────────┼─────────
   1990   │ 1250.5   │ 
   1991   │ 1380.2   │
   ...
   ```

**Phương pháp 3: Kết nối API**

1. Nhấn **"🌐 Kết Nối API"**
2. Cấu hình kết nối:
   - URL API
   - API key (nếu có)
   - Tham số truy vấn
3. Test kết nối
4. Đồng bộ dữ liệu

### 4.3 Kiểm Tra Dữ Liệu Đầu Vào

Hệ thống tự động kiểm tra:

**✅ Kiểm tra cơ bản:**
- Định dạng số hợp lệ
- Không có giá trị âm (trừ nhiệt độ)
- Đơn vị phù hợp

**⚠️ Cảnh báo:**
- Dữ liệu < 10 năm: "Khuyến nghị ≥ 30 năm"
- Giá trị ngoại lai: "Có X giá trị bất thường"
- Dữ liệu thiếu: "Thiếu Y năm dữ liệu"

**❌ Lỗi nghiêm trọng:**
- Dữ liệu < 2 năm: "Không đủ dữ liệu phân tích"
- Tất cả giá trị bằng nhau: "Dữ liệu không có biến đổi"

---

## 5. PHÂN TÍCH TẦN SUẤT CƠ BẢN

### 5.1 Bước 1: Chọn Dữ Liệu

1. Từ màn hình chính, nhấn **"📈 Phân Tích"**
2. Chọn **"🎯 Phân Tích Cơ Bản"**
3. Chọn bộ dữ liệu từ danh sách:
   ```
   📋 Dự Án: Phân tích lũ sông ABC
   📊 Dữ liệu: Lưu lượng cực đại năm (1990-2020)
   📈 Loại: 31 giá trị, đơn vị m³/s
   ```

### 5.2 Bước 2: Cài Đặt Phân Tích

**Tham số cơ bản:**
```
┌─────────────────────────────────────┐
│ ⚙️ Cài Đặt Phân Tích Tần Suất     │
├─────────────────────────────────────┤
│ Loại phân tích: ● Tự động          │
│                 ○ Thủ công         │
│                                     │
│ Phân phối:      ☑️ Gumbel          │
│                 ☑️ Log-normal      │
│                 ☑️ GEV             │
│                 ☑️ Weibull         │
│                                     │
│ Kỳ tái hiện:    ☑️ 2, 5, 10 năm   │
│                 ☑️ 25, 50, 100 năm │
│                 ☑️ 200, 500 năm    │
│                                     │
│ [🔍 Chi Tiết] [▶️ Chạy Phân Tích] │
└─────────────────────────────────────┘
```

### 5.3 Bước 3: Chạy Phân Tích

1. Nhấn **"▶️ Chạy Phân Tích"**
2. Hệ thống sẽ hiển thị thanh tiến trình:
   ```
   🔄 Đang xử lý...
   ├─ ✅ Kiểm tra dữ liệu đầu vào
   ├─ ✅ Tính toán plotting position  
   ├─ 🔄 Ước lượng tham số phân phối
   └─ ⏳ Tính toán kỳ tái hiện
   ```

3. Kết quả hiển thị trong ~5-10 giây

### 5.4 Bước 4: Xem Kết Quả

**Bảng Tóm Tắt:**
```
📊 KẾT QUẢ PHÂN TÍCH TẦN SUẤT
════════════════════════════════════════
Dữ liệu: 31 năm (1990-2020)
Trạm: Sông ABC tại XYZ
Thông số: Lưu lượng cực đại năm (m³/s)

🎯 PHÂN PHỐI TỐT NHẤT: Gumbel
   • Location (μ): 1,850 m³/s
   • Scale (β): 320 m³/s
   • AIC: 425.3 (thấp nhất)

📈 KỲ TÁI HIỆN:
   T = 2 năm:    1,627 m³/s
   T = 5 năm:    2,115 m³/s  
   T = 10 năm:   2,437 m³/s
   T = 25 năm:   2,851 m³/s
   T = 50 năm:   3,144 m³/s
   T = 100 năm:  3,437 m³/s
   T = 200 năm:  3,729 m³/s
```

**Biểu Đồ Chính:**

1. **Biểu đồ tần suất:** Điểm quan sát vs đường cong lý thuyết
2. **Biểu đồ so sánh phân phối:** Nhiều phân phối trên cùng đồ thị
3. **Biểu đồ return period:** Kỳ tái hiện với confidence intervals

### 5.5 Bước 5: Đánh Giá Kết Quả

**Chỉ số đánh giá:**
```
✅ ĐÁNH GIÁ CHẤT LƯỢNG
─────────────────────────
• Kolmogorov-Smirnov: p = 0.342 > 0.05 ✅
• Chi-square: p = 0.156 > 0.05 ✅  
• Correlation coefficient: r = 0.987 ✅
• Root Mean Square Error: 89.5 m³/s

🎖️ XẾP HẠNG TỔNG THỂ: A (Tốt)
💡 Khuyến nghị: Sử dụng được cho thiết kế
```

---

## 6. PHÂN TÍCH TẦN SUẤT NÂNG CAO

### 6.1 Phân Tích Tùy Chỉnh

**Chế độ Expert:**
```
🔬 PHÂN TÍCH CHUYÊN SÂU
┌─────────────────────────────────────┐
│ 📊 Phương pháp ước lượng:          │
│   ● Maximum Likelihood (MLE)       │
│   ○ Method of Moments (MOM)        │  
│   ○ L-Moments                      │
│                                     │
│ 📈 Plotting position:              │
│   ● Weibull: i/(n+1)              │
│   ○ Gringorten: (i-0.44)/(n+0.12) │
│   ○ Hazen: (i-0.5)/n              │
│                                     │
│ 🎯 Confidence level:               │
│   ● 95%  ○ 90%  ○ 99%             │
│                                     │
│ 📋 Tùy chọn nâng cao:              │
│   ☑️ Phân tích sensitivity         │
│   ☑️ Bootstrap confidence intervals │
│   ☑️ Outlier detection             │
│   ☑️ Trend analysis                │
└─────────────────────────────────────┘
```

### 6.2 So Sánh Nhiều Phân Phối

1. **Chọn phân phối để so sánh:**
   ```
   ☑️ Gumbel (EV1)          ☑️ Weibull (EV3)
   ☑️ GEV (Generalized)     ☑️ Gamma  
   ☑️ Log-normal (2-param)  ☑️ Log-Pearson III
   ☑️ Normal                ☑️ Exponential
   ```

2. **Bảng so sánh kết quả:**
   ```
   BẢNG SO SÁNH CÁC PHÂN PHỐI
   ═══════════════════════════════════════════════════
   Phân phối    │ AIC   │ BIC   │ K-S    │ Q100 (m³/s)
   ─────────────┼───────┼───────┼────────┼─────────────
   Gumbel       │ 425.3 │ 429.8 │ 0.089  │ 3,437 ⭐
   GEV          │ 427.1 │ 433.2 │ 0.078  │ 3,521
   Log-normal   │ 431.6 │ 436.1 │ 0.125  │ 3,892
   Weibull      │ 428.9 │ 434.5 │ 0.094  │ 3,315
   Gamma        │ 433.2 │ 437.7 │ 0.156  │ 3,785
   
   🏆 TỐT NHẤT: Gumbel (AIC thấp nhất)
   ```

3. **Biểu đồ overlay:** Tất cả đường cong trên cùng biểu đồ

### 6.3 Phân Tích Độ Không Chắc Chắn

**Bootstrap Analysis:**
```
🎲 PHÂN TÍCH BOOTSTRAP (N = 1000)
─────────────────────────────────────
Kỳ tái hiện │ Median │ CI 95% Lower │ CI 95% Upper
────────────┼────────┼──────────────┼──────────────
T = 10 năm  │  2,437 │      2,180   │      2,749
T = 50 năm  │  3,144 │      2,756   │      3,687
T = 100 năm │  3,437 │      2,946   │      4,128
T = 500 năm │  4,287 │      3,421   │      5,492

💡 Nhận xét: Độ không chắc chắn tăng theo kỳ tái hiện
```

### 6.4 Phân Tích Trend và Stationarity

**Kiểm tra xu hướng:**
```
📈 PHÂN TÍCH XU HƯỚNG
─────────────────────
• Mann-Kendall test:
  - Tau = 0.185
  - p-value = 0.094 > 0.05
  - Kết luận: KHÔNG có xu hướng đáng kể

• Linear trend:
  - Slope = 2.3 m³/s/năm  
  - R² = 0.089
  - p-value = 0.112

🔍 Stationarity check: ✅ PASS
💡 Dữ liệu phù hợp cho phân tích tần suất
```

### 6.5 Phát Hiện Ngoại Lai

**Outlier Detection:**
```
🔍 PHÁT HIỆN NGOẠI LAI
─────────────────────
Phương pháp: Grubbs test + Rosner test

Giá trị nghi ngờ:
• 1998: 4,250 m³/s (Z-score = 2.89) ⚠️
• 2003: 4,120 m³/s (Z-score = 2.67) ⚠️

Khuyến nghị:
✅ Giữ lại: Có thể là lũ lịch sử quan trọng
⚠️ Kiểm tra: Xác minh tính chính xác của dữ liệu
```

---

## 7. KIỂM SOÁT CHẤT LƯỢNG DỮ LIỆU

### 7.1 Quy Trình 9 Bước Theo WMO-168

Hệ thống tự động thực hiện 9 bước kiểm soát chất lượng theo tiêu chuẩn WMO:

```
✅ KIỂM SOÁT CHẤT LƯỢNG WMO-168
═══════════════════════════════════
1. ✅ Kiểm tra completeness (hoàn chỉnh)
   • Missing data: 0/31 năm (0%)
   • Record length: 31 năm ≥ 10 năm minimum

2. ✅ Kiểm tra consistency (nhất quán)  
   • Internal consistency: PASS
   • Temporal consistency: PASS

3. ✅ Kiểm tra credibility (tin cậy)
   • Physical limits: PASS (0 < Q < 10,000)
   • Reasonable range: PASS

4. ✅ Kiểm tra outliers (ngoại lai)
   • Statistical outliers: 2 detected
   • Physical outliers: None

5. ✅ Kiểm tra trend (xu hướng)
   • Mann-Kendall: p = 0.094 (no trend)
   • Sen's slope: 2.3 m³/s/year

6. ✅ Kiểm tra seasonality (tính mùa vụ)
   • Seasonal Kendall: Not applicable (annual data)

7. ✅ Kiểm tra homogeneity (đồng nhất)
   • SNHT test: PASS
   • Pettitt test: PASS

8. ✅ Kiểm tra independence (độc lập)
   • Lag-1 correlation: 0.12 (acceptable)
   • Durbin-Watson: 1.78

9. ✅ Kiểm tra normality (phân phối chuẩn)
   • Shapiro-Wilk: p = 0.023 (non-normal) ✅
   • Suitable for extreme value analysis

🎖️ KẾT QUẢ TỔNG THỂ: 9/9 bước PASS
📊 Chất lượng dữ liệu: XUẤT SẮC
```

### 7.2 Báo Cáo Chi Tiết

**Data Quality Report:**
```
📋 BÁO CÁO CHẤT LƯỢNG DỮ LIỆU
════════════════════════════════
Trạm: Sông ABC tại XYZ
Thời kỳ: 1990-2020 (31 năm)
Thông số: Lưu lượng cực đại năm

📊 THỐNG KÊ CƠ BẢN:
   • Trung bình: 1,847 m³/s
   • Độ lệch chuẩn: 642 m³/s
   • Coefficient of variation: 0.348
   • Skewness: 1.25 (right-skewed)
   • Kurtosis: 4.89 (heavy-tailed)

📈 PHÂN BỐ THỜI GIAN:
   1990s: 10 values (Min: 1,120, Max: 2,890)
   2000s: 10 values (Min: 1,350, Max: 4,250)  
   2010s: 11 values (Min: 1,280, Max: 3,850)

🎯 ĐÁNH GIÁ CUỐI:
   • Đủ dữ liệu: ✅ (31 ≥ 30 năm khuyến nghị)
   • Chất lượng cao: ✅ (WMO-168 compliant)  
   • Phù hợp phân tích: ✅ (All checks passed)
```

---

## 8. XUẤT KẾT QUẢ VÀ BÁO CÁO

### 8.1 Xuất Biểu Đồ

**Các loại biểu đồ có thể xuất:**

1. **Frequency plot (Biểu đồ tần suất):**
   - Định dạng: PNG, PDF, SVG
   - Resolution: 300-600 DPI
   - Kích thước: A4, A3, tùy chỉnh

2. **Return period plot:**
   - Với/không confidence intervals
   - Log/linear scale
   - Multiple distributions overlay

3. **Probability paper:**
   - Gumbel paper
   - Log-normal paper  
   - Weibull paper

**Cách xuất:**
```
1. Chọn biểu đồ muốn xuất
2. Nhấn nút [📸 Xuất Hình]  
3. Cấu hình xuất:
   ┌─────────────────────────────┐
   │ 📊 Cài Đặt Xuất Biểu Đồ   │
   ├─────────────────────────────┤
   │ Định dạng: ● PNG ○ PDF     │
   │ Chất lượng: ● High ○ Med   │
   │ Kích thước: ● A4 ○ A3      │
   │ DPI: [600] ○ 300 ○ 150    │  
   │ Nền: ● Trắng ○ Trong suốt  │
   │                             │
   │ [👁️ Preview] [💾 Xuất]     │
   └─────────────────────────────┘
4. Chọn vị trí lưu file
```

### 8.2 Xuất Bảng Dữ Liệu

**Định dạng hỗ trợ:**
- **Excel (.xlsx):** Đầy đủ định dạng, biểu đồ nhúng
- **CSV:** Dữ liệu thô, dễ xử lý
- **PDF:** Báo cáo hoàn chỉnh với biểu đồ

**Nội dung bảng xuất:**
```csv
Ky_Tai_Hien,Gumbel_m3s,LogNormal_m3s,GEV_m3s,CI_Lower_95,CI_Upper_95
2,1627.3,1598.7,1635.2,1456.8,1798.5
5,2115.4,2089.3,2128.7,1921.6,2309.8
10,2437.2,2405.1,2453.6,2198.3,2676.4
25,2851.3,2813.9,2874.5,2544.7,3158.2
50,3144.7,3102.4,3172.3,2773.9,3515.8
100,3437.1,3390.2,3469.7,3003.1,3871.4
```

### 8.3 Tạo Báo Cáo Tự Động

**Template báo cáo:**

1. **Báo cáo cơ bản (10-15 trang):**
   - Tóm tắt executive
   - Mô tả dữ liệu
   - Kết quả phân tích
   - Biểu đồ chính
   - Kết luận khuyến nghị

2. **Báo cáo chi tiết (25-30 trang):**
   - Bao gồm tất cả nội dung báo cáo cơ bản
   - Phân tích chất lượng dữ liệu
   - So sánh nhiều phân phối
   - Phân tích uncertainty
   - Phụ lục kỹ thuật

3. **Báo cáo kỹ thuật (40+ trang):**
   - Full technical documentation
   - Methodology explanation
   - Statistical tests details
   - Code và parameters
   - References và standards

**Cách tạo báo cáo:**
```
📋 TẠO BÁO CÁO TỰ ĐỘNG
┌─────────────────────────────────────┐
│ Template: ● Cơ bản ○ Chi tiết      │
│                    ○ Kỹ thuật     │
│                                     │
│ Ngôn ngữ: ● Tiếng Việt            │
│           ○ English                │
│                                     │
│ Bao gồm:  ☑️ Biểu đồ màu           │
│           ☑️ Bảng số liệu          │
│           ☑️ Statistical tests     │
│           ☑️ Khuyến nghị           │
│                                     │
│ Định dạng: ● PDF ○ Word           │
│                                     │
│ [⚙️ Tùy chỉnh] [📄 Tạo Báo Cáo]   │
└─────────────────────────────────────┘
```

### 8.4 Xuất Dữ Liệu Cho Phần Mềm Khác

**Tích hợp với phần mềm khác:**

1. **HEC-RAS:** Format DSS file
2. **MIKE:** Format dfs0 file  
3. **MATLAB:** Format .mat file
4. **R:** Format .RData file
5. **Python:** Format .pickle file

**API Export:**
```python
# Xuất qua API để tích hợp với hệ thống khác
import requests

api_url = "http://localhost:8000/api/export"
data = {
    "project_id": "ABC123",
    "format": "json", 
    "include_confidence": True
}

response = requests.post(api_url, json=data)
results = response.json()
```

---

## 9. XỬ LÝ SỰ CỐ THƯỜNG GẶP

### 9.1 Lỗi Khi Nhập Dữ Liệu

**❌ "Dữ liệu không đủ để phân tích"**
```
Nguyên nhân: < 2 năm dữ liệu
Giải pháp:
1. Kiểm tra file dữ liệu có đủ dòng
2. Kiểm tra định dạng năm (yyyy)
3. Thêm dữ liệu từ nguồn khác
```

**❌ "Phát hiện giá trị không hợp lệ"**
```
Nguyên nhân: Giá trị âm, null, hoặc text
Giải pháp:
1. Mở file Excel/CSV kiểm tra
2. Xóa/sửa các cell có vấn đề  
3. Đảm bảo định dạng số (Number)
4. Upload lại file
```

**❌ "Lỗi định dạng file"**
```
Nguyên nhân: File không đúng format
Giải pháp:
1. Chuyển file sang CSV hoặc Excel
2. Đảm bảo có header row
3. Cột năm và giá trị phải có tên rõ ràng
```

### 9.2 Lỗi Khi Phân Tích

**⚠️ "Không thể ước lượng tham số phân phối"**
```
Nguyên nhân: Dữ liệu không phù hợp phân phối
Giải pháp:
1. Kiểm tra outliers và loại bỏ nếu cần
2. Thử phân phối khác (GEV thay vì Gumbel)
3. Transform dữ liệu (log transform)
4. Kiểm tra tính stationary
```

**⚠️ "Kết quả không tin cậy"**
```
Nguyên nhân: Dữ liệu quá ít hoặc chất lượng kém
Giải pháp:  
1. Cần ít nhất 10-15 năm dữ liệu
2. Kiểm tra quality control report
3. Xem xét regional frequency analysis
4. Tham khảo ý kiến chuyên gia
```

**❌ "Phân tích bị dừng"**
```  
Nguyên nhân: Lỗi tính toán hoặc hết memory
Giải pháp:
1. Restart application
2. Giảm số lượng bootstrap samples
3. Kiểm tra RAM available  
4. Liên hệ support nếu vẫn lỗi
```

### 9.3 Lỗi Hiển Thị và Xuất File

**❌ "Biểu đồ không hiển thị"**
```
Nguyên nhân: Lỗi JavaScript hoặc network
Giải pháp:
1. Refresh browser (F5)
2. Clear cache và cookies
3. Thử browser khác (Chrome, Firefox)
4. Kiểm tra ad-blocker
```

**❌ "Không thể xuất PDF"**
```
Nguyên nhân: Lỗi PDF generator
Giải pháp:
1. Thử xuất PNG trước
2. Giảm độ phân giải
3. Export từng phần riêng lẻ
4. Restart service nếu cần
```

### 9.4 Lỗi Hệ Thống

**🔴 "Service không khả dụng"**
```
Nguyên nhân: Backend server down
Giải pháp:
1. Kiểm tra: http://localhost:8000/docs  
2. Restart backend:
   docker-compose restart backend
3. Kiểm tra MongoDB running
4. Xem log file: docker-compose logs
```

**🔴 "Database connection failed"**  
```
Nguyên nhân: MongoDB không chạy
Giải pháp:
1. Start MongoDB service
2. Kiểm tra port 27017 available
3. Restart container: 
   docker-compose restart mongodb
4. Kiểm tra disk space
```

---

## 10. CÂU HỎI THƯỜNG GẶP

### 10.1 Về Dữ Liệu

**❓ Cần bao nhiêu năm dữ liệu để phân tích tin cậy?**
```
Trả lời:
• Tối thiểu: 10 năm (cho phân tích sơ bộ)
• Khuyến nghị: 30+ năm (cho thiết kế công trình)  
• Lý tưởng: 50+ năm (cho phân tích chi tiết)

Lưu ý: Với < 30 năm, cần thận trọng khi extrapolate 
ra kỳ tái hiện cao (T > 50 năm)
```

**❓ Có thể dùng dữ liệu tháng để phân tích không?**
```
Trả lời:
✅ Có, nhưng cần lưu ý:
• Seasonal analysis phức tạp hơn
• Cần kiểm tra seasonal trend
• Kết quả khác với annual maxima
• Phù hợp cho mục đích khác nhau

💡 Khuyến nghị: Annual maxima cho thiết kế đập,
   monthly data cho quản lý vận hành
```

**❓ Làm gì khi có dữ liệu thiếu?**
```
Trả lời:
1. < 10% thiếu: Interpolation hoặc bỏ qua
2. 10-30% thiếu: Regional analysis, correlation
3. > 30% thiếu: Cần tìm nguồn dữ liệu khác

Phương pháp:
• Correlation với trạm gần
• Regional regression  
• Satellite/reanalysis data
```

### 10.2 Về Phương Pháp

**❓ Khi nào dùng Gumbel, khi nào dùng GEV?**
```
Trả lời:
🎯 Gumbel (EV1):
• Đơn giản, ít tham số
• Phù hợp với hầu hết dữ liệu thủy văn
• Được quy định trong nhiều tiêu chuẩn

🎯 GEV (Generalized):  
• Linh hoạt hơn, 3 tham số
• Phù hợp với extreme data
• Tốt hơn cho bounded/unbounded phenomena

💡 Khuyến nghị: Thử cả hai, chọn theo AIC/BIC
```

**❓ Confidence interval có đáng tin không?**
```
Trả lời:
• 95% CI có nghĩa: 95% khả năng giá trị thực nằm trong khoảng này
• CI càng rộng = uncertainty càng lớn  
• Với T càng cao, CI càng rộng
• Bootstrap CI thường reliable hơn asymptotic CI

⚠️ Lưu ý: CI không tính đến model uncertainty
```

### 10.3 Về Ứng Dụng

**❓ Kết quả dùng để thiết kế công trình được không?**
```
Trả lời:
✅ Được, với điều kiện:
• Dữ liệu ≥ 30 năm chất lượng tốt
• Pass tất cả quality control checks
• Sử dụng safety factor phù hợp
• Xem xét climate change impact

🏗️ Khuyến nghị safety factors:
• Small structures: 1.2-1.5
• Major dams: 1.5-2.0  
• Critical infrastructure: 2.0+
```

**❓ Có cần xem xét biến đổi khí hậu không?**
```
Trả lời:
🌍 CÓ, đặc biệt cho:
• Thiết kế lifetime > 50 năm
• Critical/expensive infrastructure  
• Areas with high climate sensitivity

Phương pháp:
• Non-stationary frequency analysis
• Climate change adjustment factors
• Scenario-based analysis
• Regional climate model data
```

**❓ Làm sao biết kết quả đúng hay sai?**
```
Trả lời:
✅ Dấu hiệu kết quả tốt:
• Statistical tests pass (K-S, chi-square)
• Reasonable return period values
• Good fit trên probability plot
• Consistent với regional studies

❌ Dấu hiệu cần xem xét lại:
• Return periods không hợp lý
• Poor fit trên plots
• Statistical tests fail
• Quá khác biệt với khu vực lân cận
```

### 10.4 Về Kỹ Thuật

**❓ Có thể chạy trên máy yếu không?**
```
Trả lời:
💻 Yêu cầu tối thiểu:
• RAM: 4GB (8GB khuyến nghị)
• CPU: 2 cores (4 cores tốt hơn)
• Storage: 2GB free space

⚡ Tips tối ưu:
• Giảm bootstrap samples (1000 → 500)
• Tắt real-time plotting  
• Đóng browser tabs khác
• Use Docker với memory limits
```

**❓ Có thể tự động hóa không?**
```
Trả lời:
🤖 Có, qua nhiều cách:
• REST API endpoints
• Python scripts với requests  
• Scheduled batch processing
• Integration với monitoring systems

Ví dụ Python:
```python
import requests
result = requests.post('localhost:8000/api/analyze', 
                      json={'data': annual_maxima})
```

**❓ Dữ liệu có được bảo mật không?**
```
Trả lời:
🔒 Các biện pháp bảo mật:
• HTTPS encryption trong transit
• JWT authentication  
• Database encryption at rest
• Regular security updates
• Backup và disaster recovery

💡 Cho dự án nhạy cảm: Deploy on-premises
   hoặc private cloud
```

---

## PHỤ LỤC

### A. Keyboard Shortcuts
```
Ctrl + N    : Tạo dự án mới
Ctrl + O    : Mở dự án
Ctrl + S    : Lưu dự án  
Ctrl + R    : Chạy phân tích
Ctrl + E    : Xuất kết quả
F1          : Trợ giúp
F5          : Refresh
F11         : Full screen
```

### B. Supported File Formats
```
Import: .csv, .xlsx, .txt, .json, .dss
Export: .pdf, .png, .svg, .xlsx, .csv, .json
Report: .pdf, .docx, .html
```

### C. API Endpoints
```
GET  /api/projects          : Danh sách dự án
POST /api/projects          : Tạo dự án mới  
POST /api/upload            : Upload dữ liệu
POST /api/analyze           : Chạy phân tích
GET  /api/results/{id}      : Lấy kết quả
POST /api/export            : Xuất file
```

### D. Liên Hệ Hỗ Trợ
```
📧 Email: support@hydroanalysis.vn
📞 Hotline: +84 XXX XXX XXX
🌐 Website: https://hydroanalysis.vn
📚 Documentation: https://docs.hydroanalysis.vn
💬 Community: https://forum.hydroanalysis.vn
```

---

**© 2025 Hệ Thống Phân Tích Tần Suất Thủy Văn**  
**Phiên bản hướng dẫn: 2.0 - Cập nhật 24/08/2025**