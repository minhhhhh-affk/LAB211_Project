"""
hanzii.py - Selenium crawler cho hanzii.net (toi uu thoi gian: cho thong minh thay sleep co dinh)
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
# KHOI DONG CHROME
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

    options.set_capability("goog:loggingPrefs", {"performance": "ALL"})

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )

    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });

            window.__hanziiAudio = [];

            const _Audio = window.Audio;
            window.Audio = function(src) {
                if (src && typeof src === 'string' && src.includes('audio.hanzii.net'))
                    window.__hanziiAudio.push(src);
                return new _Audio(src);
            };

            const _desc = Object.getOwnPropertyDescriptor(HTMLMediaElement.prototype, 'src');
            if (_desc && _desc.set) {
                Object.defineProperty(HTMLMediaElement.prototype, 'src', {
                    set: function(val) {
                        if (val && typeof val === 'string' && val.includes('audio.hanzii.net'))
                            window.__hanziiAudio.push(val);
                        _desc.set.call(this, val);
                    },
                    get: _desc.get
                });
            }
        """
    })

    driver.execute_cdp_cmd("Network.enable", {})
    driver.maximize_window()
    return driver

# ============================================================
# HELPER
# ============================================================
def get_text(driver, css, timeout=5):
    try:
        el = WebDriverWait(driver, timeout).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, css)))
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

def get_attr(driver, css, attr, timeout=5):
    try:
        el = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, css)))
        val = el.get_attribute(attr)
        if val and not val.startswith("data:"):
            return val
        return ""
    except:
        return ""

def close_popup(driver):
    try:
        btns = driver.find_elements(By.XPATH,
            "//*[self::button or self::a or self::span or self::div]"
            "[normalize-space(text())='\u0110\u00f3ng' or normalize-space(text())='Close'"
            " or normalize-space(text())='X' or normalize-space(text())='\u2715'"
            " or normalize-space(text())='\u00d7']"
        )
        for btn in btns:
            if btn.is_displayed():
                driver.execute_script("arguments[0].click();", btn)
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
                    return True
        except:
            pass

    try:
        driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
    except:
        pass

    return False

def expand_all(driver):
    try:
        for _ in range(10):
            clicked = False
            btns = driver.find_elements(By.XPATH,
                "//div[@id='word' or starts-with(@id,'kind') or @id='compound' "
                "or @id='syno' or @id='anto' or @id='measure']"
                "//*[contains(normalize-space(.), 'Xem th\u00eam')]"
            )
            for btn in btns:
                try:
                    txt = btn.text.strip()
                    if btn.is_displayed() and "xem th\u00eam" in txt.lower() and len(txt) < 30:
                        driver.execute_script("arguments[0].scrollIntoView(true);", btn)
                        driver.execute_script("arguments[0].click();", btn)
                        clicked = True
                except:
                    continue
            if not clicked:
                break
    except:
        pass

# ============================================================
# CHO TRANG SAN SANG - return NGAY khi co noi dung (thay sleep(7))
# ============================================================
def wait_page_ready(driver, timeout=9):
    def ready(d):
        try:
            # Co nghia (kind co text)
            if any(k.text.strip() for k in d.find_elements(By.CSS_SELECTOR, "[id^='kind']")):
                return True
            # Hoac co pinyin
            if any(p.text.strip() for p in d.find_elements(By.CSS_SELECTOR, "span.txt-pinyin")):
                return True
            # Hoac la trang han tu (co image, khong co nghia)
            if d.find_elements(By.CSS_SELECTOR, "div#image"):
                return True
        except:
            return False
        return False
    try:
        WebDriverWait(driver, timeout).until(ready)
    except:
        pass
    time.sleep(0.6)   # buffer nho cho Angular render not

# ============================================================
# DANG NHAP
# ============================================================
def is_logged_in(driver):
    try:
        els = driver.find_elements(By.CSS_SELECTOR,
            ".user-avatar, .user-name, [class*='avatar'], [class*='profile']")
        return len(els) > 0
    except:
        return False

