"""
recrawl_missing.py - Quet don: crawl lai cac tu bi thieu image/popularity/search_count

Cach dung:
  1. Chay main.py cho xong luot chinh (lay duoc ~95%)
  2. Chay file nay: python recrawl_missing.py
  3. No tim cac tu bi thieu trong DB va crawl lai, CHI cap nhat field con trong
     (khong xoa du lieu da co)
  4. Lap lai 2-3 lan cho den khi so tu bi thieu khong giam nua
     (so con lai la nhung tu that su khong co data tren hanzii)
"""

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from urllib.parse import quote
import time

from hanzii import create_driver, login_hanzii, close_popup, crawl_current_page
from database import get_connection

PAGE_TIMEOUT  = 10
DELAY_SECONDS = 1.5


def get_incomplete_words():
    """Lay cac tu thieu image HOAC popularity."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT hanzi FROM hanzii_words
        WHERE (image_url IS NULL OR image_url = '')
           OR (popularity IS NULL OR popularity = '')
    """)
    rows = [r[0] for r in cur.fetchall()]
    cur.close()
    conn.close()
    return rows


def update_word(data):
    """Chi cap nhat field moi tim duoc (khac rong), giu nguyen du lieu cu."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE hanzii_words SET
            image_url    = CASE WHEN %s <> '' THEN %s ELSE image_url    END,
            popularity   = CASE WHEN %s <> '' THEN %s ELSE popularity   END,
            search_count = CASE WHEN %s <> '' THEN %s ELSE search_count END
        WHERE hanzi = %s
    """, (
        data.get("image_url","")    or "", data.get("image_url","")    or "",
        data.get("popularity","")   or "", data.get("popularity","")   or "",
        data.get("search_count","") or "", data.get("search_count","") or "",
        data.get("hanzi"),
    ))
    conn.commit()
    cur.close()
    conn.close()


def run():
    print("=" * 58)
    print("  RECRAWL - Quet don tu bi thieu image/popularity")
    print("=" * 58)

    words = get_incomplete_words()
    print(f"  Co {len(words)} tu bi thieu. Bat dau crawl lai...")
    print()

    if not words:
        print("  Khong co tu nao thieu. Xong!")
        return

    driver = create_driver()
    login_hanzii(driver)
    close_popup(driver)
    print()

    fixed = 0
    try:
        for i, word in enumerate(words, 1):
            url = f"https://hanzii.net/search/word/{quote(word)}?hl=vi"
            print(f"[{i}/{len(words)}] [{word}]", end="  ", flush=True)

            try:
                driver.get(url)
            except Exception as e:
                print(f"LOI mo trang: {e}")
                continue

            loaded = False
            for sel in ["div#word.bg-inverse", "div#image",
                        "div#popularity", "simple-tradition"]:
                try:
                    WebDriverWait(driver, PAGE_TIMEOUT).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, sel)))
                    loaded = True
                    break
                except TimeoutException:
                    continue

            if not loaded:
                print("SKIP khong load duoc")
                time.sleep(DELAY_SECONDS)
                continue

            result = crawl_current_page(driver, word)
            if result:
                update_word(result)
                got_img = bool(result.get("image_url"))
                got_pop = bool(result.get("popularity"))
                if got_img or got_pop:
                    fixed += 1
                print(f"img:{'OK' if got_img else '-'} "
                      f"pop:{'OK' if got_pop else '-'}  (da sua: {fixed})")
            else:
                print("CRAWL LOI")

            time.sleep(DELAY_SECONDS)

    except KeyboardInterrupt:
        print("\n\n  Ctrl+C - dung. Du lieu da cap nhat KHONG mat.")
    finally:
        try:
            driver.quit()
        except Exception:
            pass

    print()
    print("=" * 58)
    print(f"  Xong. Da sua them {fixed} tu.")
    print(f"  Chay lai file nay 1 lan nua de quet not so con thieu.")
    print("=" * 58)


if __name__ == "__main__":
    run()