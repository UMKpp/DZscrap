import scrapy

class ImageItem(scrapy.Item):
    job_id = scrapy.Field()
    image_url = scrapy.Field()
    referrer_url = scrapy.Field()
    source_engine = scrapy.Field()
    sha256 = scrapy.Field()
    local_path = scrapy.Field()
    file_size = scrapy.Field()
    width = scrapy.Field()
    height = scrapy.Field()
    is_downloaded = scrapy.Field()
