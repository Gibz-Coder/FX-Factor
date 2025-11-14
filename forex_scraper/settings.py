# Scrapy settings for forex_scraper project (minimal)

BOT_NAME = 'forex_scraper'

SPIDER_MODULES = ['forex_scraper.spiders']
NEWSPIDER_MODULE = 'forex_scraper.spiders'

ROBOTSTXT_OBEY = True

ITEM_PIPELINES = {
    'forex_scraper.pipelines.JsonWriterPipeline': 300,
}

FEED_EXPORT_ENCODING = 'utf-8'

# Playwright settings to render JS-heavy pages (ForexFactory)
DOWNLOAD_HANDLERS = {
    'http': 'scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler',
    'https': 'scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler',
}

# Comment/uncomment the reactor below if you get reactor warnings in some environments
TWISTED_REACTOR = 'twisted.internet.asyncioreactor.AsyncioSelectorReactor'

PLAYWRIGHT_BROWSER_TYPE = 'chromium'
# Try non-headless to reduce bot detection; change to True if you prefer headless
PLAYWRIGHT_LAUNCH_OPTIONS = {'headless': False, 'args': ['--no-sandbox', '--disable-blink-features=AutomationControlled']}

# Set a realistic User-Agent to help avoid simple bot blocks
DEFAULT_REQUEST_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9'
}