def login_hanzii(driver):
    print("  Dang dang nhap tai khoan pro...")
    try:
        driver.get("https://hanzii.net/?hl=vi")
        time.sleep(2)
        close_popup(driver)

        login_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "div.box-login div.btn-brand")))
        driver.execute_script("arguments[0].click();", login_btn)
        print("  Da click nut Dang nhap")
        time.sleep(2)

        login_modal = WebDriverWait(driver, 8).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.login-component app-login")))
        print("  Tim thay modal dang nhap")

        email_input = login_modal.find_element(By.CSS_SELECTOR,
            "input[type='text'], input[type='email'], input[formcontrolname='email']")
        driver.execute_script("""
            arguments[0].focus();
            arguments[0].value = arguments[1];
            arguments[0].dispatchEvent(new Event('input',  {bubbles:true}));
            arguments[0].dispatchEvent(new Event('change', {bubbles:true}));
            arguments[0].dispatchEvent(new KeyboardEvent('keyup', {bubbles:true}));
        """, email_input, HANZII_EMAIL)
        time.sleep(0.5)
        print("  Da dien email")

        pass_input = login_modal.find_element(By.CSS_SELECTOR,
            "input[type='password'], input[formcontrolname='password']")
        driver.execute_script("""
            arguments[0].focus();
            arguments[0].value = arguments[1];
            arguments[0].dispatchEvent(new Event('input',  {bubbles:true}));
            arguments[0].dispatchEvent(new Event('change', {bubbles:true}));
            arguments[0].dispatchEvent(new KeyboardEvent('keyup', {bubbles:true}));
        """, pass_input, HANZII_PASSWORD)
        time.sleep(0.5)
        print("  Da dien mat khau")

        submit = login_modal.find_element(By.CSS_SELECTOR, "div.btn-login")
        driver.execute_script("arguments[0].click();", submit)
        time.sleep(3)

        try:
            WebDriverWait(driver, 5).until(
                EC.invisibility_of_element_located((By.CSS_SELECTOR, "div.login-component")))
            print("  Dang nhap thanh cong!")
            return True
        except:
            if is_logged_in(driver):
                print("  Dang nhap thanh cong!")
                return True
            print("  Dang nhap that bai - kiem tra lai config.py")
            return False
    except Exception as e:
        print(f"  Loi dang nhap: {e}")
        return False

# ============================================================
# TRICH XUAT TU TU URL
# ============================================================
def extract_word_from_url(url):
    match = re.search(r"/search/word/([^?#/]+)", url)
    if match:
        word = unquote(match.group(1))
        if re.search(r'[\u4e00-\u9fff]', word):
            return word
    return None

# ============================================================
# LAY HINH ANH - poll nhanh, return ngay khi co src
# ============================================================
def extract_image(driver, max_wait=5.0):
    try:
        img_el = driver.find_element(By.CSS_SELECTOR,
            "div#image img.w-full.thumb-extra, div#image img")
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", img_el)
    except:
        return ""

    deadline = time.time() + max_wait
    while time.time() < deadline:
        try:
            val = driver.execute_script("""
                var img = document.querySelector('div#image img.w-full.thumb-extra')
                       || document.querySelector('div#image img');
                if (!img) return '';
                var s = img.currentSrc || img.src || img.getAttribute('src') || '';
                return s.startsWith('http') ? s : '';
            """) or ""
            if val:
                return val
        except:
            pass
        time.sleep(0.25)
    return ""

# ============================================================
# LAY DO PHO BIEN - poll nhanh, return ngay khi co data
# ============================================================
def extract_popularity(driver, max_wait=6.0):
    popularity = search_count = ""
    try:
        pop_el = driver.find_element(By.CSS_SELECTOR, "div#popularity")
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", pop_el)
        time.sleep(0.3)
        # Scroll ra ngoai roi scroll lai -> dam bao Intersection Observer fire
        driver.execute_script("window.scrollBy(0, -200);")
        time.sleep(0.2)
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", pop_el)
    except:
        return "", ""

    deadline = time.time() + max_wait
    while time.time() < deadline:
        try:
            pop_text = driver.find_element(By.CSS_SELECTOR, "div#popularity").text.strip()
            if len(pop_text) > 3:
                for line in [l.strip() for l in pop_text.split("\n") if l.strip()]:
                    if line.startswith("#"):
                        popularity = line
                    elif "tra c\u1ee9u" in line or "l\u1ea7n" in line:
                        m = re.search(r"(\d[\d,\.]*)", line)
                        search_count = m.group(1).replace(",","").replace(".","") if m else ""
                if popularity:
                    return popularity, search_count
        except:
            pass
        time.sleep(0.3)
    return popularity, search_count

