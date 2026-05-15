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
- Lấy được các từ tiếng Trung cùng thông tin đi kèm: hán tự, hình ảnh, ngữ nghĩa, ví dụ...
- Lưu vào database có cấu trúc
- Thầy đặc biệt nhấn mạnh: phải lấy được **hình ảnh** (khó nhất) và vượt qua được **"key security"** của trang

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
├── config.py       ← Cấu hình database (không đụng vào)
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

### Bảng `hanzii_words` — 16 cột

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
| popularity | Độ phổ biến | #3694 |
| search_count | Số lần tra cứu (chỉ số) | 1442 |

> **Lưu ý:** Đã bỏ 2 cột `examples_cn` và `examples_vn` so với phiên bản trước.  
> Nếu DB cũ còn 2 cột này, chạy lệnh SQL sau để xóa:
> ```sql
> ALTER TABLE hanzii_words
>   DROP COLUMN examples_cn,
>   DROP COLUMN examples_vn;
> ```

---

## Lý do dùng Selenium thay Scrapy

- hanzii.net là **Angular app** — HTML trống, dữ liệu load bằng JavaScript
- Scrapy không render được JavaScript
- Response API bị **mã hóa / chặn** — không đọc được trực tiếp (403 Host not in allowlist)
- Cần Selenium để điều khiển Chrome thật

---

## Cơ chế hoạt động của bot (phiên bản hiện tại)

1. Chạy `python main.py` → bot **tự mở Chrome và vào thẳng hanzii.net**
2. Người dùng gõ từ vào ô tìm kiếm trên Chrome đó như bình thường
3. Bot theo dõi URL mỗi 1 giây — khi URL chuyển sang dạng `/search/word/...`, bot tự động crawl
4. Dữ liệu được lưu vào MySQL ngay lập tức
5. Tìm từ tiếp theo, bot tiếp tục crawl
6. Nhấn `Ctrl+C` để dừng

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
| Độ phổ biến | `div#popularity` |

---

## "Key security" thầy đề cập

Có 2 loại:

1. **Authorization token** trong Request Headers: `30412333389742336756701217912812` — tìm thấy trong Network tab. API bị chặn từ bên ngoài (403 Host not in allowlist) nên không thể dùng trực tiếp.
2. **Popup quảng cáo** "Vui lòng tắt chặn quảng cáo" / "Join OpportunItaly" — xuất hiện ngẫu nhiên, che nội dung. Bot xử lý bằng hàm `close_popup()` với 3 lớp ưu tiên:
   - XPath tìm nút có text "Đóng"
   - CSS selector đặc thù Angular Material
   - Nhấn phím Escape

---

## Vấn đề hình ảnh

- Hanzii dùng **lazy loading** — ảnh chỉ load khi scroll tới
- Bot scroll xuống cuối trang trước khi lấy ảnh, chờ 2 giây rồi scroll lên lại
- Selector: `div#image img.w-full.thumb-extra` hoặc fallback `div#image img`
- URL ảnh pattern: `https://assets.hanzii.net/img_word/{hash}.jpg`

---

## Vấn đề URL encode

- Trang hanzii encode URL thành dạng `%E4%BA%BA%E6%B0%91` thay vì chữ Hán thẳng
- Bot dùng `urllib.parse.unquote()` để decode về chữ Hán trước khi xử lý

---

## Vấn đề cấu trúc trang khác nhau

- Từ thông thường: có `div#word.bg-inverse`
- Hán tự / bộ thủ (ví dụ: 偏旁): không có `div#word.bg-inverse`, chỉ có `div#image`
- Bot thử lần lượt 4 signal để chờ trang load, chỉ cần 1 cái xuất hiện là tiến hành crawl

---

## Lệnh hay dùng

```sql
-- Xem dữ liệu
USE crawler_db;
SELECT hanzi, pinyin, han_viet, hsk_level, meanings FROM hanzii_words;

-- Đếm số từ đã crawl
SELECT COUNT(*) AS tong_so_tu FROM hanzii_words;

-- Xóa 1 từ để crawl lại
DELETE FROM hanzii_words WHERE hanzi = '你好';

-- Xóa toàn bộ để crawl lại từ đầu
DROP TABLE IF EXISTS hanzii_words;

-- Khởi động MySQL nếu bị tắt
net start MySQL80
```

```
-- Chạy crawler
python main.py
```
