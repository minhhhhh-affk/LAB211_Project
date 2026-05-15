"""
hanzii.py — Selenium crawler cho hanzii.net

Cách dùng:
  1. Chạy: python main.py
  2. Chrome tự mở trang hanzii.net
  3. Bạn gõ từ vào ô tìm kiếm trên web như bình thường
  4. Bot tự phát hiện trang đã chuyển sang trang từ và crawl data
  5. Gõ tiếp từ khác, bot tiếp tục crawl
  6. Nhấn Ctrl+C trong terminal để dừng
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from database import setup_hanzii_table, save_hanzii_word
from urllib.parse import unquote
from datetime import datetime
import time
import re

# ============================================================
# KHỞI ĐỘNG CHROME
# ============================================================
def create_driver():
    options = webdriver.ChromeOptions()
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
# HELPER
# ============================================================
def get_text(driver, css, timeout=8):
    try:
        el = WebDriverWait(driver, timeout).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, css))
        )
        return el.text.strip()
    except:
        return ""

def get_all_text(driver, css, separator=" || "):
    try:
        els = driver.find_elements(By.CSS_SELECTOR, css)
        texts = [e.text.strip() for e in els if e.text.strip()]
        return separator.join(texts) if texts else ""
    except:
        return ""

def get_attr(driver, css, attr, timeout=8):
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

def close_popup(driver):
    """Đóng mọi loại popup/quảng cáo trên hanzii.net."""
    try:
        btns = driver.find_elements(By.XPATH,
            "//*[self::button or self::a or self::span or self::div]"
            "[normalize-space(text())='Đóng' or normalize-space(text())='Close'"
            " or normalize-space(text())='X' or normalize-space(text())='✕'"
            " or normalize-space(text())='×']"
        )
        for btn in btns:
            if btn.is_displayed():
                driver.execute_script("arguments[0].click();", btn)
                time.sleep(0.5)
                return True
    except:
        pass

    for sel in [
        "div.cdk-overlay-backdrop", "div.modal-backdrop",
        "button.close", "[class*='btn-close']", "[class*='close-btn']",
        "[class*='modal'] button", "[class*='popup'] button",
        "[aria-label='Close']", "[data-dismiss='modal']",
    ]:
        try:
            for el in driver.find_elements(By.CSS_SELECTOR, sel):
                if el.is_displayed():
                    driver.execute_script("arguments[0].click();", el)
                    time.sleep(0.4)
                    return True
        except:
            pass

    try:
        driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
        time.sleep(0.3)
    except:
        pass

    return False

# ============================================================
# TRÍCH XUẤT TỪ TỪ URL
# ============================================================
def extract_word_from_url(url):
    """
    Lấy chữ Hán từ URL:
      https://hanzii.net/search/word/你好?hl=vi
      https://hanzii.net/search/word/%E4%BD%A0%E5%A5%BD?hl=vi
    """
    match = re.search(r"/search/word/([^?#/]+)", url)
    if match:
        word = unquote(match.group(1))
        if re.search(r'[\u4e00-\u9fff]', word):
            return word
    return None

# ============================================================
# CRAWL DỮ LIỆU TỪ TRANG HIỆN TẠI
# ============================================================
def crawl_current_page(driver, word):
    """Crawl toàn bộ dữ liệu từ trang /search/word/... đang mở."""
    try:
        time.sleep(4)
        close_popup(driver)

        # ── CHỮ PHỒN THỂ ──────────────────────────────────────
        phon_the = ""
        try:
            el = driver.find_element(By.CSS_SELECTOR, "simple-tradition")
            phon_the = el.text.strip()
            if "【" in phon_the and "】" in phon_the:
                phon_the = phon_the[phon_the.find("【")+1 : phon_the.find("】")]
        except:
            pass

        # ── PINYIN / BOPOMOFO / HÁN VIỆT ──────────────────────
        pinyin = bopomofo = han_viet = ""
        try:
            spans = driver.find_elements(By.CSS_SELECTOR, "span.txt-pinyin")
            for i, span in enumerate(spans):
                classes = span.get_attribute("class") or ""
                text    = span.text.strip()
                if "txt-cn_vi" in classes:
                    han_viet = text
                elif i == 0:
                    pinyin   = text
                elif i == 1:
                    bopomofo = text
        except:
            pass

        # ── CẤP ĐỘ ────────────────────────────────────────────
        hsk_level   = get_text(driver, "div.tags.tag-red",    timeout=5)
        tocfl_level = get_text(driver, "div.tags.bg-primary", timeout=5)

        # ── LOẠI TỪ + NGHĨA ───────────────────────────────────
        word_type = get_all_text(driver, "[id^='kind'] h2", separator=" | ")
        meanings  = get_all_text(driver, "[id^='kind']",    separator=" || ")

        # ── CÂU VÍ DỤ (đã bỏ theo yêu cầu) ────────────────────
        examples_cn = ""
        examples_vn = ""

        # ── THÔNG TIN MỞ RỘNG ─────────────────────────────────
        measure  = get_text(driver, "div#measure",  timeout=5)
        synonym  = get_text(driver, "div#syno",     timeout=5)
        antonym  = get_text(driver, "div#anto",     timeout=5)
        compound = get_text(driver, "div#compound", timeout=5)
        if compound and len(compound) > 500:
            compound = compound[:500] + "..."

        # ── HÌNH ẢNH (lazy load) ──────────────────────────────
        close_popup(driver)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        close_popup(driver)
        driver.execute_script("window.scrollTo(0, 0);")

        image_url = get_attr(driver, "div#image img.w-full.thumb-extra", "src", timeout=5)
        if not image_url:
            image_url = get_attr(driver, "div#image img", "src", timeout=3)

        # ── ĐỘ PHỔ BIẾN ───────────────────────────────────────
        popularity = search_count = ""
        try:
            pop_el   = driver.find_element(By.CSS_SELECTOR, "div#popularity")
            pop_text = pop_el.text.strip()
            for line in [l.strip() for l in pop_text.split("\n") if l.strip()]:
                if line.startswith("#"):
                    popularity = line
                elif "tra cứu" in line or "lần" in line:
                    search_count = line
                     # Chỉ lấy số: "Được tra cứu 1442 lần" → "1442"
                    m = re.search(r"(\d[\d,\.]*)", line)
                    search_count = m.group(1).replace(",", "").replace(".", "") if m else ""
        except:
            pass

        return {
            "hanzi"       : word,
            "phon_thể"    : phon_the,
            "pinyin"      : pinyin,
            "bopomofo"    : bopomofo,
            "han_viet"    : han_viet,
            "hsk_level"   : hsk_level,
            "tocfl_level" : tocfl_level,
            "word_type"   : word_type,
            "meanings"    : meanings,
            "examples_cn" : examples_cn,
            "examples_vn" : examples_vn,
            "measure"     : measure,
            "compound"    : compound,
            "synonym"     : synonym,
            "antonym"     : antonym,
            "image_url"   : image_url,
            "popularity"  : popularity,
            "search_count": search_count,
        }

    except Exception as e:
        print(f"  ✗ Lỗi khi crawl: {e}")
        return None

# ============================================================
# IN KẾT QUẢ
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
# HÀM CHÍNH
# ============================================================
def run_hanzii():
    print("=" * 58)
    print("  HANZII CRAWLER — Chế độ theo dõi tìm kiếm")
    print(f"  Bắt đầu: {datetime.now().strftime('%H:%M:%S %d/%m/%Y')}")
    print("=" * 58)
    print()
    print("  Cách dùng:")
    print("  1. Chrome sẽ tự mở trang hanzii.net")
    print("  2. Gõ từ vào ô tìm kiếm trên web như bình thường")
    print("  3. Bot tự động crawl và lưu vào database")
    print("  4. Tìm tiếp từ khác, bot tiếp tục crawl")
    print("  5. Nhấn Ctrl+C để dừng")
    print()

    setup_hanzii_table()

    print("Đang mở Chrome...")
    driver = create_driver()
    driver.get("https://hanzii.net/?hl=vi")
    time.sleep(2)
    close_popup(driver)

    print()
    print("=" * 58)
    print("  ✓ Sẵn sàng! Hãy tìm kiếm từ trên web.")
    print("=" * 58)
    print()

    saved_ok  = 0
    skipped   = 0
    failed    = 0
    last_word = None   # Tránh crawl lại từ vừa xong

    try:
        while True:
            try:
                current_url = driver.current_url
            except:
                # Chrome bị đóng tay
                print("\n  Chrome đã bị đóng. Dừng crawler.")
                break

            word = extract_word_from_url(current_url)

            if word and word != last_word:
                print(f"┌{'─'*54}┐")
                print(f"  Phát hiện: 【{word}】")

                # Chờ trang từ load xong — thử nhiều signal vì cấu trúc
                # trang khác nhau: từ thông thường có div#word.bg-inverse,
                # hán tự / bộ thủ có thể dùng cấu trúc khác
                loaded = False
                for wait_sel in [
                    "div#word.bg-inverse",   # từ thông thường
                    "div#image",             # hán tự / bộ thủ
                    "div#popularity",        # fallback chung
                    "simple-tradition",      # fallback chung
                ]:
                    try:
                        WebDriverWait(driver, 8).until(
                            EC.presence_of_element_located(
                                (By.CSS_SELECTOR, wait_sel)
                            )
                        )
                        loaded = True
                        break
                    except TimeoutException:
                        continue
                if not loaded:
                    print(f"  ✗ Trang load quá chậm, bỏ qua 【{word}】")
                    last_word = word

                if loaded:
                    result = crawl_current_page(driver, word)
                    if result:
                        print_result(result)
                        saved = save_hanzii_word(result)
                        if saved:
                            saved_ok += 1
                            print(f"  ✓ Đã lưu 【{word}】")
                        else:
                            skipped += 1
                            print(f"  → 【{word}】đã có trong database")
                    else:
                        failed += 1
                        print(f"  ✗ Crawl thất bại 【{word}】")

                    last_word = word

                print(f"  Thống kê: ✓{saved_ok} lưu  →{skipped} bỏ qua  ✗{failed} lỗi")
                print(f"└{'─'*54}┘")
                print()

            time.sleep(1)

    except KeyboardInterrupt:
        print("\n\nĐã nhấn Ctrl+C — đang dừng...")
    finally:
        try:
            driver.quit()
        except:
            pass

    print()
    print("=" * 58)
    print(f"  KẾT QUẢ PHIÊN LÀM VIỆC:")
    print(f"  ✓ Lưu mới  : {saved_ok} từ")
    print(f"  → Bỏ qua   : {skipped} từ (đã có)")
    print(f"  ✗ Thất bại : {failed} từ")
    print(f"  Kết thúc   : {datetime.now().strftime('%H:%M:%S %d/%m/%Y')}")
    print("=" * 58)