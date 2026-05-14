from database import setup_hanzii_table
from hanzii import run_hanzii

# Bước 1: Tạo bảng hanzii_words nếu chưa có
setup_hanzii_table()

# Bước 2: Chạy crawler
run_hanzii()