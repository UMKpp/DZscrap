import json
import logging
from urllib.parse import urlparse, parse_qs, quote_plus
import scrapy
from scrapy.selector import Selector
from scraper.items import ImageItem

logger = logging.getLogger(__name__)

class ImageSpider(scrapy.Spider):
    name = "image_spider"
    
    def __init__(self, job_id=None, query=None, limit=100, engine="bing", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.job_id = job_id
        self.query = query
        self.limit = int(limit)
        self.engine = engine.lower()
        self.scraped_count = 0
        
        logger.info(f"Initialized ImageSpider: job_id={self.job_id}, query='{self.query}', limit={self.limit}, engine='{self.engine}'")

    def start_requests(self):
        if not self.query:
            logger.error("No search query or URL provided.")
            return

        # Build start URLs based on the engine
        if self.engine == "bing":
            url = f"https://www.bing.com/images/search?q={quote_plus(self.query)}"
            yield scrapy.Request(
                url=url,
                callback=self.parse,
                meta={
                    "playwright": True,
                    "playwright_page": True,
                    "playwright_include_body": True,
                }
            )
        elif self.engine == "google":
            url = f"https://www.google.com/search?q={quote_plus(self.query)}&tbm=isch"
            yield scrapy.Request(
                url=url,
                callback=self.parse,
                meta={
                    "playwright": True,
                    "playwright_page": True,
                    "playwright_include_body": True,
                }
            )
        elif self.engine == "generic":
            # In generic engine, query is expected to be a raw URL
            url = self.query
            if not url.startswith("http"):
                url = f"https://{url}"
            yield scrapy.Request(
                url=url,
                callback=self.parse,
                meta={
                    "playwright": True,
                    "playwright_page": True,
                    "playwright_include_body": True,
                }
            )
        else:
            logger.error(f"Unknown scraping engine: {self.engine}")

    async def parse(self, response):
        page = response.meta.get("playwright_page")
        
        if not page:
            logger.warning("Playwright page not loaded. Falling back to static parsing.")
            yield from self.parse_static(response)
            return

        try:
            logger.info("Playwright page loaded successfully. Starting scroll actions...")
            
            # Wait for initial page rendering
            await page.wait_for_timeout(2000)
            
            scroll_attempts = 0
            # Increase scrolls logic. Typically 40-80 images per scroll. To get ~1000 images, we need up to 25 scrolls.
            max_scrolls = 30 
            last_image_count = 0
            consecutive_no_new_images = 0
            
            while scroll_attempts < max_scrolls:
                # Scroll to the bottom of the page
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                
                # Wait for new elements to load
                await page.wait_for_timeout(1500)
                
                # Attempt to click any "Show more results" button if it appears
                try:
                    # Potential button selectors for Google and Bing
                    for selector in [
                        "input[value='Show more results']", # Google Images button
                        ".LZ4Z5e",                          # Google Images loading div/button
                        "#smb",                             # Old Google Show More button
                        ".btn_seemore",                     # Bing See More button
                        "a.mye"                             # Bing pagination
                    ]:
                        btn = await page.query_selector(selector)
                        if btn and await btn.is_visible():
                            logger.info(f"Clicking load-more button: {selector}")
                            await btn.click()
                            await page.wait_for_timeout(1500)
                except Exception as click_err:
                    logger.debug(f"No show-more button clicked in this scroll: {click_err}")
                
                # Retrieve current HTML body content
                html_content = await page.content()
                temp_response = response.replace(body=html_content)
                
                # Count current candidate image URLs
                candidate_urls = self.extract_image_urls(temp_response)
                current_image_count = len(candidate_urls)
                
                logger.info(f"Scroll {scroll_attempts + 1}: Found {current_image_count} candidate image URLs.")
                
                # Terminate early if we have enough URLs
                if current_image_count >= self.limit:
                    logger.info(f"Reached limit target ({self.limit} images). Stopping scroll.")
                    break
                    
                # Check if we are stuck and no new images are loaded
                if current_image_count == last_image_count:
                    consecutive_no_new_images += 1
                    if consecutive_no_new_images >= 3:
                        logger.info("No new images found in last 3 scrolls. Stopping scroll.")
                        break
                else:
                    consecutive_no_new_images = 0
                    
                last_image_count = current_image_count
                scroll_attempts += 1
                
            # Perform final extraction
            final_html = await page.content()
            final_response = response.replace(body=final_html)
            
            # Close playwright page safely
            await page.close()
            
            # Extract and yield items
            yield from self.parse_final_results(final_response)
            
        except Exception as e:
            logger.error(f"Error during Playwright parsing loop: {e}", exc_info=True)
            # Make sure page is closed in case of exception
            if page:
                try:
                    await page.close()
                except Exception:
                    pass
            # Yield whatever we have in the response so far
            yield from self.parse_final_results(response)

    def extract_image_urls(self, response):
        """Helper to extract raw image URLs from the selector based on current engine."""
        urls = []
        if self.engine == "bing":
            # Bing uses JSON metadata in anchors with class iusc
            for m_str in response.css("a.iusc::attr(m)").getall():
                try:
                    m_data = json.loads(m_str)
                    img_url = m_data.get("murl")
                    if img_url and img_url.startswith("http"):
                        urls.append(img_url)
                except Exception:
                    continue
        elif self.engine == "google":
            # Google images: extract from anchor links with href matching /imgres?imgurl=
            for href in response.css("a[href*='/imgres?imgurl=']::attr(href)").getall():
                try:
                    parsed = urlparse(href)
                    queries = parse_qs(parsed.query)
                    img_url = queries.get("imgurl", [None])[0]
                    if img_url and img_url.startswith("http"):
                        urls.append(img_url)
                except Exception:
                    continue
                    
            # Fallback/Additional check: direct image tags
            if len(urls) < 10:
                for src in response.css("img::attr(src)").getall() + response.css("img::attr(data-src)").getall():
                    if src.startswith("http"):
                        urls.append(src)
        else:
            # Generic site crawler: Extract all src, data-src, data-original, etc.
            img_tags = response.css("img")
            for img in img_tags:
                for attr in ["src", "data-src", "data-original", "data-lazy-src"]:
                    src = img.css(f"::attr({attr})").get()
                    if src:
                        abs_url = response.urljoin(src)
                        if abs_url.startswith("http"):
                            urls.append(abs_url)
                            break  # Move to next image tag once a URL is found
                            
        # Remove duplicates while preserving order
        seen = set()
        return [x for x in urls if not (x in seen or seen.add(x))]

    def parse_final_results(self, response):
        """Extract and yield ImageItems up to the requested limit."""
        image_urls = self.extract_image_urls(response)
        logger.info(f"Starting pipeline processing for {len(image_urls)} unique image URLs...")
        
        for url in image_urls:
            if self.scraped_count >= self.limit:
                logger.info(f"Target limit of {self.limit} reached. Stopping yielding items.")
                break
                
            self.scraped_count += 1
            yield ImageItem(
                job_id=self.job_id,
                image_url=url,
                referrer_url=response.url,
                source_engine=self.engine
            )

    def parse_static(self, response):
        """Fallback static parser in case Playwright is not initialized/working."""
        yield from self.parse_final_results(response)
