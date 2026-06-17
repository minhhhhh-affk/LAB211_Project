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

File media (ảnh, mp3) được phục vụ riêng tại `https://media.hihsk.com/...` (nginx),
KHÔNG nằm trong JSON dưới dạng URL đầy đủ — JSON chỉ chứa **tên file**, phải tự ghép
URL theo quy luật (xem mục "Quy luật URL media" bên dưới).

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

Ghi chú về endpoint exam: cần 2 tham số level (HSK 1-6) và id bài. Crawler quét từng
level x từng id (hàm `crawl_exam` riêng). Các loại còn lại dùng endpoint 1 tham số {id}.

## Quy luật URL media (ĐÃ XÁC ĐỊNH & VERIFY)

Đây là phần khó nhất, xác định bằng cách đối chiếu các trường trong JSON với URL thật
trên DevTools (Network + Elements). Kết luận sau khi test nhiều từ:

| Media | Trường JSON (tên file) | Folder trong URL | URL đầy đủ |
|---|---|---|---|
| Ảnh | `image_10` | **luôn là `1`** (hằng số) | `media.hihsk.com/vocabulary/images/1/{image_10}` |
| Audio nam | `mp3` | `part` của từ | `media.hihsk.com/vocabulary/male/{part}/{mp3}` |
| Audio nữ | `mp3_female` | `part` của từ | `media.hihsk.com/vocabulary/female/{part}/{mp3_female}` |

Các điểm mấu chốt đã phát hiện trong quá trình debug:

- JSON có nhiều trường ảnh (`image`, `image_2`, `image_4`, `image_10`) nhưng **chỉ
  `image_10` là ảnh hiển thị trên web**. Trường `image` thường là URL ngoài
  (tuhoconline.net) hoặc None.
- Folder ảnh **luôn là `1`**, không phụ thuộc từ. Ví dụ cả 一 (id=5) và 侦探 (id=4985)
  đều dùng `/images/1/`. Thử `cate_id` hay `file_id` làm folder đều SAI (ra 404).
- Folder audio = trường **`part`** của từng từ (KHÔNG phải vocab_id, cate_id, hay
  file_id). Ví dụ: 一 có `part=1` → `/male/1/...`; 侦探 có `part=5` → `/male/5/...`.
- Cùng một từ xuất hiện ở nhiều bài (vd 一 ở cả file 1 và file 51) nhưng tên file media
  giống nhau; URL vẫn build theo `image_10`/`part` của chính từ đó, không theo bài.
- Hàm build URL bỏ qua giá trị None và giữ nguyên nếu đã là URL đầy đủ (bắt đầu http).

Các trường KHÔNG dùng (không khớp UI): `image_2`, `image_4`, `mp3_v2`.

## Lưu ý quan trọng về quyền truy cập

- Từ vựng HSK: **bài 1-5 miễn phí**, bài 6+ trả phí (401) → bỏ qua.
- Một số chủ đề từ vựng và mẫu câu có biểu tượng khóa = trả phí.
- Người dùng từng hỏi về việc dùng SQL injection / vượt quyền để lấy nội dung trả phí.
  Điều này KHÔNG được hỗ trợ: vượt phân quyền của một website đang vận hành với người
  dùng thật là truy cập trái phép, kể cả khi là đồ án của nhóm khác trong trường.
  Chỉ crawl nội dung công khai mà tài khoản được phép xem.
- Server hihsk **chặn IP ngoài Việt Nam** → phải chạy crawl từ máy đặt tại VN.

## Cấu trúc JSON từng loại (để viết parser)

- **vocabulary** (`vocal-list/{id}`): object có `cate`, `subcate` (thông tin bài),
  `subcates` (danh sách bài con), và **`vocals`** = mảng từ vựng. Mỗi từ ~50 trường:
  `id`, `vocabulary` (Hán), `vocabulary_tran` (phồn thể), `pinyin`, `lang_vi`,
  `lang_en`, `han_viet`, `measure_word`, `antonym`, `part` (folder audio),
  `image_10` (tên file ảnh), `mp3` / `mp3_female` (tên file audio nam/nữ),
  `character_detail` (JSON nét chữ), và mảng con `sentences` (câu ví dụ),
  `definitions` (nghĩa chi tiết).
