from database import setup_database
from core import run_crawlers
from sites.sites import ALL_SITES

# Setup database tables if not exists
setup_database()

# Run all crawlers at the same time
run_crawlers(ALL_SITES)