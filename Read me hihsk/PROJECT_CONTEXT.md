# Ngữ cảnh dự án — Crawler hihsk.com

File này ghi lại bối cảnh để bất kỳ đoạn chat mới nào cũng hiểu ngay dự án đang ở đâu.

## Mục tiêu

Crawl toàn bộ **dữ liệu học công khai** của trang web học tiếng Trung https://hihsk.com,
lưu vào MySQL với các bảng tách rõ ràng. Đây là project học tập (môn LAB211), tách
riêng khỏi project crawl trang hanzii trước đó.

Phạm vi: **chỉ nội dung miễn phí** mà tài khoản được phép xem. Các bài/chủ đề trả phí
(API trả 401/403) được tự động bỏ qua. Không can thiệp vào phân quyền của hệ thống.

## Trang web hoạt động thế nào

hihsk.com là ứng dụng React/Next.js, nội dung lấy qua **API JSON** tại
`https://api.hihsk.com/api/...`. Phát hiện endpoint bằng cách mở DevTools → Network →
Fetch/XHR trên từng trang. API mở CORS công khai, không cần token cho nội dung miễn phí.

URL trang web (vd `hihsk.com/vocabulary/1`) khác với URL API thật. Số cuối URL là id.

## Các loại nội dung và endpoint (ĐÃ XÁC ĐỊNH)

| Loại | URL trang web | Endpoint API | Trạng thái |
|---|---|---|---|
| Từ vựng (HSK + chủ đề) | `/vocabulary/{id}` | `api/vocal-list/{id}` | ✅ chạy tốt |
| Hội thoại | `/conversation/list/{id}` | `api/conversation/{id}` | ✅ chạy tốt |
| Bộ thủ | `/radicals/{id}` | `api/bothu/{id}` | ✅ chạy tốt |
| Luyện đề THPT | `/thpt/test/{id}` | `api/thpt/test/{id}` | ✅ chạy tốt |
| Đọc hiểu | `/reading/{id}` | `api/reading-2/{id}` | ✅ chạy tốt |
| Luyện thi | `/exam/hsk1/{id}` | `api/exam/hsk/{level}/{id}` | ✅ chạy tốt |
| Mẫu câu | `/sentence-sample/{id}` | `api/danh-sach-mau-cau/{id}` | ✅ chạy tốt |

**ĐÃ HOÀN CHỈNH CẢ 7 LOẠI** (vocabulary, conversation, radical, thpt, reading, exam, sentence).

Ghi chu ve endpoint exam: can 2 tham so level (HSK 1-6) va id bai. Crawler quet tung
level x tung id (ham crawl_exam rieng). Cac loai con lai dung endpoint 1 tham so {id}.

## Lưu ý quan trọng về quyền truy cập

- Từ vựng HSK: **bài 1-5 miễn phí**, bài 6+ trả phí (401) → bỏ qua.
- Một số chủ đề từ vựng và mẫu câu có biểu tượng khóa = trả phí.
- Người dùng từng hỏi về việc dùng SQL injection / vượt quyền để lấy nội dung trả phí.
  Điều này KHÔNG được hỗ trợ: vượt phân quyền của một website đang vận hành với người
  dùng thật là truy cập trái phép, kể cả khi là đồ án của nhóm khác trong trường.
  Chỉ crawl nội dung công khai mà tài khoản được phép xem.

## Cấu trúc cấu trúc JSON từng loại (để viết parser)

- **vocabulary** (`vocal-list/{id}`): object có `cate`, `subcate` (thông tin bài),
  `subcates` (danh sách bài con), và **`vocals`** = mảng từ vựng. Mỗi từ ~50 trường:
  `vocabulary` (Hán), `vocabulary_tran` (phồn thể), `pinyin`, `lang_vi`, `lang_en`,
  `han_viet`, `measure_word`, `antonym`, `image`, `mp3`, `character_detail` (JSON nét chữ),
  và mảng con `sentences` (câu ví dụ), `definitions` (nghĩa chi tiết), `levels`.
- **conversation** (`conversation/{id}`): có `data` = mảng bài, mỗi bài có
  `number_lesson`, `lang_vi`, `lang_en`, `lesson_data` (JSON các trang luyện),
  `test_data`.
- **radical** (`bothu/{id}`): có `data` = mảng nhóm, mỗi nhóm có `title` + `content.data[]`
  = các bộ thủ (`hanzi`, `pinyin`, `mean`, `lang_vi`, `netbut`, `image`, `mp3`,
  `common_words`).
- **thpt** (`thpt/test/{id}`): có `exam` = mảng đề, mỗi đề có `title`, `year`, và
  `part1`..`part5` = mảng câu hỏi (`question`, `A`/`B`/`C`/`D`, `answer`, `explain1`,
  `translate_vi`). Lưu ý: id trong JSON (`exam.id`) khác id file.

## Trạng thái dữ liệu hiện tại

- Từ vựng: đã crawl bài 1-5 (miễn phí) về `raw_json/`, đã nạp DB.
- Các loại khác: đã crawl thử, có file mẫu trong `raw_json/{loại}/`.
- Server hihsk **chặn IP ngoài Việt Nam** → phải chạy crawl từ máy người dùng,
  không gọi API được từ môi trường khác.

## Môi trường

- Windows, MySQL (xem bằng MySQL Workbench), Python + `requests`, `mysql-connector-python`.
- Thư mục project: `E:\LAB211\hihsk_project\`
- DB tên `hihsk_db` (tách riêng khỏi `crawler_db` của project hanzii).

## Cấu trúc code (đã gộp gọn còn 4 file)

- `config.py` — cấu hình DB, endpoint, dải id, tham số crawl.
- `database.py` — toàn bộ thao tác MySQL: tạo bảng, lưu, resume, log.
- `crawler.py` — crawl + parse cho cả 4 loại.
- `main.py` — điểm chạy (có menu).

## Việc còn lại (nếu tiếp tục)

Cả 7 loại đã crawl + parse + lưu DB xong. Có thể mở rộng:
1. Tăng dải id quét (SCAN_RANGES) nếu nghi còn nội dung miễn phí chưa lấy hết.
2. Tách sâu hơn các cột JSON còn để nguyên (vd lesson_data của hội thoại,
   explain_json của luyện thi) nếu cần phân tích chi tiết.
3. Tải file media (mp3, ảnh) về nếu muốn lưu offline (hiện chỉ lưu tên/URL file).
