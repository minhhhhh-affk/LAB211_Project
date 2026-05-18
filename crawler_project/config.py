# Database configuration
DB_HOST     = "localhost"
DB_USER     = "root"
DB_PASSWORD = "@123@123a"   # ← đổi thành mật khẩu MySQL của bạn
DB_NAME     = "crawler_db"

# Hanzii account (thầy cung cấp)
HANZII_EMAIL    = "chauanhph.neu@gmail.com"   
HANZII_PASSWORD = "Chau@nh18112000"          

# Scrapy settings
SCRAPY_SETTINGS = {
    "BOT_NAME"                        : "crawler",
    "CONCURRENT_REQUESTS"             : 4,      # số trang crawl cùng lúc
    "DOWNLOAD_DELAY"                  : 1,      # chờ 1 giây giữa các request
    "CONCURRENT_REQUESTS_PER_DOMAIN"  : 2,      # tối đa 2 request cùng lúc mỗi domain
    "ROBOTSTXT_OBEY"                  : False,
    "LOG_LEVEL"                       : "ERROR", # chỉ hiện lỗi, ẩn log thừa
    "USER_AGENT"                      : "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}