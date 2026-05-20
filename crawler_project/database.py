import mysql.connector
from config import DB_HOST, DB_USER, DB_PASSWORD, DB_NAME

def get_connection():
    return mysql.connector.connect(
        host=DB_HOST, user=DB_USER,
        password=DB_PASSWORD, database=DB_NAME
    )

def setup_database():
    """Create all tables if not exists"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS websites (
            id          INT AUTO_INCREMENT PRIMARY KEY,
            name        VARCHAR(100),
            base_url    VARCHAR(255) UNIQUE,
            category    VARCHAR(100),
            created_at  DATETIME DEFAULT NOW()
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS items (
            id            INT AUTO_INCREMENT PRIMARY KEY,
            website_id    INT,
            website_name  VARCHAR(100),
            title         VARCHAR(500),
            field1_name   VARCHAR(100),
            field1_value  TEXT,
            field2_name   VARCHAR(100),
            field2_value  TEXT,
            field3_name   VARCHAR(100),
            field3_value  TEXT,
            url           VARCHAR(500) UNIQUE,
            crawled_at    DATETIME DEFAULT NOW(),
            FOREIGN KEY (website_id) REFERENCES websites(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS crawl_logs (
            id            INT AUTO_INCREMENT PRIMARY KEY,
            website_id    INT,
            website_name  VARCHAR(100),
            started_at    DATETIME,
            finished_at   DATETIME,
            items_saved   INT DEFAULT 0,
            status        VARCHAR(50),
            FOREIGN KEY (website_id) REFERENCES websites(id)
        )
    """)

    conn.commit()
    cursor.close()
    conn.close()
    print("Database setup complete!")

def register_website(name, base_url, category):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT IGNORE INTO websites (name, base_url, category)
            VALUES (%s, %s, %s)
        """, (name, base_url, category))
        conn.commit()
        cursor.execute("SELECT id FROM websites WHERE base_url = %s", (base_url,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        return row[0] if row else None
    except Exception as e:
        print(f"Error registering website: {e}")
        return None

def save_item(website_id, website_name, title, fields, url):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        field_keys   = list(fields.keys())
        field_values = list(fields.values())

        f1_name  = field_keys[0]   if len(field_keys)   > 0 else None
        f1_value = field_values[0] if len(field_values) > 0 else None
        f2_name  = field_keys[1]   if len(field_keys)   > 1 else None
        f2_value = field_values[1] if len(field_values) > 1 else None
        f3_name  = field_keys[2]   if len(field_keys)   > 2 else None
        f3_value = field_values[2] if len(field_values) > 2 else None

        cursor.execute("""
            INSERT IGNORE INTO items
            (website_id, website_name, title,
             field1_name, field1_value,
             field2_name, field2_value,
             field3_name, field3_value, url)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (website_id, website_name, title,
              f1_name, f1_value,
              f2_name, f2_value,
              f3_name, f3_value, url))

        conn.commit()
        saved = cursor.rowcount
        cursor.close()
        conn.close()
        return saved
    except Exception as e:
        print(f"Error saving item: {e}")
        return 0

def log_crawl(website_id, website_name, started_at, finished_at, items_saved, status):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO crawl_logs
            (website_id, website_name, started_at, finished_at, items_saved, status)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (website_id, website_name, started_at, finished_at, items_saved, status))
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error saving log: {e}")


def setup_hanzii_table():
    """Tạo bảng hanzii_words với đầy đủ các cột"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS hanzii_words (
            id           INT AUTO_INCREMENT PRIMARY KEY,

            -- Thông tin cơ bản
            hanzi        VARCHAR(50) UNIQUE,   -- Chữ Hán:        人民
            phon_thể     VARCHAR(50),          -- Chữ phồn thể:   學生
            pinyin       VARCHAR(200),         -- Pinyin Latin:    [ rénmín ]
            bopomofo     VARCHAR(200),         -- Pinyin BoPoMoFo: [ ㄖㄣˊㄇㄧㄣˊ ]
            han_viet     VARCHAR(200),         -- Hán Việt:        [ NHÂN DÂN ]

            -- Cấp độ
            hsk_level    VARCHAR(20),          -- HSK 3
            tocfl_level  VARCHAR(20),          -- TOCFL 3

            -- Nghĩa
            word_type    TEXT,                 -- Loại từ:         Danh từ
            meanings     TEXT,                 -- Tất cả nghĩa ghép lại

            -- Thông tin từ vựng mở rộng
            measure      TEXT,                 -- Lượng từ
            compound     TEXT,                 -- Từ ghép
            synonym      TEXT,                 -- Từ cận nghĩa
            antonym      TEXT,                 -- Từ trái nghĩa

            -- Hình ảnh
            image_url    VARCHAR(1000),        -- URL ảnh minh họa

            -- Audio
            audio_url          VARCHAR(500),   -- URL mp3 phát âm từ chính
            example_audio_urls TEXT,           -- URL mp3 câu ví dụ, ngăn cách bằng ||

            -- Độ phổ biến
            popularity   VARCHAR(20),          -- #3694
            search_count VARCHAR(50),          -- 1442

            crawled_at   DATETIME DEFAULT NOW()
        ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
    """)

    # Tự động thêm cột mới nếu bảng cũ chưa có
    new_columns = [
        ("audio_url",          "ALTER TABLE hanzii_words ADD COLUMN audio_url VARCHAR(500) AFTER image_url"),
        ("example_audio_urls", "ALTER TABLE hanzii_words ADD COLUMN example_audio_urls TEXT AFTER audio_url"),
    ]
    for col_name, sql in new_columns:
        try:
            cursor.execute(sql)
            print(f"Đã thêm cột {col_name}")
        except:
            pass  # Cột đã tồn tại → bỏ qua

    conn.commit()
    cursor.close()
    conn.close()
    print("Bảng hanzii_words sẵn sàng")


def save_hanzii_word(data):
    """Lưu 1 từ vào bảng hanzii_words"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT IGNORE INTO hanzii_words (
                hanzi, phon_thể, pinyin, bopomofo, han_viet,
                hsk_level, tocfl_level,
                word_type, meanings,
                measure, compound, synonym, antonym,
                image_url, audio_url, example_audio_urls,
                popularity, search_count
            ) VALUES (
                %s, %s, %s, %s, %s,
                %s, %s,
                %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s,
                %s, %s
            )
        """, (
            data.get("hanzi"),
            data.get("phon_thể"),
            data.get("pinyin"),
            data.get("bopomofo"),
            data.get("han_viet"),
            data.get("hsk_level"),
            data.get("tocfl_level"),
            data.get("word_type"),
            data.get("meanings"),
            data.get("measure"),
            data.get("compound"),
            data.get("synonym"),
            data.get("antonym"),
            data.get("image_url"),
            data.get("audio_url"),
            data.get("example_audio_urls"),
            data.get("popularity"),
            data.get("search_count"),
        ))
        conn.commit()
        saved = cursor.rowcount
        cursor.close()
        conn.close()
        return saved
    except Exception as e:
        print(f"Lỗi DB: {e}")
        return 0
