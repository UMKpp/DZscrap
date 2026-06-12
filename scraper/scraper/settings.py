import os

BOT_NAME = "scraper"

SPIDER_MODULES = ["scraper.spiders"]
NEWSPIDER_MODULE = "scraper.spiders"

# Crawl responsibly by identifying yourself (and your website) on the user-agent
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# Obey robots.txt rules
ROBOTS_TXT_OBEY = False

# Configure maximum concurrent requests performed by Scrapy (default: 16)
CONCURRENT_REQUESTS = 16

# Configure a delay for requests for the same website (default: 0)
DOWNLOAD_DELAY = 0.5
CONCURRENT_REQUESTS_PER_DOMAIN = 8

# Disable cookies (enabled by default)
COOKIES_ENABLED = False

# Twisted Reactor for Playwright asyncio support
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"

# Download Handlers for Playwright
DOWNLOAD_HANDLERS = {
    "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
    "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
}

# Playwright Launch Settings (Crucial for Docker containers running as root)
PLAYWRIGHT_LAUNCH_OPTIONS = {
    "headless": True,
    "args": [
        "--no-sandbox",
        "--disable-setuid-sandbox",
        "--disable-dev-shm-usage",
        "--disable-gpu",
    ],
}

# Default context configuration for Playwright to avoid bot detection (mask headless chrome)
PLAYWRIGHT_CONTEXTS = {
    "default": {
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "viewport": {"width": 1280, "height": 720},
    }
}

# Enable/Disable downloader middlewares
DOWNLOADER_MIDDLEWARES = {
    "scraper.middlewares.RandomUserAgentMiddleware": 400,
    "scrapy.downloadermiddlewares.useragent.UserAgentMiddleware": None,
}

# Configure item pipelines
ITEM_PIPELINES = {
    "scraper.pipelines.ImageDownloadPipeline": 300,
    "scraper.pipelines.DeduplicatePipeline": 400,
    "scraper.pipelines.DatabasePipeline": 500,
}

# Playwright specific settings
PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT = 30000  # 30 seconds

# Set logs level
LOG_LEVEL = "INFO"

# Hashing and Storage
STORAGE_DIR = os.getenv("STORAGE_DIR", "../storage")
