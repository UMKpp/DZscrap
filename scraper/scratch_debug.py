import sys
import os
from pathlib import Path

# Add project root to python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from twisted.internet import reactor
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from scrapy.core.engine import ExecutionEngine

# Import test spider
from scraper.spiders.test_spider import TestSpider

# Monkeypatch ExecutionEngine to print debug info
old_next_request = ExecutionEngine._next_request
def new_next_request(self, spider):
    print(f"DEBUG_ENGINE: _next_request called for {spider.name}!")
    slot = self.slots[spider]
    print(f"DEBUG_ENGINE: slot.start_requests is {type(slot.start_requests)}")
    print(f"DEBUG_ENGINE: slot.inprogress count: {len(slot.inprogress)}")
    print(f"DEBUG_ENGINE: slot.scheduler count: {len(slot.scheduler)}")
    return old_next_request(self, spider)

ExecutionEngine._next_request = new_next_request

old_spider_is_idle = ExecutionEngine.spider_is_idle
def new_spider_is_idle(self, spider):
    idle = old_spider_is_idle(self, spider)
    print(f"DEBUG_ENGINE: spider_is_idle returned {idle}!")
    return idle

ExecutionEngine.spider_is_idle = new_spider_is_idle

# Run CrawlerProcess
os.chdir(Path(__file__).resolve().parent)
settings = get_project_settings()
process = CrawlerProcess(settings)
process.crawl(TestSpider)
process.start()