- **conversation** (`conversation/{id}`): có `data` = mảng bài, mỗi bài có
  `number_lesson`, `lang_vi`, `lang_en`, `lesson_data` (JSON các trang luyện),
  `test_data`.
- **radical** (`bothu/{id}`): có `data` = mảng nhóm, mỗi nhóm có `title` +
  `content.data[]` = các bộ thủ (`hanzi`, `pinyin`, `mean`, `lang_vi`, `netbut`,
  `image`, `mp3`, `common_words`).
- **thpt** (`thpt/test/{id}`): có `exam` = mảng đề, mỗi đề có `title`, `year`, và
  `part1`..`part5` = mảng câu hỏi (`question`, `A`/`B`/`C`/`D`, `answer`, `explain1`,
  `translate_vi`). Lưu ý: id trong JSON (`exam.id`) khác id file.
- **reading** (`reading-2/{id}`): có `data` với `content_json` chứa `passage` và
  `questions[]` (nhiều dạng: dictation_input, matching_pairs, multiple choice).
- **exam** (`exam/hsk/{level}/{id}`): có `exam` = mảng đề, mỗi đề có `part1`..`part6`.
- **sentence** (`danh-sach-mau-cau/{id}`): có `data` = mảng mẫu câu.

## Trạng thái dữ liệu hiện tại

- Từ vựng: đã crawl nhiều bài về `raw_json/vocabulary/`, đã nạp DB.
- Media URL: đã hoàn thiện logic build URL cho ảnh + audio nam + audio nữ.
- Các loại khác: đã crawl thử, có file mẫu trong `raw_json/{loại}/`.

## Môi trường

- Windows, MySQL (xem bằng MySQL Workbench), Python + `requests`,
  `mysql-connector-python`.
- Thư mục project: `E:\LAB211\hihsk_project\`
- DB tên `hihsk_db` (tách riêng khỏi `crawler_db` của project hanzii).

## Cấu trúc code (4 file chính)

- `config.py` — cấu hình DB, endpoint, dải id, tham số crawl.
- `database.py` — toàn bộ thao tác MySQL: tạo bảng, lưu, resume, log, migrate cột media.
- `crawler.py` — crawl + parse cho cả 7 loại, gồm hàm build URL media.
- `main.py` — điểm chạy (có menu).

## Các cột media trong bảng `vocabulary`

| Cột | Kiểu | Nội dung |
|---|---|---|
| `image_url` | `VARCHAR(1000)` | URL ảnh đầy đủ (build từ `image_10`) |
| `audio_mp3` | `VARCHAR(1000)` | URL audio giọng nam (build từ `mp3` + `part`) |
| `audio_mp3_female` | `VARCHAR(1000)` | URL audio giọng nữ (build từ `mp3_female` + `part`) |

Hàm `migrate_media_columns()` trong `database.py` tự chạy khi `setup_database()`, dùng
`ADD COLUMN IF NOT EXISTS` + `MODIFY COLUMN` nên chạy lại an toàn, không cần xóa bảng.

## Việc còn lại (nếu tiếp tục)

Cả 7 loại đã crawl + parse + lưu DB xong, gồm cả media URL. Có thể mở rộng:

1. Tăng dải id quét (`SCAN_RANGES`) nếu nghi còn nội dung miễn phí chưa lấy hết.
2. Tách sâu hơn các cột JSON còn để nguyên (vd `lesson_data` của hội thoại,
   `explain_json` của luyện thi) nếu cần phân tích chi tiết.
3. Tải file media (mp3, ảnh) về máy nếu muốn lưu offline (hiện chỉ lưu URL).
4. Kiểm tra `part` có None ở từ nào không → từ đó sẽ không có audio (hiếm gặp).
