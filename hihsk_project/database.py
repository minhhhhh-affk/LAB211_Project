# -*- coding: utf-8 -*-
"""
Toan bo thao tac database cho project hihsk.

Cac bang:
  TU VUNG:   lessons, vocabulary, sentences, definitions
  HOI THOAI: conversation_lessons
  BO THU:    radical_details
  THPT:      thpt_questions
  LOG:       crawl_logs
"""

import mysql.connector
from config import DB_HOST, DB_USER, DB_PASSWORD, DB_NAME


def get_connection(with_db=True):
    cfg = dict(host=DB_HOST, user=DB_USER, password=DB_PASSWORD)
    if with_db:
        cfg["database"] = DB_NAME
    return mysql.connector.connect(**cfg)


def _exec(sql, params=None, fetch=False):
    """Helper: mo ket noi, chay sql, dong. fetch=True -> tra ve fetchone()[0]."""
    conn = get_connection(); cur = conn.cursor()
    cur.execute(sql, params or ())
    result = cur.fetchone()[0] if fetch else cur.rowcount
    conn.commit(); cur.close(); conn.close()
    return result


# ==================== TAO DATABASE + BANG ====================

def setup_database():
    # Tao DB
    conn = get_connection(with_db=False); cur = conn.cursor()
    cur.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME} "
                f"CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
    conn.commit(); cur.close(); conn.close()

    conn = get_connection(); cur = conn.cursor()

    # ----- TU VUNG -----
    cur.execute("""
        CREATE TABLE IF NOT EXISTS lessons (
            lesson_id      INT PRIMARY KEY,
            cate           VARCHAR(20),
            name           VARCHAR(255),
            lang_vi        VARCHAR(255),
            des            VARCHAR(255),
            conversation   LONGTEXT,
            fill_data_json JSON,
            subcates_json  JSON,
            crawled_at     DATETIME DEFAULT NOW()
        ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS vocabulary (
            id               INT AUTO_INCREMENT PRIMARY KEY,
            vocab_id         INT,
            lesson_id        INT,
            hanzi            VARCHAR(100),
            hanzi_phon       VARCHAR(100),
            pinyin           VARCHAR(255),
            han_viet         VARCHAR(255),
            meaning_vi       TEXT,
            meaning_en       TEXT,
            measure_word     VARCHAR(255),
            antonym          VARCHAR(255),
            image_url        VARCHAR(1000),
            audio_mp3        VARCHAR(1000),
            audio_mp3_female VARCHAR(1000),
            char_detail_json JSON,
            crawled_at       DATETIME DEFAULT NOW(),
            UNIQUE KEY uq_vocab (lesson_id, vocab_id),
            INDEX idx_lesson (lesson_id)
        ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS sentences (
            id        INT AUTO_INCREMENT PRIMARY KEY,
            sent_id   INT,
            vocab_id  INT,
            lesson_id INT,
            text      TEXT, pinyin TEXT, lang_vi TEXT, lang_en TEXT,
            audio_mp3 VARCHAR(1000),
            INDEX idx_vocab (vocab_id), INDEX idx_lesson (lesson_id)
        ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS definitions (
            id             INT AUTO_INCREMENT PRIMARY KEY,
            def_id         INT, vocab_id INT, lesson_id INT,
            part_of_speech VARCHAR(100),
            meaning_vi     TEXT, meaning_en TEXT, senses_json JSON,
            INDEX idx_vocab (vocab_id), INDEX idx_lesson (lesson_id)
        ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
    """)

    # ----- HOI THOAI -----
    cur.execute("""
        CREATE TABLE IF NOT EXISTS conversation_lessons (
            id            INT PRIMARY KEY,
            file_id       INT,
            number_lesson INT,
            lang_vi       VARCHAR(255),
            lang_en       VARCHAR(255),
            lesson_data   LONGTEXT,
            test_data     LONGTEXT,
            crawled_at    DATETIME DEFAULT NOW()
        ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
    """)

    # ----- BO THU -----
    cur.execute("""
        CREATE TABLE IF NOT EXISTS radical_details (
            id           INT AUTO_INCREMENT PRIMARY KEY,
            file_id      INT,
            group_title  VARCHAR(255),
            hanzi        VARCHAR(50),
            pinyin       VARCHAR(100),
            lang_vi      VARCHAR(255),
            mean         VARCHAR(255),
            netbut       VARCHAR(255),
            image        VARCHAR(500),
            mp3          VARCHAR(255),
            common_words TEXT,
            extra_json   LONGTEXT
        ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
    """)

    # ----- THPT -----
    cur.execute("""
        CREATE TABLE IF NOT EXISTS thpt_questions (
            id           INT AUTO_INCREMENT PRIMARY KEY,
            exam_id      INT,
            exam_title   VARCHAR(500),
            year         INT,
            part         VARCHAR(20),
            q_id         INT,
            question     TEXT,
            answer       VARCHAR(10),
            opt_a TEXT, opt_b TEXT, opt_c TEXT, opt_d TEXT,
            explain1     TEXT,
            translate_vi TEXT
        ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
    """)

    # ----- DOC HIEU -----
    cur.execute("""
        CREATE TABLE IF NOT EXISTS reading_lessons (
            reading_id INT PRIMARY KEY,
            name       VARCHAR(500),
            passage    LONGTEXT,
            crawled_at DATETIME DEFAULT NOW()
        ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS reading_questions (
            id          INT AUTO_INCREMENT PRIMARY KEY,
            reading_id  INT,
            q_num       INT,
            q_type      VARCHAR(50),
            question    TEXT,
            choices     TEXT,
            answer      TEXT,
            INDEX idx_reading (reading_id)
        ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
    """)

    # ----- LUYEN THI HSK -----
    cur.execute("""
        CREATE TABLE IF NOT EXISTS exam_questions (
            id           INT AUTO_INCREMENT PRIMARY KEY,
            exam_id      INT,
            level        INT,
            exam_name    VARCHAR(255),
            part         VARCHAR(20),
            q_id         INT,
            question     TEXT,
            answer       VARCHAR(20),
            opt_a TEXT, opt_b TEXT, opt_c TEXT, opt_d TEXT,
            explain1     TEXT,
            translate_vi TEXT,
            mp3          VARCHAR(255),
            image        VARCHAR(255),
            INDEX idx_exam (exam_id)
        ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
    """)

    # ----- MAU CAU -----
    cur.execute("""
        CREATE TABLE IF NOT EXISTS sentence_samples (
            sample_id     INT PRIMARY KEY,
            subcate_id    INT,
            title         VARCHAR(255),
            cn            VARCHAR(500),
            pinyin        VARCHAR(500),
            lang_vi       VARCHAR(500),
            json_question LONGTEXT,
            words_json    LONGTEXT,
            crawled_at    DATETIME DEFAULT NOW(),
            INDEX idx_subcate (subcate_id)
        ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
    """)

    # ----- LOG -----
    cur.execute("""
        CREATE TABLE IF NOT EXISTS crawl_logs (
            id         INT AUTO_INCREMENT PRIMARY KEY,
            loai       VARCHAR(30),
            item_id    INT,
            saved      INT DEFAULT 0,
            status     VARCHAR(50),
            crawled_at DATETIME DEFAULT NOW()
        ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
    """)

    conn.commit(); cur.close(); conn.close()
    print(f"Database '{DB_NAME}' va cac bang da san sang.")
    migrate_media_columns()


