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
| Audio từ chính | URL file .mp3 phát âm |
| Audio câu ví dụ | URL các file .mp3 câu ví dụ |
| Độ phổ biến | #3694 |
| Số lần tra | 1442 |

---

## Yêu cầu

- Windows 10/11
- Python 3.x
- Google Chrome
- MySQL Server 8.0

---

## Hướng dẫn cài đặt và chạy bot

### Bước 1 — Cài Python

Vào [python.org/downloads](https://www.python.org/downloads/) → tải Python 3.x → chạy installer.

> ⚠️ Tick chọn **"Add Python to PATH"** trước khi bấm Install.

Kiểm tra sau khi cài:
```
python --version
```

---

### Bước 2 — Cài MySQL

#### 2.1 Tải MySQL Installer

Vào: https://dev.mysql.com/downloads/installer/

Tải file `mysql-installer-community-8.0.46.0.msi` → chạy.

#### 2.2 Cài MySQL Server

Trong installer: **Add** → chọn **MySQL Server 8.0.46 X64** → **Next** → **Execute**

#### 2.3 Cấu hình

- **Authentication:** chọn **Use Strong Password Encryption**
- **Root password:** đặt mật khẩu và **ghi lại**
- **Windows Service:** giữ mặc định → **Execute** → **Finish**

#### 2.4 Cài MySQL Workbench

Vào: https://downloads.mysql.com/archives/workbench/

- Product Version: **8.0.46** → tải MSI → cài → mở Workbench → kết nối Local (127.0.0.1:3306)

---

### Bước 3 — Tạo Database

Mở MySQL Workbench → Ctrl+T → dán lệnh sau → bấm ⚡:

```sql
CREATE DATABASE IF NOT EXISTS crawler_db
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;
```

---

### Bước 4 — Clone project

```bash
git clone https://github.com/minhhhhh-affk/LAB211_Project.git
cd LAB211_Project/crawler_project
```

---

### Bước 5 — Cài thư viện Python

```bash
pip install selenium webdriver-manager mysql-connector-python
```

---

### Bước 6 — Cấu hình

Mở file `config.py`, điền thông tin:

```python
DB_PASSWORD     = "mat_khau_mysql"   # ← mật khẩu MySQL của bạn
HANZII_EMAIL    = "email@gmail.com"  # ← email tài khoản hanzii.net
HANZII_PASSWORD = "mat_khau"        # ← mật khẩu tài khoản hanzii.net
```

---

### Bước 7 — Chạy bot

```bash
python main.py
```

Chrome sẽ **tự mở và tự đăng nhập** vào hanzii.net. **Không đóng cửa sổ Chrome này.**

Terminal hiển thị:
```
==========================================================
  HANZII CRAWLER — Chế độ theo dõi tìm kiếm
  Bắt đầu: 10:00:00 18/05/2026
==========================================================
  Đang đăng nhập tài khoản pro...
  ✓ Đã click nút Đăng nhập
  ✓ Tìm thấy modal đăng nhập
  ✓ Đã điền email
  ✓ Đã điền mật khẩu
  ✓ Đăng nhập thành công!

==========================================================
  ✓ Sẵn sàng! Hãy tìm kiếm từ trên web.
==========================================================
```

---

### Bước 8 — Tìm từ để crawl

1. Trên Chrome vừa mở, gõ từ tiếng Trung vào ô tìm kiếm → Enter
2. Bot tự động crawl và hiển thị kết quả trong terminal:

```
┌──────────────────────────────────────────────────────┐
  Phát hiện: 【人民】
  Phồn thể      : 人民
  Pinyin        : [ rénmín ]
  Hán Việt      : [ NHÂN DÂN ]
  HSK           : HSK 3
  Nghĩa         : Danh từ || 1. nhân dân; đồng bào...
  Hình ảnh      : https://assets.hanzii.net/...
  Audio         : https://audio.hanzii.net/audios/cnvi/...
  Audio ví dụ   : https://audio.hanzii.net/audios/e_cnvi/...
  ✓ Đã lưu 【人民】
  Thống kê: ✓1 lưu  →0 bỏ qua  ✗0 lỗi
└──────────────────────────────────────────────────────┘
```

3. Tìm từ tiếp theo, bot tự crawl tiếp
4. Nhấn **Ctrl+C** trong terminal để dừng

---

### Bước 9 — Xem dữ liệu trong MySQL Workbench

```sql
USE crawler_db;

-- Xem toàn bộ
SELECT * FROM hanzii_words;

-- Xem gọn
SELECT hanzi, pinyin, han_viet, hsk_level, meanings
FROM hanzii_words;

-- Xem audio
SELECT hanzi, audio_url, example_audio_urls
FROM hanzii_words;

-- Đếm số từ đã crawl
SELECT COUNT(*) AS tong_so_tu FROM hanzii_words;
```

---

## Hướng dẫn tìm Secret Key của hanzii.net

Hanzii.net mã hóa toàn bộ response API bằng **AES-CBC**. Secret key được hardcode trong
source code JavaScript — đây là lỗ hổng bảo mật có thể tìm thấy bằng Chrome DevTools.

### Bước 1 — Mở trang và DevTools

1. Vào `hanzii.net` → tìm bất kỳ từ nào (ví dụ `学习`)
2. Nhấn **F12** → click tab **Sources**

### Bước 2 — Tìm kiếm trong source code

Nhấn **Ctrl+Shift+F** → gõ:

```
secretKeyBase64
```

### Bước 3 — Đọc kết quả

Kết quả hiện trong các file `chunk-XXXX.js`:

```javascript
...secretKeyBase64,"LmOUYD1WMUlbNDVL..."...
```

Chuỗi base64 dài nằm trong dấu nháy kép đó chính là **AES Secret Key** — click vào dòng kết quả để xem đầy đủ và copy.

### Kết quả tìm được

| Thông tin | Giá trị |
|---|---|
| Vị trí | File `chunk-XXXX.js` (JS bundle Angular) |
| Thuật toán | AES-CBC, Pkcs7 padding, key 256-bit |
| Key (base64) | `LmOUYD1WMUlbNDVLFgdEMVEAPBV1ARpHFGQ5PAdUAgyYhB358SzZREQ1GHB1pF2VAGw0QSSQRNB1UYAgHIx0FQxw3LE1WaUcECAQLHj8fcBF5JRYuEjweL14XbEMMDCM1BxopBg==` |
| Dùng để | Mã hóa toàn bộ response từ `api2.hanzii.net` |

### Ý nghĩa bảo mật

Đây là lỗ hổng **hardcoded secret** — một trong những lỗi bảo mật phổ biến nhất:

- Secret key được bundle thẳng vào JavaScript gửi về trình duyệt
- Bất kỳ ai có DevTools đều có thể tìm thấy trong vài phút
- Kẻ tấn công có thể dùng key này để giải mã toàn bộ API response

**Khuyến nghị:** Secret key không bao giờ được đặt ở frontend — phải xử lý hoàn toàn ở server-side.

---

## Cấu trúc thư mục

```
crawler_project/
├── config.py      ← Cấu hình database + tài khoản hanzii
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

**`pip` không nhận:**
```bash
python -m pip install selenium webdriver-manager mysql-connector-python
```

**MySQL không kết nối được:**
- Mở `services.msc` → tìm **MySQL80** → Start
- Kiểm tra lại mật khẩu trong `config.py`

**MySQL bị tắt sau khi restart máy:**
```bash
net start MySQL80
```

**Chrome không mở được:**
- Kiểm tra Chrome đã cài chưa
- Chạy lại `pip install webdriver-manager`

**Đăng nhập thất bại:**
- Kiểm tra `HANZII_EMAIL` và `HANZII_PASSWORD` trong `config.py`
- Thử đăng nhập thủ công trên trình duyệt để xác nhận thông tin đúng

**Dữ liệu bị thiếu (pinyin, nghĩa trống):**
- Trang load chậm → mở `hanzii.py` → tìm `time.sleep(4)` → đổi thành `time.sleep(6)`

**Muốn crawl lại 1 từ đã có:**
```sql
USE crawler_db;
DELETE FROM hanzii_words WHERE hanzi = '你好';
```

**Muốn xóa toàn bộ và crawl lại từ đầu:**
```sql
USE crawler_db;
DROP TABLE IF EXISTS hanzii_words;
```

---

## Lưu ý

- Không đóng cửa sổ Chrome khi đang dùng
- Nhấn **Ctrl+C** trong terminal để dừng bất cứ lúc nào — dữ liệu đã lưu không bị mất
- Những từ đã crawl sẽ tự động bỏ qua khi tìm lại
- Bot chỉ crawl khi URL chuyển sang trang từ (`/search/word/...`)
- Mỗi lần chạy bot sẽ **đăng nhập lại** từ đầu
