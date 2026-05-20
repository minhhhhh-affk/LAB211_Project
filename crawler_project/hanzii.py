"""
hanzii.py — Selenium crawler cho hanzii.net

Cách dùng:
  1. Chạy: python main.py
  2. Chrome tự mở trang hanzii.net, tự đăng nhập tài khoản pro
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
from config import HANZII_EMAIL, HANZII_PASSWORD
from urllib.parse import unquote
from datetime import datetime
import time
import re
import json
import os

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

    # Bật performance logging để capture network requests (dùng cho audio)
    options.set_capability("goog:loggingPrefs", {"performance": "ALL"})

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )

    # Xóa navigator.webdriver — vượt qua automation detection
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """
    })

    # Bật Network CDP để capture request
    driver.execute_cdp_cmd("Network.enable", {})

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

def expand_all(driver):
    """Click tất cả nút Xem thêm trong phần từ vựng — bỏ qua Góp ý"""
    try:
        max_rounds = 10
        for _ in range(max_rounds):
            clicked = False
            btns = driver.find_elements(By.XPATH,
                "//div[@id='word' or starts-with(@id,'kind') or @id='compound' "
                "or @id='syno' or @id='anto' or @id='measure']"
                "//*[contains(normalize-space(.), 'Xem thêm')]"
            )
            for btn in btns:
                try:
                    txt = btn.text.strip()
                    if btn.is_displayed() and "xem thêm" in txt.lower() and len(txt) < 30:
                        driver.execute_script("arguments[0].scrollIntoView(true);", btn)
                        driver.execute_script("arguments[0].click();", btn)
                        time.sleep(0.4)
                        clicked = True
                except:
                    continue
            if not clicked:
                break
    except:
        pass

# ============================================================
# ĐĂNG NHẬP — Luôn đăng nhập mới mỗi lần chạy
# ============================================================
def is_logged_in(driver):
    try:
        els = driver.find_elements(By.CSS_SELECTOR,
            ".user-avatar, .user-name, [class*='avatar'], [class*='profile']"
        )
        return len(els) > 0
    except:
        return False

def login_hanzii(driver):
    """Tự động đăng nhập vào hanzii.net bằng tài khoản pro"""
    print("  Đang đăng nhập tài khoản pro...")
    try:
        driver.get("https://hanzii.net/?hl=vi")
        time.sleep(2)
        close_popup(driver)

        login_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "div.box-login div.btn-brand"))
        )
        driver.execute_script("arguments[0].click();", login_btn)
        print("Đã click nút Đăng nhập")
        time.sleep(2)

        login_modal = WebDriverWait(driver, 8).until(
            EC.presence_of_element_located((By.CSS_SELECTOR,
                "div.login-component app-login"
            ))
        )
        print("Tìm thấy modal đăng nhập")

        email_input = login_modal.find_element(By.CSS_SELECTOR,
            "input[type='text'], input[type='email'], input[formcontrolname='email']"
        )
        driver.execute_script("""
            arguments[0].focus();
            arguments[0].value = arguments[1];
            arguments[0].dispatchEvent(new Event('input',  {bubbles:true}));
            arguments[0].dispatchEvent(new Event('change', {bubbles:true}));
            arguments[0].dispatchEvent(new KeyboardEvent('keyup', {bubbles:true}));
        """, email_input, HANZII_EMAIL)
        time.sleep(0.5)
        print("Đã điền email")

        pass_input = login_modal.find_element(By.CSS_SELECTOR,
            "input[type='password'], input[formcontrolname='password']"
        )
        driver.execute_script("""
            arguments[0].focus();
            arguments[0].value = arguments[1];
            arguments[0].dispatchEvent(new Event('input',  {bubbles:true}));
            arguments[0].dispatchEvent(new Event('change', {bubbles:true}));
            arguments[0].dispatchEvent(new KeyboardEvent('keyup', {bubbles:true}));
        """, pass_input, HANZII_PASSWORD)
        time.sleep(0.5)
        print("Đã điền mật khẩu")

        submit = login_modal.find_element(By.CSS_SELECTOR, "div.btn-login")
        driver.execute_script("arguments[0].click();", submit)
        time.sleep(3)

        try:
            WebDriverWait(driver, 5).until(
                EC.invisibility_of_element_located((By.CSS_SELECTOR, "div.login-component"))
            )
            print("Đăng nhập thành công!")
            return True
        except:
            if is_logged_in(driver):
                print("Đăng nhập thành công!")
                return True
            print("Đăng nhập thất bại — kiểm tra lại email/password trong config.py")
            return False

    except Exception as e:
        print(f"Lỗi đăng nhập: {e}")
        return False

