import scrapy
from scrapy.crawler import CrawlerProcess
from datetime import datetime
from config import SCRAPY_SETTINGS
from database import register_website, save_item, log_crawl

class GenericSpider(scrapy.Spider):
    name = "generic_spider"

    def __init__(self, config, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config       = config
        self.start_urls   = [config["index_url"]]
        self.website_id   = register_website(
                                config["name"],
                                config["base_url"],
                                config["category"]
                            )
        self.website_name = config["name"]
        self.items_saved  = 0
        self.started_at   = datetime.now()

    def parse(self, response):
        """Parse index page, find all links"""
        links = response.css(self.config["link_selector"]+"::attr(href)").getall()
        print(f"Found {len(links)} links on {self.config['name']}")

        for link in links:
            full_url = response.urljoin(link)
            yield scrapy.Request(full_url, callback=self.parse_item)

    def parse_item(self, response):
        """Parse each item page, extract fields"""
        title_selector = self.config["title_selector"]
        title = response.css(title_selector + "::text").get()
        if not title:
            title = response.css(title_selector).get()
        title = title.strip() if title else "No title"

        # Extract extra fields defined in config
        fields = {}
        for field_name, selector in self.config["fields"].items():
            value = response.css(selector + "::text").get()
            if not value:
                value = response.css(selector).get()
            fields[field_name] = value.strip() if value else ""

        saved = save_item(
            self.website_id,
            self.website_name,
            title,
            fields,
            response.url
        )
        if saved:
            self.items_saved += 1
            print(f"[{self.website_name}] Saved: {title}")
        else:
            print(f"[{self.website_name}] Skipped (already exists): {response.url}")

    def closed(self, reason):
        """Called when spider finishes"""
        finished_at = datetime.now()
        status      = "success" if reason == "finished" else "failed"
        log_crawl(
            self.website_id,
            self.website_name,
            self.started_at,
            finished_at,
            self.items_saved,
            status
        )
        print(f"\n=== {self.website_name}: {self.items_saved} items saved ===")

def run_crawlers(configs):
    """Run all site configs at the same time"""
    process = CrawlerProcess(settings=SCRAPY_SETTINGS)

    for config in configs:
        print(f"=== Queuing: {config['name']} ===")
        process.crawl(GenericSpider, config=config)

    print("\n=== Starting all crawlers ===")
    process.start()
    print("\n=== All crawlers finished ===")