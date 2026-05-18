# Ngữ cảnh Project Web Crawler — Hanzii.net

## Thông tin project

- **Chuyên ngành:** An toàn thông tin
- **Loại project:** Mini project — Web Crawling
- **Thời gian:** 11/05/2025 – 01/07/2025
- **Nhóm:** 4 thành viên
- **Trang web crawl:** hanzii.net (từ điển Hán-Việt)

---

## Yêu cầu của thầy

- Crawl dữ liệu từ hanzii.net
- Lấy được các từ tiếng Trung cùng thông tin đi kèm: hán tự, hình ảnh, ngữ nghĩa, ví dụ, audio...
- Lưu vào database có cấu trúc
- Thầy đặc biệt nhấn mạnh:
  - Phải lấy được **hình ảnh** (lazy loading — khó nhất)
  - Phải lấy được **audio phát âm** (intercept network request)
  - Phải vượt qua được **"key security"** của trang
  - Phải **tự đăng nhập** bằng tài khoản pro được cấp
  - Phải tìm được **secret key** mã hóa response API

---

## Môi trường làm việc

| Thành phần | Chi tiết |
|---|---|
| Hệ điều hành | Windows 11 |
| Python | 3.14.3 |
| Editor | VS Code |
| Database | MySQL Server 8.0.46 + Workbench 8.0.46 |
| Thư viện | selenium, webdriver-manager, mysql-connector-python |
| Thư mục project | E:\LAB211\crawler_project |

---

## Cấu trúc thư mục project

```
crawler_project/
├── config.py       ← Cấu hình database + tài khoản hanzii
├── database.py     ← Kết nối MySQL, tạo bảng, lưu dữ liệu
├── hanzii.py       ← Toàn bộ logic Selenium crawler
├── main.py         ← File chạy chính
├── core.py         ← Scrapy engine cũ (không đụng vào)
└── sites/
    ├── __init__.py
    └── sites.py    ← Cấu hình site Scrapy cũ (không đụng vào)
```

---

## Database

- Tên database: `crawler_db`
- Bảng chính: `hanzii_words`
- Các bảng cũ (không dùng): `websites`, `items`, `crawl_logs`

### Bảng `hanzii_words` — 18 cột

| Cột | Nội dung | Ví dụ |
|---|---|---|
| hanzi | Chữ Hán | 人民 |
| phon_thể | Chữ phồn thể | 人民 |
| pinyin | Pinyin Latin | [ rénmín ] |
| bopomofo | Pinyin Bopomofo | [ ㄖㄣˊㄇㄧㄣˊ ] |
| han_viet | Hán Việt | [ NHÂN DÂN ] |
| hsk_level | Cấp độ HSK | HSK 3 |
| tocfl_level | Cấp độ TOCFL | TOCFL 3 |
| word_type | Loại từ | Danh từ |
| meanings | Nghĩa (ghép bằng \|\|) | nhân dân; đồng bào |
| measure | Lượng từ | 群, 批, 个, 国 |
| compound | Từ ghép | 人民币, 人民网... |
| synonym | Từ cận nghĩa | 群众, 黎民 |
| antonym | Từ trái nghĩa | 故人 |
| image_url | URL hình ảnh minh họa | https://assets.hanzii.net/... |
| audio_url | URL audio phát âm từ chính | https://audio.hanzii.net/audios/cnvi/... |
| example_audio_urls | URL audio câu ví dụ (ghép bằng \|\|) | https://audio.hanzii.net/audios/e_cnvi/... |
| popularity | Độ phổ biến | #3694 |
| search_count | Số lần tra cứu | 1442 |

---

## Lý do dùng Selenium thay Scrapy

- hanzii.net là **Angular app** — HTML trống, dữ liệu load bằng JavaScript
- Scrapy không render được JavaScript
- Response API bị **mã hóa AES** — không đọc được trực tiếp (403 Host not in allowlist)
- Cần Selenium để điều khiển Chrome thật, render JS và lấy dữ liệu từ DOM

---

## Cơ chế hoạt động của bot (phiên bản hiện tại)

1. Chạy `python main.py`
2. Bot **tự mở Chrome**, tự động đăng nhập tài khoản pro
3. Bot in ra **Authorization token** và **secret keys** tìm được từ network
4. Người dùng gõ từ vào ô tìm kiếm trên Chrome đó như bình thường
5. Bot theo dõi URL mỗi 1 giây — khi URL chuyển sang dạng `/search/word/...`, bot tự động crawl
6. Bot click nút "Xem thêm" để lấy đầy đủ dữ liệu
7. Bot scroll trang để trigger lazy load hình ảnh
8. Bot click nút phát âm để bắt audio URL qua network log
9. Dữ liệu được lưu vào MySQL ngay lập tức
10. Tìm từ tiếp theo, bot tiếp tục crawl
11. Nhấn `Ctrl+C` để dừng

---

## Các kỹ thuật bảo mật đã vượt qua

### 1. Automation Detection (navigator.webdriver)

Chrome tự động set `navigator.webdriver = true` khi bị điều khiển bởi Selenium. Hanzii kiểm tra giá trị này để phát hiện bot.

**Cách vượt qua:** Dùng Chrome DevTools Protocol (CDP) inject script trước khi trang load:

```python
driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
    "source": """
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
    """
})
```

### 2. Popup quảng cáo / Modal che nội dung

Hanzii hiển thị popup ngẫu nhiên che nội dung (quảng cáo, thông báo...).

