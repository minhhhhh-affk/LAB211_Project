# Hanzii Crawler 🐼

Crawl dữ liệu từ điển Hán-Việt từ [hanzii.net](https://hanzii.net) và lưu vào MySQL.

---

## Dữ liệu crawl được

| Cột | Ví dụ |
|---|---|
| Chữ Hán | 人民 |
| Chữ phồn thể | 人民 |
| Pinyin | [ rénmín ] |
| Bopomofo | [ ㄖㄣˊㄇㄧㄣˊ ] |
| Hán Việt | [ NHÂN DÂN ] |
| HSK | HSK 3 |
| TOCFL | TOCFL 3 |
| Loại từ | Danh từ |
| Nghĩa | nhân dân; đồng bào |
| Lượng từ | 群, 批, 个, 国 |
| Từ ghép | 人民币, 人民网... |
| Từ cận nghĩa | 群众, 黎民, 百姓 |
| Từ trái nghĩa | 故人 |
| Hình ảnh | URL ảnh minh họa |
| Độ phổ biến | #3694 |
| Số lần tra | 1442 |

---

## Yêu cầu cài đặt

- Windows 10/11
- Python 3.x
- Google Chrome
- MySQL Server 8.0

---

## Bước 1 — Cài Python

Vào [python.org/downloads](https://www.python.org/downloads/) → tải Python 3.x → chạy installer.

> ⚠️ Quan trọng: Tick chọn **"Add Python to PATH"** trước khi bấm Install.

Kiểm tra sau khi cài:
```
python --version
```

---

## Bước 2 — Cài MySQL

### 2.1 Tải MySQL Installer
Vào: https://dev.mysql.com/downloads/installer/

Tải file `mysql-installer-community-8.0.46.0.msi` (~565MB) → chạy.

### 2.2 Cài MySQL Server
Trong installer:
- Click **Add** → chọn **MySQL Server 8.0.46 X64** → click mũi tên → **Next → Execute**

### 2.3 Cấu hình
- **Authentication:** chọn **Use Strong Password Encryption**
- **Root password:** đặt mật khẩu, **ghi lại cẩn thận**
- **Windows Service:** giữ mặc định → **Execute → Finish**

### 2.4 Cài MySQL Workbench
Vào: https://downloads.mysql.com/archives/workbench/

- Product Version: **8.0.46**
- Tải MSI → cài → mở Workbench → kết nối Local (127.0.0.1:3306, user: root)

---

## Bước 3 — Tạo Database

Mở MySQL Workbench → kết nối Local → Ctrl+T → dán lệnh sau → bấm ⚡:

```sql
CREATE DATABASE IF NOT EXISTS crawler_db
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;
```

---

## Bước 4 — Clone project

```
git clone https://github.com/minhhhhh-affk/LAB211_Project.git
cd LAB211_Project/crawler_project
```

---

## Bước 5 — Cài thư viện Python

Mở CMD trong thư mục project, chạy:

```
pip install selenium webdriver-manager mysql-connector-python
```

Chờ đến khi thấy **"Successfully installed..."**

---

## Bước 6 — Cấu hình mật khẩu MySQL

Mở file `config.py`, sửa dòng này:

```python
DB_PASSWORD = "@123@123a"   # ← đổi thành mật khẩu MySQL của bạn
```

---

## Bước 7 — Chạy bot

```
python main.py
```

Chrome sẽ **tự mở và vào thẳng hanzii.net**. **Không đóng cửa sổ Chrome này.**

---

## Bước 8 — Tìm từ để crawl

1. Trên Chrome vừa mở (đã ở sẵn hanzii.net), gõ từ tiếng Trung bất kỳ vào ô tìm kiếm → Enter
2. Bot tự động phát hiện và crawl dữ liệu của từ đó
3. Kết quả hiển thị ngay trong terminal

```
┌──────────────────────────────────────────────────────┐
  Phát hiện: 【人民】
  Phồn thể  : 人民
  Pinyin    : [ rénmín ]
  Hán Việt  : [ NHÂN DÂN ]
  HSK       : HSK 3
  ...
  ✓ Đã lưu 【人民】
  Thống kê: ✓1 lưu  →0 bỏ qua  ✗0 lỗi
└──────────────────────────────────────────────────────┘
```

5. Tìm từ tiếp theo, bot tự crawl tiếp
6. Nhấn **Ctrl+C** trong terminal để dừng

---

## Bước 9 — Xem dữ liệu trong MySQL Workbench

Mở Workbench → kết nối Local → Ctrl+T → chạy:

```sql
USE crawler_db;

-- Xem toàn bộ
SELECT * FROM hanzii_words;

-- Xem gọn
SELECT hanzi, pinyin, han_viet, hsk_level, meanings
FROM hanzii_words;

-- Đếm số từ đã crawl
SELECT COUNT(*) AS tong_so_tu FROM hanzii_words;
```

---

## Cấu trúc thư mục

```
crawler_project/
├── config.py      ← Cấu hình database
├── database.py    ← Kết nối MySQL, tạo bảng, lưu dữ liệu
├── hanzii.py      ← Toàn bộ logic crawler (Selenium)
├── main.py        ← File chạy chính
├── core.py        ← Scrapy engine (không đụng vào)
└── sites/
    ├── __init__.py
    └── sites.py   ← Cấu hình các site Scrapy (không đụng vào)
```

---

## Xử lý sự cố

**Lỗi `pip` không nhận:**
```
python -m pip install selenium webdriver-manager mysql-connector-python
```

**MySQL không kết nối được:**
- Mở `services.msc` → tìm **MySQL80** → Start
- Kiểm tra lại mật khẩu trong `config.py`

**MySQL bị tắt sau khi restart máy:**
```
net start MySQL80
```
Chạy lệnh này trong CMD quyền Admin.

**Chrome không mở được:**
- Kiểm tra Chrome đã cài chưa
- Chạy lại `pip install webdriver-manager` để cập nhật ChromeDriver

**Dữ liệu bị thiếu (pinyin, nghĩa trống):**
- Trang load chậm → mở `hanzii.py` → tìm `time.sleep(4)` → đổi thành `time.sleep(6)`

**Từ bị NULL toàn bộ (ví dụ từ hán tự / bộ thủ):**
- Đây là từ có cấu trúc trang khác (không có `div#word`) — bot đã tự xử lý, thử tìm lại từ đó là được.

**Muốn crawl lại 1 từ đã có:**
```sql
USE crawler_db;
DELETE FROM hanzii_words WHERE hanzi = '你好';
```
Rồi tìm lại từ đó trên web.

**Muốn xóa toàn bộ và crawl lại từ đầu:**
```sql
USE crawler_db;
DROP TABLE IF EXISTS hanzii_words;
```
Rồi chạy lại `python main.py`

---

## Lưu ý

- Không đóng cửa sổ Chrome khi đang dùng
- Có thể bấm **Ctrl+C** trong terminal để dừng bất cứ lúc nào — dữ liệu đã lưu sẽ không bị mất
- Những từ đã crawl sẽ tự động bỏ qua khi tìm lại
- Bot chỉ crawl khi URL chuyển sang trang từ (`/search/word/...`) — lướt trang bình thường không ảnh hưởng gì
