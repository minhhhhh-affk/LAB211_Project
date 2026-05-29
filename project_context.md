# Ngữ cảnh Project Web Crawler — Hanzii.net

## Thông tin project

- **Chuyên ngành:** An toàn thông tin
- **Loại project:** Mini project — Web Crawling
- **Thời gian:** 11/05/2025 – 01/07/2025
- **Nhóm:** 4 thành viên
- **Trang web crawl:** hanzii.net (từ điển Hán-Việt)

---

## Yêu cầu của thầy

- Crawl dữ liệu từ hanzii.net: hán tự, hình ảnh, ngữ nghĩa, ví dụ, audio...
- Lưu vào database có cấu trúc
- Nhấn mạnh: lấy được **hình ảnh** (lazy load), **audio phát âm**, vượt **"key security"**,
  **tự đăng nhập** tài khoản pro, tìm được **secret key** mã hóa response API

---

## Môi trường làm việc

| Thành phần | Chi tiết |
|---|---|
| Hệ điều hành | Windows 11 |
| Python | 3.14.3 |
| Editor | VS Code |
| Database | MySQL Server 8.0.46 + Workbench 8.0.46 |
| Thư viện | selenium, webdriver-manager, mysql-connector-python, requests |
| Thư mục project | E:\LAB211\crawler_project |

---

## Cấu trúc thư mục

```
crawler_project/
├── config.py            ← Cấu hình database + tài khoản hanzii
├── database.py          ← Kết nối MySQL, tạo bảng, lưu dữ liệu
├── hanzii.py            ← Logic Selenium crawler
├── crawl_auto.py        ← Chế độ tự động (đọc wordlist, vòng lặp, resume)
├── recrawl_missing.py   ← Quét dọn từ bị thiếu image/popularity
├── main.py              ← File chạy chính
├── hanzii_wordlist.txt  ← ~115.106 từ (nguồn CC-CEDICT)
├── core.py              ← Scrapy engine cũ (không đụng vào)
└── sites/sites.py       ← Cấu hình Scrapy cũ (không đụng vào)
```

---

## Database

- Tên database: `crawler_db` | Bảng chính: `hanzii_words` (18 cột + id + crawled_at)
- Bảng cũ không dùng: `websites`, `items`, `crawl_logs`

### Các cột chính của `hanzii_words`

hanzi, phon_thể, pinyin, bopomofo, han_viet, hsk_level, tocfl_level, word_type,
meanings, measure, compound, synonym, antonym, image_url, audio_url,
example_audio_urls, popularity, search_count

---

## Nguồn danh sách từ (Wordlist)

- **Nguồn:** CC-CEDICT (từ điển Trung-Anh mã nguồn mở, CC BY-SA 3.0)
- **Số lượng:** 115.106 từ giản thể có chữ Hán (≈ 114k thầy đưa, overlap ~99%)
- **Các hướng đã thử và loại bỏ:**
  - `sitemap.xml` → chỉ có 3 URL chung, không liệt kê từng từ
  - Sổ tay học từ → từ học tập chọn lọc, có trùng lặp và từ ghép, không đại diện đủ
  - API danh sách từ → không tìm được endpoint public
- **Xử lý từ không tồn tại:** bot báo "không load được → bỏ qua", không crash, tự retry lần sau

---

## Lý do dùng Selenium thay Scrapy

hanzii.net là **Angular SPA** — HTML trống, data load bằng JavaScript, response API mã hóa AES.
Scrapy không render được JS. Selenium điều khiển Chrome thật để render và lấy data từ DOM.

---

## Cơ chế hoạt động

### Lượt chính (`run_auto` trong crawl_auto.py)

1. Đọc toàn bộ từ trong `hanzii_wordlist.txt`
2. Query DB lấy từ đã có → loại ra (resume)
3. Mở Chrome, tự đăng nhập pro 1 lần
4. Mỗi từ: `driver.get(.../search/word/{từ}?hl=vi)` → chờ → crawl → lưu → nghỉ 1.5s
5. Ctrl+C dừng, chạy lại tiếp tục từ chỗ dở

`main.py`:
```python
from crawl_auto import run_auto
run_auto()
```

### Lượt quét dọn (`recrawl_missing.py`)

- Tìm các từ trong DB thiếu image hoặc popularity
- Crawl lại từng từ, **UPDATE** chỉ field còn trống (giữ nguyên data đã có)
- Lặp 2-3 lần đến khi số từ thiếu không giảm nữa

---

## Tối ưu thời gian

Thay tất cả `time.sleep()` cố định bằng **chờ thông minh (polling)** — có data là chạy tiếp ngay,
không đợi thừa:

| Chỗ | Trước | Sau |
|---|---|---|
| Đầu mỗi từ | sleep(7) cứng | `wait_page_ready()` return ngay khi có nội dung |
| Lấy ảnh | sleep cứng | poll 0.25s, có src là return |
| Lấy popularity | sleep cứng | poll 0.3s + scroll-kick để trigger Intersection Observer |
| Audio | sleep(3) cứng | poll interceptor, bắt được URL là return |

Kết quả: ~17s/từ → ~8s/từ. Tổng 115k từ: ~13 ngày → ~7 ngày chạy liên tục.

**Đòn bẩy mạnh hơn (chưa triển khai):**
- Chạy song song nhiều Chrome (chia wordlist) → giảm theo số luồng
- Đường API + giải mã AES → xuống mức vài giờ, nhưng cần reverse engineer phần giải mã

