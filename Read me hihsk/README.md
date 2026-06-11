# Crawler hihsk.com

Thu thập dữ liệu học tiếng Trung công khai từ [hihsk.com](https://hihsk.com) thông qua
API JSON, rồi lưu vào cơ sở dữ liệu MySQL với các bảng được tách rõ ràng.

Dự án học tập (môn LAB211). Chỉ thu thập **nội dung miễn phí** mà tài khoản được phép xem;
nội dung trả phí (API trả về 401/403) được tự động bỏ qua.

## Tính năng

- Crawl 7 loại nội dung: **từ vựng** (HSK + chủ đề), **hội thoại**, **bộ thủ**,
  **luyện đề THPT**, **đọc hiểu**, **luyện thi HSK**, **mẫu câu**.
- Lưu JSON gốc vào `raw_json/` để an toàn, đồng thời nạp dữ liệu đã tách cột vào MySQL.
- Tự động bỏ qua mục đã crawl (resume) và mục trả phí.
- Giới hạn tốc độ (nghỉ giữa các request) để không gây tải cho server.

## Yêu cầu

- Python 3.8+
- MySQL Server (khuyến nghị dùng MySQL Workbench để xem dữ liệu)
- Các thư viện Python:

```bash
pip install requests mysql-connector-python
```

## Cài đặt

```bash
git clone <URL-repo-cua-ban>
cd hihsk_project
pip install requests mysql-connector-python
```

### Cấu hình

Mở `config.py` và điền thông tin kết nối MySQL của bạn:

```python
DB_HOST     = "localhost"
DB_USER     = "root"
DB_PASSWORD = "MAT_KHAU_MYSQL_CUA_BAN"   # <- thay bằng mật khẩu của bạn
DB_NAME     = "hihsk_db"
```

> **Lưu ý bảo mật:** đừng commit mật khẩu thật lên GitHub. Hãy để placeholder trong
> `config.py`, hoặc dùng biến môi trường. Nếu lỡ đẩy mật khẩu thật lên repo public,
> nên đổi mật khẩu MySQL ngay.

## Sử dụng

Chạy với menu tương tác:

```bash
python main.py
```

Hoặc dùng tham số dòng lệnh:

```bash
python main.py crawl              # crawl tất cả các loại từ API
python main.py crawl vocabulary   # crawl riêng 1 loại
python main.py crawl exam         # luyện thi (quét theo cả 6 level HSK)
python main.py local              # nạp lại từ raw_json/ đã tải (không gọi API)
```

Các loại hợp lệ: `vocabulary`, `conversation`, `radical`, `thpt`, `reading`, `exam`, `sentence`.

## Cấu trúc dự án

```
hihsk_project/
├── config.py     # Cấu hình: DB, endpoint API, dải id, tham số crawl
├── database.py   # Toàn bộ thao tác MySQL: tạo bảng, lưu, resume, log
├── crawler.py    # Logic crawl + parse cho tất cả các loại
├── main.py       # Điểm chạy chính (có menu)
└── raw_json/     # JSON gốc tải về (tự sinh, không đưa lên git)
```

## Các bảng dữ liệu (`hihsk_db`)

| Nhóm | Bảng | Nội dung |
|---|---|---|
| Từ vựng | `lessons` | Thông tin mỗi bài (cấp, tên, hội thoại, câu hỏi) |
| | `vocabulary` | Từng từ: Hán, pinyin, hán việt, nghĩa Việt/Anh, lượng từ, ảnh, audio |
| | `sentences` | Câu ví dụ của mỗi từ |
| | `definitions` | Nghĩa chi tiết của mỗi từ |
| Hội thoại | `conversation_lessons` | Bài hội thoại |
| Bộ thủ | `radical_details` | Từng bộ thủ: Hán, pinyin, nghĩa, nét bút, từ thường gặp |
| THPT | `thpt_questions` | Câu hỏi đề THPT: đề bài, A/B/C/D, đáp án, giải thích, bản dịch |
| Đọc hiểu | `reading_lessons` | Bài đọc (đoạn văn) |
| | `reading_questions` | Câu hỏi của bài đọc (nhiều dạng) |
| Luyện thi | `exam_questions` | Câu hỏi luyện thi HSK theo level và part |
| Mẫu câu | `sentence_samples` | Mẫu câu theo chủ đề: Hán, pinyin, nghĩa, câu hỏi |
| Khác | `crawl_logs` | Nhật ký mỗi lần crawl |

## Xem dữ liệu

Bằng MySQL Workbench: mở `hihsk_db` rồi chuột phải vào bảng và chọn **Select Rows**.

Hoặc bằng SQL:

```sql
USE hihsk_db;
SELECT lesson_id, hanzi, pinyin, han_viet, meaning_vi FROM vocabulary;
SELECT group_title, hanzi, pinyin, mean FROM radical_details;
SELECT exam_title, year, question, answer, opt_a, opt_b, opt_c, opt_d FROM thpt_questions;
SELECT reading_id, name, LEFT(passage, 50) FROM reading_lessons;
SELECT exam_id, level, part, answer, translate_vi FROM exam_questions;
SELECT sample_id, title, cn, pinyin, lang_vi FROM sentence_samples;
```

## Ghi chú

- Server hihsk chặn truy cập từ IP ngoài Việt Nam, nên cần chạy crawler từ máy đặt tại VN.
- Dự án chỉ thu thập nội dung công khai; nội dung trả phí được bỏ qua.
- Đã hoàn chỉnh cả 7 loại nội dung. Xem `PROJECT_CONTEXT.md` để biết chi tiết endpoint.

## Giấy phép

Dự án phục vụ mục đích học tập.