# ============================================================
# CRAWL DU LIEU TU TRANG HIEN TAI
# ============================================================
def crawl_current_page(driver, word):
    try:
        wait_page_ready(driver)     # thay cho sleep(7) - return ngay khi san sang
        close_popup(driver)
        expand_all(driver)

        # CHU PHON THE
        phon_the = ""
        try:
            el = driver.find_element(By.CSS_SELECTOR, "simple-tradition")
            phon_the = el.text.strip()
            if "\u3010" in phon_the and "\u3011" in phon_the:
                phon_the = phon_the[phon_the.find("\u3010")+1 : phon_the.find("\u3011")]
        except:
            pass

        # PINYIN / BOPOMOFO / HAN VIET
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

        # CAP DO
        hsk_level   = get_text(driver, "div.tags.tag-red",    timeout=3)
        tocfl_level = get_text(driver, "div.tags.bg-primary", timeout=3)

        # LOAI TU + NGHIA
        word_type = get_all_text(driver, "[id^='kind'] h2", separator=" | ")
        meanings  = get_all_text(driver, "[id^='kind']",    separator=" || ")

        # THONG TIN MO RONG
        measure  = get_text(driver, "div#measure",  timeout=3)
        synonym  = get_text(driver, "div#syno",     timeout=3)
        antonym  = get_text(driver, "div#anto",     timeout=3)
        compound = get_text(driver, "div#compound", timeout=3)
        if compound and len(compound) > 500:
            compound = compound[:500] + "..."

        # SCROLL XUONG DAY -> trigger lazy load (ca anh va popularity)
        close_popup(driver)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2.0)
        close_popup(driver)

        # DO PHO BIEN (poll nhanh)
        popularity, search_count = extract_popularity(driver)

        # HINH ANH (poll nhanh)
        image_url = extract_image(driver)

        # AUDIO - click loa roi poll interceptor (return ngay khi bat duoc URL)
        try:
            driver.execute_script("window.__hanziiAudio = [];")
        except:
            pass
        try:
            speaker_btn = driver.find_element(By.CSS_SELECTOR,
                "app-svg-icon[name='outline_speaker']")
            driver.execute_script("arguments[0].click();", speaker_btn)
        except:
            pass
        try:
            example_btns = driver.find_elements(By.CSS_SELECTOR,
                "[id^='kind'] app-svg-icon[name='outline_speaker']")
            for btn in example_btns:
                try:
                    if btn.is_displayed():
                        driver.execute_script("arguments[0].click();", btn)
                except:
                    continue
        except:
            pass

        # Poll interceptor toi da 2.5s
        audio_url          = ""
        example_audio_urls = ""
        example_urls       = []
        deadline = time.time() + 2.5
        while time.time() < deadline:
            try:
                captured = driver.execute_script("return window.__hanziiAudio || [];")
            except:
                captured = []
            example_urls = []
            audio_url = ""
            for url in (captured or []):
                if "/audios/cnvi/" in url and not audio_url:
                    audio_url = url
                elif "/audios/e_cnvi/" in url and url not in example_urls:
                    example_urls.append(url)
            if audio_url or example_urls:
                break
            time.sleep(0.25)
        example_audio_urls = " || ".join(example_urls)

        return {
            "hanzi"              : word,
            "phon_th\u1ec3"      : phon_the,
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
        print(f"Loi khi crawl: {e}")
        return None

# ============================================================
# IN KET QUA
# ============================================================
def print_result(data):
    fields = [
        ("Phon the",      "phon_th\u1ec3"),
        ("Pinyin",        "pinyin"),
        ("Bopomofo",      "bopomofo"),
        ("Han Viet",      "han_viet"),
        ("HSK",           "hsk_level"),
        ("TOCFL",         "tocfl_level"),
        ("Loai tu",       "word_type"),
        ("Nghia",         "meanings"),
        ("Luong tu",      "measure"),
        ("Tu ghep",       "compound"),
        ("Can nghia",     "synonym"),
        ("Trai nghia",    "antonym"),
        ("Hinh anh",      "image_url"),
        ("Audio",         "audio_url"),
        ("Audio vi du",   "example_audio_urls"),
        ("Pho bien",      "popularity"),
        ("Tra cuu",       "search_count"),
    ]
    for label, key in fields:
        val = data.get(key, "") or ""
        if val:
            display = (val[:75] + "...") if len(val) > 75 else val
            print(f"  {label:<14}: {display}")
        else:
            print(f"  {label:<14}: -")