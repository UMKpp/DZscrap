import scrapy

class TestSpider(scrapy.Spider):
    name = "test_spider"
    
    def start_requests(self):
        self.logger.info("TEST_SPIDER start_requests called!")
        yield scrapy.Request("https://httpbin.org/get", callback=self.parse)
        
    def parse(self, response):
        self.logger.info(f"TEST_SPIDER parsed response! Status: {response.status}")