def migrate_media_columns():
    """Cap nhat schema media. Chay an toan nhieu lan."""
    conn = get_connection(); cur = conn.cursor()
    for table, col in [
        ("vocabulary",      "image_url"),
        ("vocabulary",      "audio_mp3"),
        ("sentences",       "audio_mp3"),
        ("radical_details", "image"),
        ("radical_details", "mp3"),
        ("exam_questions",  "mp3"),
        ("exam_questions",  "image"),
    ]:
        try:
            cur.execute(f"ALTER TABLE {table} MODIFY COLUMN {col} VARCHAR(1000)")
        except Exception as e:
            print(f"  [migrate] MODIFY {table}.{col}: {e}")
    try:
        cur.execute(
            "ALTER TABLE vocabulary "
            "ADD COLUMN IF NOT EXISTS audio_mp3_female VARCHAR(1000) AFTER audio_mp3")
    except Exception as e:
        print(f"  [migrate] ADD audio_mp3_female: {e}")
    conn.commit(); cur.close(); conn.close()
    print("Migrate media columns hoan tat.")


# ==================== KIEM TRA DA CRAWL (resume) ====================

def vocab_lesson_done(lesson_id):
    return _exec("SELECT COUNT(*) FROM vocabulary WHERE lesson_id=%s",
                 (lesson_id,), fetch=True) > 0

def conversation_done(file_id):
    return _exec("SELECT COUNT(*) FROM conversation_lessons WHERE file_id=%s",
                 (file_id,), fetch=True) > 0

def radical_done(file_id):
    return _exec("SELECT COUNT(*) FROM radical_details WHERE file_id=%s",
                 (file_id,), fetch=True) > 0

def thpt_done(file_id):
    return _exec("SELECT COUNT(*) FROM thpt_questions WHERE exam_id=%s",
                 (file_id,), fetch=True) > 0

def reading_done(reading_id):
    return _exec("SELECT COUNT(*) FROM reading_lessons WHERE reading_id=%s",
                 (reading_id,), fetch=True) > 0

def exam_done(exam_id):
    return _exec("SELECT COUNT(*) FROM exam_questions WHERE exam_id=%s",
                 (exam_id,), fetch=True) > 0

def sentence_done(subcate_id):
    return _exec("SELECT COUNT(*) FROM sentence_samples WHERE subcate_id=%s",
                 (subcate_id,), fetch=True) > 0


# ==================== LUU TU VUNG ====================

