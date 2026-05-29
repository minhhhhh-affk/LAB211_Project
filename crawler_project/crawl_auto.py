"""
crawl_auto.py - Tu dong crawl toan bo tu trong wordlist

Dung lai toan bo engine crawl trong hanzii.py (dang nhap, lay anh, lay audio...).
Them: doc wordlist tu file, vong lap tu dong, resume, rate-limit.
"""

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from urllib.parse import quote
from datetime import datetime
import time
import os

from hanzii import create_driver, login_hanzii, close_popup, crawl_current_page
from database import setup_hanzii_table, save_hanzii_word, get_connection

WORDLIST_FILE = "hanzii_wordlist.txt"
DELAY_SECONDS = 1.5
PAGE_TIMEOUT  = 8


def load_wordlist(path):
    if not os.path.exists(path):
        print(f"  LOI: Khong tim thay '{path}'")
        print(f"  Hay dat file wordlist vao cung thu muc voi main.py")
        return []
    with open(path, encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


def get_done_words():
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT hanzi FROM hanzii_words")
        done = {row[0] for row in cur.fetchall()}
        cur.close()
        conn.close()
        return done
    except Exception as e:
        print(f"  Khong doc duoc DB de resume: {e}")
        return set()


def run_auto(limit=None):
    print("=" * 58)
    print("  HANZII CRAWLER - CHE DO TU DONG")
    print(f"  Bat dau: {datetime.now():%H:%M:%S %d/%m/%Y}")
    print("=" * 58)

    setup_hanzii_table()

    words = load_wordlist(WORDLIST_FILE)
    if not words:
        return

    if limit:
        words = words[:limit]

    done  = get_done_words()
    todo  = [w for w in words if w not in done]

    print(f"  Tong trong wordlist : {len(words)}")
    print(f"  Da co trong DB      : {len(done)}")
    print(f"  Can crawl lan nay   : {len(todo)}")
    print("=" * 58)
    print()

    if not todo:
        print("  Tat ca tu da co trong DB roi. Khong co gi de crawl.")
        return

    print("  Dang mo Chrome va dang nhap...")
    driver = create_driver()
    login_hanzii(driver)
    close_popup(driver)
    print()

    saved_ok = skipped = failed = 0

    try:
        for i, word in enumerate(todo, 1):
            url = f"https://hanzii.net/search/word/{quote(word)}?hl=vi"
            print(f"[{i}/{len(todo)}] [{word}]", end="  ", flush=True)

            try:
                driver.get(url)
            except Exception as e:
                failed += 1
                print(f"LOI mo trang: {e}")
                continue

            loaded = False
            for sel in ["div#word.bg-inverse", "div#image",
                        "div#popularity", "simple-tradition"]:
                try:
                    WebDriverWait(driver, PAGE_TIMEOUT).until(
                        EC.presence_of_element_located(
                            (By.CSS_SELECTOR, sel)))
                    loaded = True
                    break
                except TimeoutException:
                    continue

            if not loaded:
                failed += 1
                print(f"SKIP khong load duoc   (ok:{saved_ok} skip:{skipped} loi:{failed})")
                time.sleep(DELAY_SECONDS)
                continue

            result = crawl_current_page(driver, word)

            if result:
                if save_hanzii_word(result):
                    saved_ok += 1
                    print(f"LUU OK   (ok:{saved_ok} skip:{skipped} loi:{failed})")
                else:
                    skipped += 1
                    print(f"DA CO    (ok:{saved_ok} skip:{skipped} loi:{failed})")
            else:
                failed += 1
                print(f"CRAWL LOI (ok:{saved_ok} skip:{skipped} loi:{failed})")

            time.sleep(DELAY_SECONDS)

    except KeyboardInterrupt:
        print("\n\n  Ctrl+C - dung. Du lieu da luu KHONG mat.")
    finally:
        try:
            driver.quit()
        except Exception:
            pass

    print()
    print("=" * 58)
    print("  KET QUA:")
    print(f"  Luu moi  : {saved_ok} tu")
    print(f"  Da co    : {skipped} tu (bo qua)")
    print(f"  Loi/ko co: {failed} tu")
    print(f"  Ket thuc : {datetime.now():%H:%M:%S %d/%m/%Y}")
    print("=" * 58)