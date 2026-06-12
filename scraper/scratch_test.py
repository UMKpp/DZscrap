import sys
import os
from pathlib import Path

# Add project root to python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import logging
logging.basicConfig(level=logging.DEBUG)

from twisted.internet import reactor
from scrapy.crawler import CrawlerRunner
from scrapy.utils.log import configure_logging
from scrapy.utils.project import get_project_settings

# Make sure working directory is correct
os.chdir(Path(__file__).resolve().parent)

from scraper.spiders.image_spider import ImageSpider

configure_logging()
settings = get_project_settings()
# Print settings to debug
print("ITEM_PIPELINES:", settings.get("ITEM_PIPELINES"))
print("DOWNLOAD_HANDLERS:", settings.get("DOWNLOAD_HANDLERS"))

runner = CrawlerRunner(settings)

d = runner.crawl(ImageSpider, query="cute cats", limit=5, engine="bing", job_id="test_run")
d.addBoth(lambda _: reactor.stop())
reactor.run()
