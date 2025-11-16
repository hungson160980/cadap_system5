# 🏦 Hệ Thống Thẩm Định Phương Án Kinh Doanh

Ứng dụng web phân tích và thẩm định phương án vay vốn ngân hàng sử dụng AI Gemini.

## ✨ Tính Năng

- 📤 **Upload & Trích xuất**: Upload file PASDV.docx và tự động trích xuất thông tin
- ✏️ **Chỉnh sửa động**: Điều chỉnh các thông số với nút +/- và tự động tính toán lại
- 📊 **Phân tích tài chính**: Tính toán đầy đủ các chỉ tiêu tài chính, DSCR, LTV
- 📈 **Biểu đồ trực quan**: Hiển thị biểu đồ dư nợ, thu chi, cơ cấu thanh toán
- 🤖 **Phân tích AI**: Sử dụng Gemini AI để phân tích chuyên sâu
- 💬 **Chatbox AI**: Hỏi đáp với AI về phương án vay vốn
- 📥 **Xuất báo cáo**: Xuất Excel (kế hoạch trả nợ) và Word (báo cáo thẩm định)

## 🚀 Hướng Dẫn Deploy Trên Streamlit Cloud

### 1. Chuẩn Bị

- Tài khoản GitHub
- Tài khoản Streamlit Cloud (https://streamlit.io/cloud)
- Gemini API Key (https://aistudio.google.com/app/apikey)

### 2. Upload Lên GitHub

```bash
# Tạo repository mới trên GitHub
# Clone repository về máy
git clone https://github.com/your-username/your-repo-name.git
cd your-repo-name

# Copy các file vào thư mục
# - app.py
# - requirements.txt
# - README.md

# Commit và push
git add .
git commit -m "Initial commit"
git push origin main
```

### 3. Deploy Trên Streamlit Cloud

1. Truy cập: https://share.streamlit.io/
2. Click "New app"
3. Chọn repository GitHub của bạn
4. Branch: `main`
5. Main file path: `app.py`
6. Click "Deploy"

### 4. Sử Dụng

1. Mở ứng dụng đã deploy
2. Nhập Gemini API Key ở sidebar
3. Upload file PASDV.docx
4. Click "Trích xuất dữ liệu"
5. Xem và chỉnh sửa thông tin
6. Phân tích và xuất báo cáo

## 📋 Cấu Trúc File PASDV.docx

File phải chứa các thông tin:

### Thông tin khách hàng
- Họ và tên
- CCCD/CMND
- Địa chỉ
- Số điện thoại
- Email

### Thông tin tài chính
- Tổng nhu cầu vốn
- Vốn đối ứng
- Số tiền vay
- Lãi suất
- Thời hạn vay
- Mục đích vay
- Thu nhập hàng tháng
- Chi phí hàng tháng

### Tài sản đảm bảo
- Loại tài sản
- Giá trị
- Địa chỉ
- Diện tích

## 🔧 Cài Đặt Cục Bộ

```bash
# Clone repository
git clone https://github.com/your-username/your-repo-name.git
cd your-repo-name

# Cài đặt thư viện
pip install -r requirements.txt

# Chạy ứng dụng
streamlit run app.py
```

## 📊 Các Tab Chính

1. **📋 Thông Tin KH**: Thông tin định danh khách hàng
2. **💰 Thông Tin Tài Chính**: Thông tin vay vốn và thu chi
3. **🏠 Tài Sản Đảm Bảo**: Chi tiết tài sản đảm bảo
4. **📊 Chỉ Tiêu & Kế Hoạch**: Các chỉ tiêu tài chính và bảng trả nợ
5. **📈 Biểu Đồ**: Trực quan hóa dữ liệu
6. **🤖 Phân Tích AI**: Phân tích từ file và chỉ số
7. **💬 Chatbox AI**: Hỏi đáp với AI
8. **📥 Xuất Dữ Liệu**: Xuất Excel và Word

## 🎯 Các Chỉ Tiêu Tính Toán

- **Trả nợ gốc hàng tháng**: Dư nợ / Số tháng
- **Trả lãi**: Dư nợ × Lãi suất tháng
- **Thu nhập ròng**: Thu nhập - Chi phí
- **Tỷ lệ trả nợ/Thu nhập**: (Trả nợ / Thu nhập) × 100%
- **DSCR**: Thu nhập ròng / Trả nợ
- **LTV**: Số tiền vay / Giá trị tài sản × 100%

## 💡 Lưu Ý

- Tất cả số liệu hiển thị phân cách hàng nghìn bằng dấu "."
- Dữ liệu thay đổi sẽ tự động tính toán lại
- Cần API Key Gemini để sử dụng tính năng AI
- File upload phải đúng định dạng .docx

## 🛠️ Công Nghệ Sử Dụng

- **Streamlit**: Framework web app
- **Pandas**: Xử lý dữ liệu
- **Plotly**: Biểu đồ tương tác
- **python-docx**: Đọc/ghi file Word
- **openpyxl**: Xuất file Excel
- **Google Gemini AI**: Phân tích thông minh

## 📞 Hỗ Trợ

Nếu gặp vấn đề, vui lòng tạo issue trên GitHub.

## 📄 License

MIT License

---

**Phát triển bởi**: Claude AI
**Version**: 1.0
**Cập nhật**: 2025
