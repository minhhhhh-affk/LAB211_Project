"""
hanzii.py — Selenium crawler cho hanzii.net
Crawl đầy đủ dữ liệu từ điển Hán-Việt

Selector dựa trên HTML thực tế đã phân tích:
  - span.txt-pinyin           → pinyin Latin:   [ rénmín ]
  - span.txt-pinyin (thứ 2)   → bopomofo:       [ ㄖㄣˊㄇㄧㄣˊ ]
  - span.txt-pinyin.txt-cn-vi → Hán Việt:       [ NHÂN DÂN ]
  - simple-tradition          → chữ phồn thể
  - div.tags.tag-red          → HSK level
  - div.tags.bg-primary       → TOCFL level
  - div#kind_n                → loại từ + nghĩa
  - div#measure               → lượng từ
  - div#compound              → từ ghép
  - div#syno                  → từ cận nghĩa
  - div#anto                  → từ trái nghĩa
  - div#image img.w-full      → hình ảnh
  - div#popularity            → độ phổ biến + số lần tra
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
from database import setup_hanzii_table, save_hanzii_word
from datetime import datetime
import time

# ============================================================
# DANH SÁCH TỪ MUỐN CRAWL — thêm/bớt tùy ý
# ============================================================
WORD_LIST = [
    "人民", "你好", "谢谢", "再见", "对不起",
    "中国", "学习", "汉字", "老师", "学生",
    "精神", "我",   "你",   "他",   "她",
    "吃",   "喝",   "去",   "来",   "看",
    "大",   "小",   "好",   "新",   "一",
]

# ============================================================
# KHỞI ĐỘNG CHROME
# ============================================================
def create_driver():
    options = webdriver.ChromeOptions()

    # Bỏ dấu # nếu KHÔNG muốn thấy cửa sổ Chrome
    # options.add_argument("--headless=new")

    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--lang=vi-VN")
    options.add_argument("--window-size=1400,900")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/148.0.0.0 Safari/537.36"
    )
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )
    driver.maximize_window()
    return driver

# ============================================================
# HELPER — lấy dữ liệu an toàn
# ============================================================
def get_text(driver, css, timeout=8):
    """Lấy text của 1 element"""
    try:
        el = WebDriverWait(driver, timeout).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, css))
        )
        return el.text.strip()
    except:
        return ""

def get_all_text(driver, css, separator=" || "):
    """Lấy text của nhiều element, ghép lại bằng separator"""
    try:
        els = driver.find_elements(By.CSS_SELECTOR, css)
        texts = [e.text.strip() for e in els if e.text.strip()]
        return separator.join(texts) if texts else ""
    except:
        return ""

def get_attr(driver, css, attr, timeout=8):
    """Lấy attribute của 1 element (ví dụ: src của img)"""
    try:
        el = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, css))
        )
        val = el.get_attribute(attr)
        if val and not val.startswith("data:"):
            return val
        return ""
    except:
        return ""

# ============================================================
# CRAWL 1 TỪ
# ============================================================
def crawl_one_word(driver, word):
    url = f"https://hanzii.net/search/word/{word}?hl=vi"
    print(f"  → {url}")

    try:
        driver.get(url)

        # Chờ trang render xong — div#word là signal chính
        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "div#word.bg-inverse")
                )
            )
        except TimeoutException:
            print(f"  ✗ Trang load quá chậm: {word}")
            return None

        # Thêm thời gian để Angular render hết dữ liệu
        time.sleep(4)

        # ── CHỮ PHỒN THỂ ─────────────────────────────────────
        # simple-tradition chứa cả giản thể lẫn phồn thể
        # Ví dụ: 謝謝 (phồn thể của 谢谢)
        phon_the = ""
        try:
            el = driver.find_element(By.CSS_SELECTOR, "simple-tradition")
            phon_the = el.text.strip()
            # Bỏ phần giản thể, chỉ lấy phồn thể trong【】
            if "【" in phon_the and "】" in phon_the:
                phon_the = phon_the[phon_the.find("【")+1 : phon_the.find("】")]
        except:
            pass

        # ── PINYIN, BOPOMOFO, HÁN VIỆT ───────────────────────
        # Có 3 span.txt-pinyin theo thứ tự:
        # [0] = pinyin Latin:   [ rénmín ]
        # [1] = bopomofo:       [ ㄖㄣˊㄇㄧㄣˊ ]
        # [2] = Hán Việt:       [ NHÂN DÂN ]  ← có thêm class txt-cn-vi
        pinyin   = ""
        bopomofo = ""
        han_viet = ""
        try:
            spans = driver.find_elements(By.CSS_SELECTOR, "span.txt-pinyin")
            for i, span in enumerate(spans):
                classes = span.get_attribute("class") or ""
                text    = span.text.strip()
                if "txt-cn-vi" in classes:
                    han_viet = text
                elif i == 0:
                    pinyin   = text
                elif i == 1:
                    bopomofo = text
        except:
            pass

        # ── HSK LEVEL ─────────────────────────────────────────
        # div.tags.tag-red → "HSK 3"
        hsk_level = get_text(driver, "div.tags.tag-red", timeout=5)

        # ── TOCFL LEVEL ───────────────────────────────────────
        # div.tags.bg-primary → "TOCFL 3"
        tocfl_level = get_text(driver, "div.tags.bg-primary", timeout=5)

        # ── LOẠI TỪ ───────────────────────────────────────────
        # Mỗi div#kind_n, div#kind_v, div#kind_adj... là 1 loại từ
        # Lấy tất cả loại từ có trên trang
        word_type = get_all_text(
            driver,
            "[id^='kind'] h2",   # h2 bên trong div có id bắt đầu bằng "kind"
            separator=" | "
        )

        # ── NGHĨA ────────────────────────────────────────────
        # Lấy toàn bộ text của tất cả div kind (chứa loại từ + nghĩa)
        # Ghép lại bằng ||
        meanings = get_all_text(
            driver,
            "[id^='kind']",
            separator=" || "
        )

        # ── CÂU VÍ DỤ TIẾNG TRUNG ────────────────────────────
        # Các câu ví dụ tiếng Trung nằm trong .vi-cn hoặc .sentence-cn
        examples_cn = get_all_text(driver, ".vi-cn, [class*='sentence-cn']")
        # Nếu không tìm được, thử lấy từ div#kind toàn bộ (đã có ví dụ bên trong)
        if not examples_cn:
            try:
                # Lấy các dòng có chữ Hán trong phần kind
                els = driver.find_elements(
                    By.CSS_SELECTOR, "[id^='kind'] .example, [id^='kind'] .vi-item"
                )
                texts = [e.text.strip() for e in els if e.text.strip()]
                examples_cn = " || ".join(texts[:4]) if texts else ""
            except:
                pass

        # ── CÂU VÍ DỤ TIẾNG VIỆT ─────────────────────────────
        examples_vn = get_all_text(driver, ".vi-vn, [class*='sentence-vn']")

        # ── LƯỢNG TỪ ─────────────────────────────────────────
        # div#measure → "群, 批, 个, 国 [qún, pī, gè, guó]"
        measure = get_text(driver, "div#measure", timeout=5)

        # ── TỪ GHÉP ──────────────────────────────────────────
        # div#compound → danh sách từ ghép
        compound = get_text(driver, "div#compound", timeout=5)
        # Cắt bớt nếu quá dài
        if compound and len(compound) > 500:
            compound = compound[:500] + "..."

        # ── TỪ CẬN NGHĨA ─────────────────────────────────────
        # div#syno → 群众, 黎民, 百姓...
        synonym = get_text(driver, "div#syno", timeout=5)

        # ── TỪ TRÁI NGHĨA ─────────────────────────────────────
        # div#anto → 故人
        antonym = get_text(driver, "div#anto", timeout=5)

        # ── HÌNH ẢNH ─────────────────────────────────────────
        # Scroll xuống để kích hoạt lazy load ảnh
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)  # Chờ ảnh load
        driver.execute_script("window.scrollTo(0, 0);")  # Scroll lên lại

        image_url = get_attr(driver, "div#image img.w-full.thumb-extra", "src", timeout=5)
        if not image_url:
            image_url = get_attr(driver, "div#image img", "src", timeout=3)

        # ── ĐỘ PHỔ BIẾN ──────────────────────────────────────
        # div#popularity chứa "#3694" và "Được tra cứu 1442 lần"
        popularity   = ""
        search_count = ""
        try:
            pop_el = driver.find_element(By.CSS_SELECTOR, "div#popularity")
            pop_text = pop_el.text.strip()
            # Tách ra: "#3694" và "Được tra cứu 1442 lần"
            lines = [l.strip() for l in pop_text.split("\n") if l.strip()]
            if lines:
                popularity   = lines[0] if len(lines) > 0 else ""
                search_count = lines[1] if len(lines) > 1 else ""
        except:
            pass

        return {
            "hanzi"      : word,
            "phon_thể"   : phon_the,
            "pinyin"     : pinyin,
            "bopomofo"   : bopomofo,
            "han_viet"   : han_viet,
            "hsk_level"  : hsk_level,
            "tocfl_level": tocfl_level,
            "word_type"  : word_type,
            "meanings"   : meanings,
            "examples_cn": examples_cn,
            "examples_vn": examples_vn,
            "measure"    : measure,
            "compound"   : compound,
            "synonym"    : synonym,
            "antonym"    : antonym,
            "image_url"  : image_url,
            "popularity" : popularity,
            "search_count": search_count,
        }

    except Exception as e:
        print(f"  ✗ Lỗi: {e}")
        return None

# ============================================================
# IN KẾT QUẢ RA MÀN HÌNH
# ============================================================
def print_result(data):
    fields = [
        ("Phồn thể",   "phon_thể"),
        ("Pinyin",     "pinyin"),
        ("Bopomofo",   "bopomofo"),
        ("Hán Việt",   "han_viet"),
        ("HSK",        "hsk_level"),
        ("TOCFL",      "tocfl_level"),
        ("Loại từ",    "word_type"),
        ("Nghĩa",      "meanings"),
        ("Ví dụ CN",   "examples_cn"),
        ("Lượng từ",   "measure"),
        ("Từ ghép",    "compound"),
        ("Cận nghĩa",  "synonym"),
        ("Trái nghĩa", "antonym"),
        ("Hình ảnh",   "image_url"),
        ("Phổ biến",   "popularity"),
        ("Tra cứu",    "search_count"),
    ]
    for label, key in fields:
        val = data.get(key, "") or ""
        if val:
            display = (val[:75] + "...") if len(val) > 75 else val
            print(f"  {label:<12}: {display}")
        else:
            print(f"  {label:<12}: —")

# ============================================================
# HÀM CHÍNH — được gọi từ main.py
# ============================================================
def run_hanzii():
    print("=" * 58)
    print("  HANZII CRAWLER — Từ điển Hán-Việt")
    print(f"  Bắt đầu: {datetime.now().strftime('%H:%M:%S %d/%m/%Y')}")
    print("=" * 58)

    setup_hanzii_table()

    print("\nĐang mở Chrome...")
    driver = create_driver()

    total    = len(WORD_LIST)
    saved_ok = 0
    skipped  = 0
    failed   = 0

    print(f"Tổng số từ: {total}\n")
    print("-" * 58)

    try:
        for i, word in enumerate(WORD_LIST, 1):
            print(f"\n[{i:02d}/{total}] Từ: {word}")

            result = crawl_one_word(driver, word)

            if not result:
                failed += 1
                print("  → THẤT BẠI")
                continue

            print_result(result)

            saved = save_hanzii_word(result)
            if saved:
                saved_ok += 1
                print("  → ✓ Đã lưu vào database")
            else:
                skipped += 1
                print("  → Đã có sẵn, bỏ qua")

            time.sleep(2)

    finally:
        driver.quit()

    print("\n" + "=" * 58)
    print(f"  KẾT QUẢ:")
    print(f"  ✓ Lưu mới   : {saved_ok} từ")
    print(f"  → Bỏ qua    : {skipped} từ (đã có)")
    print(f"  ✗ Thất bại  : {failed} từ")
    print(f"  Kết thúc    : {datetime.now().strftime('%H:%M:%S %d/%m/%Y')}")
    print("=" * 58)
    print("\nXem dữ liệu trong MySQL Workbench:")
    print("  USE crawler_db;")
    print("  SELECT hanzi, pinyin, han_viet, hsk_level, meanings")
    print("  FROM hanzii_words;")