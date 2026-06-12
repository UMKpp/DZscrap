import scrapy

class ImageItem(scrapy.Item):
    job_id = scrapy.Field()
    image_url = scrapy.Field()
    referrer_url = scrapy.Field()
    source_engine = scrapy.Field()
