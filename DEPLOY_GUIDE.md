# HƯỚNG DẪN DEPLOY CHI TIẾT

## 📦 Bước 1: Chuẩn Bị File

Bạn đã có đầy đủ các file sau:
- ✅ app.py (file chính)
- ✅ requirements.txt (các thư viện)
- ✅ README.md (tài liệu)
- ✅ .gitignore (bỏ qua file không cần)
- ✅ .streamlit/config.toml (cấu hình theme)

## 🚀 Bước 2: Upload Lên GitHub

### Cách 1: Sử dụng GitHub Desktop (Dễ nhất)

1. Tải và cài đặt GitHub Desktop: https://desktop.github.com/
2. Đăng nhập GitHub
3. Click "File" → "New Repository"
4. Điền thông tin:
   - Name: `bank-loan-analysis` (hoặc tên bạn muốn)
   - Description: `Hệ thống thẩm định phương án kinh doanh`
   - Local path: Chọn thư mục chứa các file
5. Click "Create Repository"
6. Copy tất cả file vào thư mục đó
7. Commit với message: "Initial commit"
8. Click "Publish repository" → Chọn "Public" → Publish

### Cách 2: Sử dụng Git Command Line

```bash
# Bước 1: Tạo repository trên GitHub.com
# - Đăng nhập GitHub
# - Click "+" → "New repository"
# - Điền tên repository
# - Chọn "Public"
# - Click "Create repository"

# Bước 2: Trong thư mục chứa các file, chạy lệnh:
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/YOUR-REPO-NAME.git
git push -u origin main
```

### Cách 3: Upload Trực Tiếp Trên GitHub.com

1. Đăng nhập GitHub
2. Click "+" → "New repository"
3. Điền tên repository → "Create repository"
4. Click "uploading an existing file"
5. Kéo thả tất cả các file vào
6. Click "Commit changes"

## ☁️ Bước 3: Deploy Trên Streamlit Cloud

### 3.1. Tạo Tài Khoản

1. Truy cập: https://streamlit.io/cloud
2. Click "Sign up"
3. Chọn "Continue with GitHub"
4. Cho phép Streamlit truy cập GitHub

### 3.2. Deploy App

1. Click "New app"
2. Điền thông tin:
   - **Repository**: Chọn repo bạn vừa tạo
   - **Branch**: main
   - **Main file path**: app.py
   - **App URL**: Chọn tên URL cho app
3. Click "Deploy!"

### 3.3. Đợi Deploy Hoàn Tất

- Streamlit sẽ tự động cài đặt các thư viện từ requirements.txt
- Quá trình này mất khoảng 2-3 phút
- Khi thấy "Your app is live!" là hoàn tất

## 🔑 Bước 4: Lấy Gemini API Key

1. Truy cập: https://aistudio.google.com/app/apikey
2. Đăng nhập bằng Google Account
3. Click "Create API Key"
4. Chọn "Create API key in new project"
5. Copy API Key (dạng: AIzaSy...)
6. LƯU Ý: Không chia sẻ API Key cho người khác!

## 💻 Bước 5: Sử Dụng App

1. Mở link app của bạn (ví dụ: https://your-app.streamlit.app)
2. Ở sidebar bên trái:
   - Paste Gemini API Key vào ô "Nhập Gemini API Key"
   - Upload file PASDV.docx
   - Click "Trích xuất dữ liệu"
3. Xem và chỉnh sửa thông tin ở các tab
4. Sử dụng các tính năng:
   - Xem chỉ tiêu tài chính
   - Xem biểu đồ
   - Phân tích bằng AI
   - Chat với AI
   - Xuất báo cáo

## 🔄 Cập Nhật App

Khi bạn muốn thay đổi code:

### Cách 1: GitHub Desktop
1. Chỉnh sửa file app.py
2. Mở GitHub Desktop
3. Viết commit message
4. Click "Commit to main"
5. Click "Push origin"
6. Streamlit tự động deploy lại sau 1-2 phút

### Cách 2: Git Command Line
```bash
git add .
git commit -m "Update feature"
git push
```

### Cách 3: Chỉnh sửa trực tiếp trên GitHub
1. Vào repository trên GitHub
2. Click vào file cần sửa
3. Click biểu tượng bút chì (Edit)
4. Chỉnh sửa
5. Click "Commit changes"

## 🐛 Xử Lý Lỗi Thường Gặp

### Lỗi: "ModuleNotFoundError"
**Nguyên nhân**: Thiếu thư viện trong requirements.txt
**Giải pháp**: Thêm thư viện vào requirements.txt và push lại

### Lỗi: "API Key không hợp lệ"
**Nguyên nhân**: API Key sai hoặc hết hạn
**Giải pháp**: Tạo API Key mới từ Google AI Studio

### Lỗi: "File upload failed"
**Nguyên nhân**: File quá lớn hoặc sai định dạng
**Giải pháp**: Kiểm tra file phải là .docx và < 200MB

### App chạy chậm
**Nguyên nhân**: Streamlit Cloud free tier giới hạn tài nguyên
**Giải pháp**: 
- Tối ưu code
- Hoặc nâng cấp lên Streamlit Cloud Pro

## 📊 Giới Hạn Streamlit Cloud (Free Tier)

- ✅ Apps không giới hạn
- ✅ 1 GB RAM
- ✅ 1 CPU
- ✅ Băng thông không giới hạn
- ⚠️ App sẽ sleep sau 7 ngày không sử dụng
- ⚠️ Giới hạn thời gian chạy liên tục

## 🎯 Tips & Tricks

### 1. Tăng Tốc App
- Cache các hàm tính toán nặng với `@st.cache_data`
- Giảm số lượng API calls không cần thiết
- Tối ưu code xử lý file

### 2. Bảo Mật
- KHÔNG hardcode API Key trong code
- Luôn nhập API Key qua sidebar
- Không commit file chứa thông tin nhạy cảm

### 3. Tùy Chỉnh Giao Diện
- Chỉnh sửa file `.streamlit/config.toml`
- Thay đổi màu sắc, font chữ theo ý muốn
- Thêm CSS tùy chỉnh trong `st.markdown()`

### 4. Chia Sẻ App
- Copy link app và chia sẻ
- App public, ai cũng có thể truy cập
- Nếu muốn private, nâng cấp lên paid plan

## 📞 Cần Trợ Giúp?

### Tài liệu tham khảo:
- Streamlit Docs: https://docs.streamlit.io/
- Gemini API Docs: https://ai.google.dev/docs
- GitHub Guides: https://guides.github.com/

### Community:
- Streamlit Forum: https://discuss.streamlit.io/
- GitHub Issues: Tạo issue trên repo của bạn

## ✅ Checklist Trước Khi Deploy

- [ ] Đã test app chạy tốt trên máy local
- [ ] File requirements.txt đầy đủ
- [ ] Đã tạo repository GitHub
- [ ] Đã push code lên GitHub
- [ ] Đã tạo tài khoản Streamlit Cloud
- [ ] Đã lấy Gemini API Key
- [ ] Đã test file PASDV.docx mẫu

## 🎉 Chúc Mừng!

Bạn đã hoàn thành việc deploy app lên Streamlit Cloud!
App của bạn đã sẵn sàng sử dụng tại: https://your-app.streamlit.app

---

**Phát triển bởi**: Claude AI
**Phiên bản**: 1.0
**Ngày cập nhật**: 2025
