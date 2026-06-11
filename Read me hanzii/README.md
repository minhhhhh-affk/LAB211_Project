# Hanzii Crawler 🐼

Crawl dữ liệu từ điển Hán-Việt từ [hanzii.net](https://hanzii.net) và lưu vào MySQL.
Tự động crawl toàn bộ wordlist ~115k từ, có resume và quét dọn (re-crawl) các từ bị thiếu.

---

## Dữ liệu crawl được (18 cột)

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
| Hình ảnh | URL ảnh minh họa (assets.hanzii.net hoặc th.bing.com) |
| Audio từ chính | URL file .mp3 phát âm |
| Audio câu ví dụ | URL các file .mp3 câu ví dụ |
| Độ phổ biến | #3694 |
| Số lần tra | 1442 |

> **Lưu ý quan trọng:** Một số từ có audio_url / image_url / popularity = NULL.
> Đây là **bình thường**, không phải lỗi crawler:
> - audio NULL: hanzii dùng browser TTS (Artyom.js) thay vì file MP3 cho từ đó
> - image NULL: server hanzii trả 500 cho ảnh đó, hoặc từ không có ảnh
> - popularity NULL: từ hiếm, chưa đủ lượt tra để có thống kê

---

## Cấu trúc thư mục

```
crawler_project/
├── config.py            ← Cấu hình database + tài khoản hanzii
├── database.py          ← Kết nối MySQL, tạo bảng, lưu dữ liệu
├── hanzii.py            ← Logic Selenium crawler (chờ thông minh, bắt audio/ảnh)
├── crawl_auto.py        ← Chế độ tự động (đọc wordlist, vòng lặp, resume)
├── recrawl_missing.py   ← Quét dọn: crawl lại các từ bị thiếu image/popularity
├── main.py              ← File chạy chính
├── hanzii_wordlist.txt  ← Danh sách ~115.106 từ (nguồn CC-CEDICT)
├── core.py              ← Scrapy engine cũ (không đụng vào)
└── sites/
    ├── __init__.py
    └── sites.py         ← Cấu hình site Scrapy cũ (không đụng vào)
```

---

## Yêu cầu

- Windows 10/11
- Python 3.x
- Google Chrome
- MySQL Server 8.0

---

## Cài đặt

### Bước 1 — Cài Python

[python.org/downloads](https://www.python.org/downloads/) → tải Python 3.x → chạy installer.

> ⚠️ Tick **"Add Python to PATH"** trước khi Install.

```
python --version
```

### Bước 2 — Cài MySQL

Tải MySQL Installer từ https://dev.mysql.com/downloads/installer/ → cài **MySQL Server 8.0.46**
+ **MySQL Workbench 8.0.46**. Đặt và ghi lại root password.

### Bước 3 — Tạo Database

Mở MySQL Workbench → Ctrl+T → chạy:

```sql
CREATE DATABASE IF NOT EXISTS crawler_db
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;
```

### Bước 4 — Clone project

```bash
git clone https://github.com/minhhhhh-affk/LAB211_Project.git
cd LAB211_Project/crawler_project
```

### Bước 5 — Cài thư viện

```bash
pip install selenium webdriver-manager mysql-connector-python requests
```

### Bước 6 — Cấu hình

Mở `config.py`, điền:

```python
DB_PASSWORD     = "mat_khau_mysql"
HANZII_EMAIL    = "email@gmail.com"
HANZII_PASSWORD = "mat_khau_hanzii"
```

---

## Cách chạy

### Lượt chính — crawl toàn bộ

`main.py`:
```python
from crawl_auto import run_auto
run_auto()
```

```bash
python main.py
```

Chrome tự mở, tự đăng nhập, tự crawl toàn bộ wordlist. **Không đụng vào cửa sổ Chrome.**

Terminal hiển thị:
```
[1/115056] [一]  LUU OK   (ok:1 skip:0 loi:0)
[2/115056] [一一] LUU OK   (ok:2 skip:0 loi:0)
[3/115056] [游戏] DA CO    (ok:2 skip:1 loi:0)
```

- **Tốc độ:** ~8 giây/từ (đã tối ưu bằng chờ thông minh thay sleep cố định)
- **Resume:** chạy lại tự bỏ qua từ đã có, crawl tiếp từ còn thiếu
- **Dừng:** Ctrl+C bất cứ lúc nào — dữ liệu đã lưu không mất

### Lượt quét dọn — bổ sung từ bị thiếu

Sau khi lượt chính xong, một số từ có thể thiếu image/popularity do Angular load chậm.
Chạy script quét dọn để crawl lại riêng chúng:

```bash
python recrawl_missing.py
```

Script tìm các từ thiếu trong DB, crawl lại, **chỉ điền field còn trống** (giữ nguyên
dữ liệu đã có). **Lặp lại 2-3 lần** đến khi số từ thiếu không giảm nữa — số còn lại là
những từ thật sự không có data trên hanzii.

---

## Xem dữ liệu

```sql
USE crawler_db;

-- Đếm số từ đã crawl
SELECT COUNT(*) AS tong_so_tu FROM hanzii_words;

-- Xem gọn
SELECT hanzi, pinyin, han_viet, hsk_level, meanings FROM hanzii_words LIMIT 20;

-- Xem audio và ảnh
SELECT hanzi, audio_url, example_audio_urls, image_url FROM hanzii_words LIMIT 20;

-- Đếm số từ còn thiếu image/popularity
SELECT COUNT(*) FROM hanzii_words
WHERE (image_url IS NULL OR image_url = '')
   OR (popularity IS NULL OR popularity = '');
```

---

## Xử lý sự cố

**`pip` không nhận:**
```bash
python -m pip install selenium webdriver-manager mysql-connector-python requests
```

**MySQL không kết nối / bị tắt:**
```bash
net start MySQL80
```
Hoặc mở `services.msc` → MySQL80 → Start. Kiểm tra mật khẩu trong `config.py`.

**Lỗi SQL 1175 (safe update mode) khi DELETE:**
```sql
SET SQL_SAFE_UPDATES = 0;
-- câu lệnh delete của bạn
SET SQL_SAFE_UPDATES = 1;
```

**Đăng nhập thất bại:**
Kiểm tra `HANZII_EMAIL` / `HANZII_PASSWORD` trong `config.py`.

**Nhiều từ thiếu image/popularity:**
Chạy `python recrawl_missing.py` vài lần. Đây là cách xử lý chính thức,
không cần sửa code.

**Muốn crawl lại 1 từ:**
```sql
SET SQL_SAFE_UPDATES = 0;
DELETE FROM hanzii_words WHERE hanzi = '你好';
SET SQL_SAFE_UPDATES = 1;
```

---

## Tìm Secret Key của hanzii.net (phần bảo mật)

Hanzii mã hóa toàn bộ response API bằng **AES-CBC**, secret key hardcode trong JavaScript.

**Cách tìm:** Vào hanzii.net → F12 → Sources → Ctrl+Shift+F → gõ `secretKeyBase64`.
Kết quả nằm trong file `chunk-XXXX.js`.

| Thông tin | Giá trị |
|---|---|
| Thuật toán | AES-CBC, Pkcs7 padding, key 256-bit |
| Key (base64) | `LmOUYD1WMUlbNDVLFgdEMVEAPBV1ARpHFGQ5PAdUAgyYhB358SzZREQ1GHB1pF2VAGw0QSSQRNB1UYAgHIx0FQxw3LE1WaUcECAQLHj8fcBF5JRYuEjweL14XbEMMDCM1BxopBg==` |
| Authorization token | `33165161127683599254S0B20S319S62` |

**Ý nghĩa bảo mật:** Đây là lỗ hổng **hardcoded secret** — key bundle thẳng vào
JavaScript frontend, ai có DevTools đều tìm được. Khuyến nghị: xử lý hoàn toàn ở server-side.