def save_lesson(row):
    _exec("""INSERT INTO lessons
             (lesson_id, cate, name, lang_vi, des, conversation,
              fill_data_json, subcates_json)
             VALUES (%(lesson_id)s,%(cate)s,%(name)s,%(lang_vi)s,%(des)s,
                     %(conversation)s,%(fill_data_json)s,%(subcates_json)s)
             ON DUPLICATE KEY UPDATE name=VALUES(name)""", row)

def save_vocab(row):
    return _exec("""INSERT IGNORE INTO vocabulary
             (vocab_id, lesson_id, hanzi, hanzi_phon, pinyin, han_viet,
              meaning_vi, meaning_en, measure_word, antonym,
              image_url, audio_mp3, audio_mp3_female, char_detail_json)
             VALUES (%(vocab_id)s,%(lesson_id)s,%(hanzi)s,%(hanzi_phon)s,%(pinyin)s,
                     %(han_viet)s,%(meaning_vi)s,%(meaning_en)s,%(measure_word)s,
                     %(antonym)s,%(image_url)s,%(audio_mp3)s,%(audio_mp3_female)s,
                     %(char_detail_json)s)""", row)

def save_sentence(row):
    _exec("""INSERT INTO sentences
             (sent_id, vocab_id, lesson_id, text, pinyin, lang_vi, lang_en, audio_mp3)
             VALUES (%(sent_id)s,%(vocab_id)s,%(lesson_id)s,%(text)s,%(pinyin)s,
                     %(lang_vi)s,%(lang_en)s,%(audio_mp3)s)""", row)

def save_definition(row):
    _exec("""INSERT INTO definitions
             (def_id, vocab_id, lesson_id, part_of_speech, meaning_vi, meaning_en, senses_json)
             VALUES (%(def_id)s,%(vocab_id)s,%(lesson_id)s,%(part_of_speech)s,
                     %(meaning_vi)s,%(meaning_en)s,%(senses_json)s)""", row)


# ==================== LUU HOI THOAI / BO THU / THPT ====================

def save_conversation_lesson(row):
    return _exec("""INSERT IGNORE INTO conversation_lessons
             (id, file_id, number_lesson, lang_vi, lang_en, lesson_data, test_data)
             VALUES (%(id)s,%(file_id)s,%(number_lesson)s,%(lang_vi)s,
                     %(lang_en)s,%(lesson_data)s,%(test_data)s)""", row)

def save_radical_detail(row):
    return _exec("""INSERT INTO radical_details
             (file_id, group_title, hanzi, pinyin, lang_vi, mean,
              netbut, image, mp3, common_words, extra_json)
             VALUES (%(file_id)s,%(group_title)s,%(hanzi)s,%(pinyin)s,%(lang_vi)s,
                     %(mean)s,%(netbut)s,%(image)s,%(mp3)s,%(common_words)s,%(extra_json)s)""", row)

def save_thpt_question(row):
    return _exec("""INSERT INTO thpt_questions
             (exam_id, exam_title, year, part, q_id, question, answer,
              opt_a, opt_b, opt_c, opt_d, explain1, translate_vi)
             VALUES (%(exam_id)s,%(exam_title)s,%(year)s,%(part)s,%(q_id)s,
                     %(question)s,%(answer)s,%(opt_a)s,%(opt_b)s,%(opt_c)s,
                     %(opt_d)s,%(explain1)s,%(translate_vi)s)""", row)


def save_reading_lesson(row):
    return _exec("""INSERT IGNORE INTO reading_lessons
             (reading_id, name, passage)
             VALUES (%(reading_id)s,%(name)s,%(passage)s)""", row)

def save_reading_question(row):
    return _exec("""INSERT INTO reading_questions
             (reading_id, q_num, q_type, question, choices, answer)
             VALUES (%(reading_id)s,%(q_num)s,%(q_type)s,%(question)s,
                     %(choices)s,%(answer)s)""", row)


def save_exam_question(row):
    return _exec("""INSERT INTO exam_questions
             (exam_id, level, exam_name, part, q_id, question, answer,
              opt_a, opt_b, opt_c, opt_d, explain1, translate_vi, mp3, image)
             VALUES (%(exam_id)s,%(level)s,%(exam_name)s,%(part)s,%(q_id)s,
                     %(question)s,%(answer)s,%(opt_a)s,%(opt_b)s,%(opt_c)s,
                     %(opt_d)s,%(explain1)s,%(translate_vi)s,%(mp3)s,%(image)s)""", row)


def save_sentence_sample(row):
    return _exec("""INSERT IGNORE INTO sentence_samples
             (sample_id, subcate_id, title, cn, pinyin, lang_vi,
              json_question, words_json)
             VALUES (%(sample_id)s,%(subcate_id)s,%(title)s,%(cn)s,%(pinyin)s,
                     %(lang_vi)s,%(json_question)s,%(words_json)s)""", row)


# ==================== LOG ====================

def log(loai, item_id, saved, status):
    _exec("""INSERT INTO crawl_logs (loai, item_id, saved, status)
             VALUES (%s,%s,%s,%s)""", (loai, item_id, saved, status))