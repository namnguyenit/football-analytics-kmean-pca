# Football Player Performance Analytics & Valuation (K-Means & PCA)

Dự án Bài tập lớn Phân tích Dữ liệu với Python (Nhóm 6 — Khoa CNTT, Đại học Phenikaa). Hệ thống xây dựng quy trình toàn diện từ **cào dữ liệu tự động (Web Scraping)**, **quản trị cơ sở dữ liệu SQLite**, **phân cụm cầu thủ (K-Means)**, **giảm chiều dữ liệu (PCA)** cho đến **mô hình định giá chuyển nhượng cầu thủ bóng đá**.

---

## 📌 Các Giai Đoạn Nghiên Cứu & Triển Khai

### Phần 1: Tiền Xử Lý & Thống Kê Mô Tả (`SOURCE_CODE/PHAN1/`)
- `Cau11.py`, `Cau12.py`: Làm sạch dữ liệu, xử lý giá trị thiếu (Missing values), tính toán các chỉ số thống kê mô tả (Mean, Median, Standard Deviation) và chuẩn hóa dữ liệu chỉ số thể lực/kỹ thuật.

### Phần 2: Thiết Kế Cơ Sở Dữ Liệu & API Tra Cứu (`SOURCE_CODE/PHAN2/`)
- `football.sqlite`: Cơ sở dữ liệu quan hệ lưu trữ thông tin câu lạc bộ, hồ sơ cầu thủ, vị trí và lịch sử thi đấu.
- `API.py` & `lookup.py`: Dịch vụ truy vấn và cung cấp API tra cứu thông tin phong độ cầu thủ theo mùa giải.

### Phần 3: Học Máy Nâng Cao, Phân Cụm & Định Giá (`SOURCE_CODE/PHAN3/`)
- `crawl.py`: Script tự động cào dữ liệu chỉ số từ các chuyên trang thống kê bóng đá quốc tế sử dụng Selenium WebDriver.
- `PCA.py`: Kỹ thuật phân tích thành phần chính (Principal Component Analysis) nhằm giảm số chiều dữ liệu từ hàng chục chỉ số kỹ thuật xuống các chiều đặc trưng then chốt mà vẫn giữ trọn phương sai dữ liệu.
- `kmean.py`: Thuật toán phân cụm K-Means phân loại cầu thủ thành các nhóm phong cách thi đấu đặc trưng (Playmakers, Defensive Anchors, Clinical Finishers, Box-to-Box Midfielders).
- `dinhgia.py`: Mô hình ước lượng giá trị chuyển nhượng dựa trên tương quan giữa độ tuổi, phong độ ghi bàn/kiến tạo và nhóm cụm kỹ thuật.
- `phongdo.py`, `trungvi.py`: Đánh giá độ ổn định và chu kỳ phong độ theo từng chặng mùa giải.

---

## 📂 Cấu trúc Thư mục

```text
football-analytics-kmean-pca/
├── BAOCAO/                  # Báo cáo toàn văn kết quả nghiên cứu và slide thuyết trình
├── SOURCE_CODE/
│   ├── PHAN1/               # Làm sạch và thống kê mô tả
│   │   ├── Cau11.py
│   │   └── Cau12.py
│   ├── PHAN2/               # Database SQLite và API tra cứu
│   │   ├── API.py
│   │   ├── football.sqlite
│   │   └── lookup.py
│   └── PHAN3/               # Cào dữ liệu, K-Means, PCA và Định giá
│       ├── crawl.py
│       ├── dinhgia.py
│       ├── kmean.py
│       ├── PCA.py
│       ├── phongdo.py
│       └── trungvi.py
└── README.md
```

---

## 🚀 Hướng dẫn Chạy Thử nghiệm

### 1. Cài đặt Môi trường
```bash
pip install numpy pandas scikit-learn matplotlib seaborn selenium
```

### 2. Chạy Phân cụm K-Means & PCA
```bash
cd SOURCE_CODE/PHAN3
python PCA.py
python kmean.py
```

### 3. Ước tính Định giá Cầu thủ
```bash
python dinhgia.py
```

---

## 👥 Nhóm Thực Hiện
- **Đơn vị**: Nhóm 6 — Lớp Phân tích Dữ liệu Python, Khoa CNTT, Trường Đại học Phenikaa
- **Thành viên tham gia**: Cao Đức Trung (`namnguyenit`) cùng các thành viên nhóm 6
