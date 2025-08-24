# 🗺️ Tích Hợp Bản Đồ Nâng Cao với Mapbox

## 📋 Tổng Quan

Hệ thống đã được tích hợp tính năng **bản đồ nâng cao** với đa lớp bản đồ (OpenStreetMap + Mapbox Satellite) và hiển thị các trạm đo thủy văn với icon tùy chỉnh.

## ✨ Tính Năng Mới

### 🎯 **Bản Đồ Nâng Cao**

- **Đa lớp bản đồ**: Chuyển đổi giữa OpenStreetMap, Mapbox Satellite, Mapbox Streets
- **Icon trạm thông minh**: Màu sắc thay đổi theo mực nước và trạng thái trạm
- **Popup thông tin chi tiết**: Hiển thị đầy đủ thông tin trạm khi click
- **Legend tương tác**: Chú thích màu sắc cho từng loại trạm
- **Responsive design**: Tương thích với mọi thiết bị

### 🎨 **Màu Sắc Icon Trạm**

- 🟢 **Xanh lá**: Mực nước thấp (< 0.2m)
- 🟡 **Vàng**: Mực nước trung bình (0.2-0.5m)  
- 🔴 **Đỏ**: Mực nước cao (> 0.5m)
- ⚫ **Xám**: Trạm không hoạt động

## 🚀 Cách Sử Dụng

### 1. **Truy Cập Bản Đồ Nâng Cao**

```
Sidebar → Dữ liệu Realtime → Bản đồ nâng cao
```

### 2. **Cấu Hình Mapbox Token**

1. Click vào card "Cấu hình Mapbox Token"
2. Click "Thêm Token" hoặc "Cập nhật Token"
3. Làm theo hướng dẫn để lấy token từ Mapbox
4. Nhập token và lưu

### 3. **Lấy Mapbox Access Token**

1. Truy cập [Mapbox Account](https://account.mapbox.com/)
2. Đăng nhập hoặc tạo tài khoản mới
3. Vào phần "Access Tokens"
4. Tạo token mới hoặc copy token hiện có
5. Token phải bắt đầu bằng "pk."

### 4. **Sử Dụng Bản Đồ**

- **Chuyển đổi lớp bản đồ**: Sử dụng control ở góc trên bên phải
- **Xem thông tin trạm**: Click vào icon trạm
- **Chọn trạm**: Click để xem thông tin chi tiết bên dưới

## 🔧 Cấu Trúc Code

### **Component Chính**

- `AdvancedStationMap.js`: Component bản đồ nâng cao
- `MapboxTokenInput.js`: Component nhập token
- `advancedStationMap.css`: Styling cho bản đồ

### **Tích Hợp**

- Đã thêm vào `App.js` với route `ban-do-nang-cao`
- Đã thêm vào `sideBar.js` với icon và label phù hợp
- Sử dụng localStorage để lưu token

## 📊 Dữ Liệu Hiển Thị

### **Thông Tin Trạm**

- ID trạm và tên
- Vị trí (latitude, longitude)
- Trạng thái hoạt động
- Mực nước hiện tại
- Thời gian cập nhật cuối
- Tổng số đo
- Thống kê (trung bình, min, max)

### **Nguồn Dữ Liệu**

- API: `GET /realtime/stations`
- Backend: `backend/app/routers/realtime_router.py`
- Database: MongoDB collection `hydro_db.realtime_depth`

## 🎯 Lợi Ích

### **Cho Người Dùng**

- Trải nghiệm bản đồ chuyên nghiệp
- Thông tin trạm trực quan
- Dễ dàng theo dõi mực nước
- Giao diện thân thiện

### **Cho Hệ Thống**

- Tích hợp đa lớp bản đồ
- Icon thông minh theo dữ liệu
- Responsive và scalable
- Dễ bảo trì và mở rộng

## 🔮 Tính Năng Tương Lai

### **Có Thể Phát Triển Thêm**

- [ ] Animation cho icon trạm
- [ ] Heatmap mực nước
- [ ] Timeline playback
- [ ] Export bản đồ
- [ ] Tích hợp thêm bản đồ khác (Google Maps, Bing Maps)

## 🛠️ Troubleshooting

### **Lỗi Thường Gặp**

1. **Token không hợp lệ**: Kiểm tra format token (phải bắt đầu bằng "pk.")
2. **Bản đồ không load**: Kiểm tra kết nối internet và token
3. **Trạm không hiển thị**: Kiểm tra API `/realtime/stations`

### **Debug**

- Mở Developer Tools (F12)
- Kiểm tra Console để xem lỗi
- Kiểm tra Network tab để xem API calls

## 📝 Ghi Chú

- Token được lưu trong localStorage của trình duyệt
- Bản đồ sử dụng Leaflet + React-Leaflet
- Icon trạm được tạo bằng L.divIcon
- Responsive design cho mobile và desktop

---

**🎉 Chúc bạn sử dụng tính năng bản đồ nâng cao hiệu quả!**