**Cách vượt qua:** Hàm `close_popup()` với 3 lớp:
- XPath tìm nút có text "Đóng" / "Close" / "×"
- CSS selector đặc thù Angular Material
- Nhấn phím Escape

### 3. Lazy Loading hình ảnh

Hanzii dùng lazy loading — ảnh chỉ load khi scroll tới vùng hiển thị.

**Cách vượt qua:** Bot scroll xuống cuối trang, chờ 2 giây, rồi scroll lên để trigger load ảnh.

### 4. Authorization Token (API)

API `api2.hanzii.net` yêu cầu Authorization header hợp lệ. Request trực tiếp bị chặn (403).

**Cách tìm:** F12 → Network → tìm request đến `api2.hanzii.net` → xem Request Headers.

**Giá trị tìm được:** `33165161127683599254S0B20S319S62`

**Cách vượt qua:** Dùng Selenium với tài khoản pro đăng nhập → token được tự động gắn vào mọi request.

### 5. Audio URL (Network Intercept)

Audio phát âm không có trong DOM — chỉ được gọi khi người dùng click nút phát.

**Cách lấy:** Bật Chrome performance logging → flush log → click nút phát âm → bắt URL `.mp3` từ log:

```python
options.set_capability("goog:loggingPrefs", {"performance": "ALL"})
driver.execute_cdp_cmd("Network.enable", {})
# Sau khi click phát âm:
logs = driver.get_log("performance")
# Tìm URL chứa "audio.hanzii.net" và đuôi ".mp3"
```

**Pattern URL:**
- Audio từ chính: `https://audio.hanzii.net/audios/cnvi/{id}/{word_id}.mp3`
- Audio câu ví dụ: `https://audio.hanzii.net/audios/e_cnvi/{id}/{example_id}.mp3`

### 6. AES Secret Key (Response Encryption)

Toàn bộ response từ `api2.hanzii.net` bị mã hóa AES-CBC. Field `data` trong JSON là chuỗi base64 đã mã hóa.

**Cách tìm:** F12 → Sources → Ctrl+Shift+F → search `secretKeyBase64` → tìm thấy trong file JS bundle.

**Secret key tìm được:**
```
LmOUYD1WMUlbNDVLFgdEMVEAPBV1ARpHFGQ5PAdUAgyYhB358SzZREQ1GHB1pF2VAGw0QSSQRNB1UYAgHIx0FQxw3LE1WaUcECAQLHj8fcBF5JRYuEjweL14XbEMMDCM1BxopBg==
```

**Thuật toán:** AES-CBC với Pkcs7 padding, key 256-bit (32 bytes).

**Ý nghĩa bảo mật:** Đây là lỗ hổng nghiêm trọng — secret key bị hardcode trong frontend JavaScript, bất kỳ ai cũng có thể tìm thấy và dùng để giải mã toàn bộ response API.

---

## Selector HTML đã phân tích

| Dữ liệu | Selector |
|---|---|
| Chờ trang load (từ thường) | `div#word.bg-inverse` |
| Chờ trang load (hán tự/bộ thủ) | `div#image` |
| Chữ phồn thể | `simple-tradition` |
| Pinyin Latin | `span.txt-pinyin` (phần tử đầu tiên, không có `txt-cn_vi`) |
| Bopomofo | `span.txt-pinyin` (phần tử thứ 2) |
| Hán Việt | `span.txt-pinyin.txt-cn_vi` |
| HSK level | `div.tags.tag-red` |
| TOCFL level | `div.tags.bg-primary` |
| Loại từ | `[id^='kind'] h2` |
| Nghĩa | `[id^='kind']` |
| Lượng từ | `div#measure` |
| Từ ghép | `div#compound` |
| Từ cận nghĩa | `div#syno` |
| Từ trái nghĩa | `div#anto` |
| Hình ảnh | `div#image img.w-full.thumb-extra` → fallback `div#image img` |
| Nút phát âm | `app-svg-icon[name='outline_speaker']` |
| Nút Xem thêm | XPath trong `div#word`, `div#kind*`, `div#compound`, `div#syno`, `div#anto` |
| Độ phổ biến | `div#popularity` |

---

## Vấn đề URL encode

- Trang hanzii encode URL thành dạng `%E4%BA%BA%E6%B0%91` thay vì chữ Hán thẳng
- Bot dùng `urllib.parse.unquote()` để decode về chữ Hán trước khi xử lý

---

## Vấn đề cấu trúc trang khác nhau

- Từ thông thường: có `div#word.bg-inverse`
- Hán tự / bộ thủ: không có `div#word.bg-inverse`, chỉ có `div#image`
- Bot thử lần lượt 4 signal để chờ trang load, chỉ cần 1 cái xuất hiện là tiến hành crawl

---

## Lệnh hay dùng

```sql
-- Xem dữ liệu
USE crawler_db;
SELECT hanzi, pinyin, han_viet, hsk_level, meanings FROM hanzii_words;

-- Xem audio
SELECT hanzi, audio_url, example_audio_urls FROM hanzii_words;

-- Đếm số từ đã crawl
SELECT COUNT(*) AS tong_so_tu FROM hanzii_words;

-- Xóa 1 từ để crawl lại
DELETE FROM hanzii_words WHERE hanzi = '你好';

-- Xóa toàn bộ để crawl lại từ đầu
DROP TABLE IF EXISTS hanzii_words;

-- Khởi động MySQL nếu bị tắt
net start MySQL80
```

```bash
# Chạy crawler
python main.py
```