---

## Các kỹ thuật bảo mật đã vượt qua

### 1. Automation Detection (navigator.webdriver)
CDP inject script `Page.addScriptToEvaluateOnNewDocument` set `navigator.webdriver = undefined`
trước khi Angular chạy.

### 2. Popup / Modal
Hàm `close_popup()`: XPath nút đóng → CSS Angular Material → phím Escape.

### 3. Lazy Loading hình ảnh (Intersection Observer)
Ảnh chỉ load khi scroll vào viewport. Bot scroll xuống đáy để trigger, rồi
`scrollIntoView({block:'center'})` đến đúng element, poll src đến khi có giá trị http.

### 4. Authorization Token
Token `33165161127683599254S0B20S319S62`. Tự gắn vào request khi đăng nhập pro qua Selenium.

### 5. Audio URL — 2 loại
| Loại | Cơ chế | Cách lấy |
|---|---|---|
| Có thu âm | Fetch file .mp3 từ audio.hanzii.net | Interceptor JS bắt lúc Angular gọi `new Audio(url)` / set `audioEl.src` |
| Không thu âm | Artyom.js + browser Speech Synthesis | Không có URL → audio_url = NULL (bình thường) |

Interceptor inject vào `Page.addScriptToEvaluateOnNewDocument` (chạy trước Angular) nên bắt được
URL dù Angular set lúc nào.

Pattern URL: từ chính `audio.hanzii.net/audios/cnvi/{id}/{word_id}.mp3`,
câu ví dụ `.../audios/e_cnvi/{id}/{example_id}.mp3`

### 6. AES Secret Key (Response Encryption)
Response từ api2.hanzii.net mã hóa AES-CBC, field `data` là base64 đã mã hóa.
Tìm bằng: F12 → Sources → Ctrl+Shift+F → `secretKeyBase64` (trong file chunk-XXXX.js).

Key: `LmOUYD1WMUlbNDVLFgdEMVEAPBV1ARpHFGQ5PAdUAgyYhB358SzZREQ1GHB1pF2VAGw0QSSQRNB1UYAgHIx0FQxw3LE1WaUcECAQLHj8fcBF5JRYuEjweL14XbEMMDCM1BxopBg==`

Thuật toán: AES-CBC, Pkcs7 padding, key 256-bit.
Ý nghĩa: lỗ hổng **hardcoded secret** — key bundle thẳng vào frontend JavaScript.

---

## Selector HTML đã phân tích

| Dữ liệu | Selector |
|---|---|
| Chờ trang load | `div#word.bg-inverse` / `div#image` / `simple-tradition` / `[id^='kind']` text |
| Chữ phồn thể | `simple-tradition` |
| Pinyin Latin | `span.txt-pinyin` (phần tử đầu, không có `txt-cn_vi`) |
| Bopomofo | `span.txt-pinyin` (phần tử thứ 2) |
| Hán Việt | `span.txt-pinyin.txt-cn_vi` |
| HSK / TOCFL | `div.tags.tag-red` / `div.tags.bg-primary` |
| Loại từ / Nghĩa | `[id^='kind'] h2` / `[id^='kind']` |
| Lượng từ / Từ ghép / Cận / Trái | `div#measure` / `div#compound` / `div#syno` / `div#anto` |
| Hình ảnh | `div#image img.w-full.thumb-extra` → fallback `div#image img` |
| Nút phát âm | `app-svg-icon[name='outline_speaker']` |
| Độ phổ biến | `div#popularity` |

---

## Giới hạn đã biết

| Vấn đề | Nguyên nhân | Xử lý |
|---|---|---|
| audio_url NULL | Hanzii dùng Artyom.js TTS, không có MP3 | Chấp nhận — đúng thực tế |
| image_url NULL | Server 500, hoặc từ không có ảnh, hoặc load chậm | recrawl_missing.py vài lần |
| popularity NULL | Từ hiếm chưa đủ lượt tra, hoặc load chậm | recrawl_missing.py vài lần |
| meanings NULL | Từ đặc biệt (tên bệnh, ký hiệu) layout khác | Số lượng ít |
| "không load được" | Mạng chậm hoặc từ không tồn tại | Tự retry lần chạy sau |

**Lưu ý kỹ thuật quan trọng:** Crawl Angular SPA bằng Selenium không thể đạt 100% trong 1 lượt
(lazy load mang tính bất định). Giải pháp là chấp nhận lượt đầu ~95% rồi dùng recrawl_missing.py
quét dọn — đây là cách xử lý đúng, không phải bug.

---

## Lệnh hay dùng

```sql
USE crawler_db;
SELECT COUNT(*) FROM hanzii_words;
SELECT hanzi, pinyin, han_viet, meanings FROM hanzii_words;

-- Đếm từ còn thiếu image/popularity
SELECT COUNT(*) FROM hanzii_words
WHERE (image_url IS NULL OR image_url='') OR (popularity IS NULL OR popularity='');

-- Xóa để crawl lại (nhớ tắt safe mode)
SET SQL_SAFE_UPDATES = 0;
DELETE FROM hanzii_words WHERE hanzi = '你好';
SET SQL_SAFE_UPDATES = 1;
```

```bash
python main.py             # lượt chính
python recrawl_missing.py  # quét dọn (lặp vài lần)
net start MySQL80          # khởi động MySQL nếu bị tắt
```
