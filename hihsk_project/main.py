# -*- coding: utf-8 -*-
"""
Diem chay chinh project crawl hihsk.com.

Cach dung:
  python main.py                 -> hien menu lua chon
  python main.py crawl           -> crawl ca 4 loai tu API
  python main.py crawl vocabulary-> crawl 1 loai (vocabulary/conversation/radical/thpt)
  python main.py local           -> nap lai tu raw_json/ da co (khong goi API)
"""

import sys
import config
import database as db
import crawler


def main():
    print("=== Crawler hihsk.com ===")
    db.setup_database()

    args = sys.argv[1:]

    # Khong tham so -> menu
    if not args:
        print("""
Chon che do:
  1. Crawl tat ca tu API
  2. Crawl 1 loai
  3. Nap lai tu file raw_json/ da co (khong goi API)
""")
        choice = input("Nhap so (1/2/3): ").strip()
        if choice == "1":
            crawler.crawl_all()
        elif choice == "2":
            print("Cac loai:", ", ".join(config.ENDPOINTS))
            loai = input("Nhap ten loai: ").strip()
            if loai in config.ENDPOINTS:
                crawler.crawl_loai(loai)
            else:
                print("Ten loai khong hop le.")
        elif choice == "3":
            for loai in config.ENDPOINTS:
                crawler.parse_local(loai)
        else:
            print("Lua chon khong hop le.")
        return

    # Co tham so
    mode = args[0]
    if mode == "crawl":
        if len(args) > 1:
            if args[1] == "exam":
                crawler.crawl_exam()
            else:
                crawler.crawl_loai(args[1])
        else:
            crawler.crawl_all()
    elif mode == "local":
        for loai in config.ENDPOINTS:
            crawler.parse_local(loai)
    else:
        print(f"Khong hieu lenh '{mode}'. Xem huong dan o dau file main.py.")


if __name__ == "__main__":
    main()
