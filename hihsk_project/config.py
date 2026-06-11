# -*- coding: utf-8 -*-
# Cau hinh project crawl hihsk.com
# Database tach rieng khoi project hanzii.

# ---- Database ----
DB_HOST     = "localhost"
DB_USER     = "root"
DB_PASSWORD = "@123@123a"      # <- doi thanh mat khau MySQL cua ban
DB_NAME     = "hihsk_db"

# ---- API ----
API = "https://api.hihsk.com/api/"

# Cac loai noi dung va endpoint tuong ung (da xac dinh qua DevTools)
ENDPOINTS = {
    "vocabulary":   "vocal-list/{id}",     # tu vung (HSK + chu de)
    "conversation": "conversation/{id}",   # hoi thoai
    "radical":      "bothu/{id}",          # bo thu
    "thpt":         "thpt/test/{id}",      # luyen de THPT
    "reading":      "reading-2/{id}",      # doc hieu
    # luyen thi HSK: endpoint exam/hsk/{level}/{id} - xu ly rieng trong crawler
    "exam":         "exam/hsk/{level}/{id}",
    "sentence":     "danh-sach-mau-cau/{id}",  # mau cau
}

# Dai id quet cho tung loai
SCAN_RANGES = {
    "vocabulary":   (1, 500),
    "conversation": (1, 300),
    "radical":      (1, 250),
    "thpt":         (1, 50),
    "reading":      (1, 400),
    "exam":         (1, 600),   # id bai thi (quet chung cho ca 6 level)
    "sentence":     (1, 1000),  # id chu de mau cau
}

# Cac level HSK cho luyen thi
EXAM_LEVELS = [1, 2, 3, 4, 5, 6]

# ---- Tham so crawl ----
DELAY_SEC = 1.0      # nghi giua cac request (lich su voi server)
MAX_MISS  = 50       # gap lien tiep ngan nay id rong thi dung som
TIMEOUT   = 20

USER_AGENT = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
              "AppleWebKit/537.36 (KHTML, like Gecko) "
              "Chrome/120.0 Safari/537.36")