# ============================================================
# TRÍCH XUẤT TỪ TỪ URL
# ============================================================
def extract_word_from_url(url):
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

        # ── MỞ RỘNG TẤT CẢ "XEM THÊM" (chỉ trong section từ vựng) ──
        expand_all(driver)

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

        # ── AUDIO URL (bắt từ network log) ────────────────────
        # Flush log cũ
        try:
            driver.get_log("performance")
        except:
            pass

        # Click nút loa chính để trigger request audio
        try:
            speaker_btn = driver.find_element(By.CSS_SELECTOR,
                "app-svg-icon[name='outline_speaker']"
            )
            driver.execute_script("arguments[0].click();", speaker_btn)
            time.sleep(1.5)
        except:
            pass

        # Click tất cả nút loa trong câu ví dụ
        try:
            example_btns = driver.find_elements(By.CSS_SELECTOR,
                "[id^='kind'] app-svg-icon[name='outline_speaker']"
            )
            for btn in example_btns:
                try:
                    if btn.is_displayed():
                        driver.execute_script("arguments[0].click();", btn)
                        time.sleep(0.4)
                except:
                    continue
        except:
            pass

        time.sleep(1)

        # Lấy log 1 lần — xử lý cả audio chính lẫn audio ví dụ
        audio_url          = ""
        example_audio_urls = ""
        try:
            logs = driver.get_log("performance")
            example_urls = []
            for log in logs:
                try:
                    msg = json.loads(log["message"])["message"]
                    if msg["method"] != "Network.requestWillBeSent":
                        continue
                    url = msg["params"]["request"].get("url", "")
                    if "audio.hanzii.net" not in url or not url.endswith(".mp3"):
                        continue
                    if "/audios/cnvi/" in url and not audio_url:
                        audio_url = url
                    elif "/audios/e_cnvi/" in url and url not in example_urls:
                        example_urls.append(url)
                except:
                    continue
            example_audio_urls = " || ".join(example_urls)
        except:
            pass

        # ── ĐỘ PHỔ BIẾN ───────────────────────────────────────
        popularity = search_count = ""
        try:
            pop_el   = driver.find_element(By.CSS_SELECTOR, "div#popularity")
            pop_text = pop_el.text.strip()
            for line in [l.strip() for l in pop_text.split("\n") if l.strip()]:
                if line.startswith("#"):
                    popularity = line
                elif "tra cứu" in line or "lần" in line:
                    m = re.search(r"(\d[\d,\.]*)", line)
                    search_count = m.group(1).replace(",", "").replace(".", "") if m else ""
        except:
            pass

        return {
            "hanzi"              : word,
            "phon_thể"           : phon_the,
            "pinyin"             : pinyin,
            "bopomofo"           : bopomofo,
            "han_viet"           : han_viet,
            "hsk_level"          : hsk_level,
            "tocfl_level"        : tocfl_level,
            "word_type"          : word_type,
            "meanings"           : meanings,
            "measure"            : measure,
            "compound"           : compound,
            "synonym"            : synonym,
            "antonym"            : antonym,
            "image_url"          : image_url,
            "audio_url"          : audio_url,
            "example_audio_urls" : example_audio_urls,
            "popularity"         : popularity,
            "search_count"       : search_count,
        }

    except Exception as e:
        print(f"Lỗi khi crawl: {e}")
        return None

# ============================================================
# IN KẾT QUẢ
# ============================================================
def print_result(data):
    fields = [
        ("Phồn thể",      "phon_thể"),
        ("Pinyin",        "pinyin"),
        ("Bopomofo",      "bopomofo"),
        ("Hán Việt",      "han_viet"),
        ("HSK",           "hsk_level"),
        ("TOCFL",         "tocfl_level"),
        ("Loại từ",       "word_type"),
        ("Nghĩa",         "meanings"),
        ("Lượng từ",      "measure"),
        ("Từ ghép",       "compound"),
        ("Cận nghĩa",     "synonym"),
        ("Trái nghĩa",    "antonym"),
        ("Hình ảnh",      "image_url"),
        ("Audio",         "audio_url"),
        ("Audio ví dụ",   "example_audio_urls"),
        ("Phổ biến",      "popularity"),
        ("Tra cứu",       "search_count"),
    ]
    for label, key in fields:
        val = data.get(key, "") or ""
        if val:
            display = (val[:75] + "...") if len(val) > 75 else val
            print(f"  {label:<14}: {display}")
        else:
            print(f"  {label:<14}: —")

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
    print("  1. Chrome sẽ tự mở và đăng nhập tài khoản pro")
    print("  2. Gõ từ vào ô tìm kiếm trên web như bình thường")
    print("  3. Bot tự động crawl và lưu vào database")
    print("  4. Tìm tiếp từ khác, bot tiếp tục crawl")
    print("  5. Nhấn Ctrl+C để dừng")
    print()

    setup_hanzii_table()

    print("Đang mở Chrome...")
    driver = create_driver()

    # Luôn đăng nhập mới mỗi lần chạy
    login_hanzii(driver)
    close_popup(driver)

    print()
    print("=" * 58)
    print("Sẵn sàng! Hãy tìm kiếm từ trên web.")
    print("=" * 58)
    print()

    saved_ok  = 0
    skipped   = 0
    failed    = 0
    last_word = None

    try:
        while True:
            try:
                current_url = driver.current_url
            except:
                print("\n  Chrome đã bị đóng. Dừng crawler.")
                break

            word = extract_word_from_url(current_url)

            if word and word != last_word:
                print(f"┌{'─'*54}┐")
                print(f"  Phát hiện: 【{word}】")

                loaded = False
                for wait_sel in [
                    "div#word.bg-inverse",
                    "div#image",
                    "div#popularity",
                    "simple-tradition",
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
                    print(f"Trang load quá chậm, bỏ qua 【{word}】")
                    last_word = word

                if loaded:
                    result = crawl_current_page(driver, word)

                    if result:
                        print_result(result)
                        saved = save_hanzii_word(result)
                        if saved:
                            saved_ok += 1
                            print(f"Đã lưu 【{word}】")
                        else:
                            skipped += 1
                            print(f"【{word}】đã có trong database")
                    else:
                        failed += 1
                        print(f"Crawl thất bại 【{word}】")

                    last_word = word

                print(f"  Thống kê: {saved_ok} lưu {skipped} bỏ qua {failed} lỗi")
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
    print(f"KẾT QUẢ PHIÊN LÀM VIỆC:")
    print(f"Lưu mới  : {saved_ok} từ")
    print(f"Bỏ qua   : {skipped} từ (đã có)")
    print(f"Thất bại : {failed} từ")
    print(f"Kết thúc   : {datetime.now().strftime('%H:%M:%S %d/%m/%Y')}")
    print("=" * 58)
