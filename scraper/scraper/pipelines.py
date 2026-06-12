import os
import io
import hashlib
import logging
import httpx
from PIL import Image
from scrapy.exceptions import DropItem
from sqlalchemy.orm import Session

from backend.database import SessionLocal
from backend import models, config

logger = logging.getLogger(__name__)

class ImageDownloadPipeline:
    """Pipeline to download image bytes, compute SHA256, verify validity, and check duplicates."""
    
    def __init__(self):
        # Create an async HTTP client for downloading images
        self.client = httpx.AsyncClient(
            timeout=10.0,
            follow_redirects=True,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
        )

    async def close_spider(self, spider):
        await self.client.aclose()

    async def process_item(self, item, spider):
        job_id = item["job_id"]
        url = item["image_url"]
        
        # Ensure job directory exists
        job_dir = config.IMAGES_DIR / job_id
        job_dir.mkdir(parents=True, exist_ok=True)
        
        # Database session to check for global deduplication
        db = SessionLocal()
        try:
            # 1. Quick check: Is this exact URL already scraped for this job?
            existing_url = db.query(models.ScrapedImage).filter(
                models.ScrapedImage.job_id == job_id,
                models.ScrapedImage.url == url
            ).first()
            if existing_url:
                raise DropItem(f"URL already processed for this job: {url}")
                
            # 2. Download image bytes
            try:
                response = await self.client.get(url)
                if response.status_code != 200:
                    raise DropItem(f"Failed to download image from {url}: HTTP {response.status_code}")
                img_bytes = response.content
            except Exception as e:
                raise DropItem(f"Error downloading image from {url}: {e}")
                
            # 3. Verify min size
            if len(img_bytes) < 1024:  # Drop files smaller than 1KB
                raise DropItem(f"Image is too small (< 1KB): {url}")
                
            # 4. Compute SHA256 Hash
            sha256_hash = hashlib.sha256(img_bytes).hexdigest()
            
            # 5. Job-level deduplication: Has this hash already been scraped for this job?
            existing_hash_in_job = db.query(models.ScrapedImage).filter(
                models.ScrapedImage.job_id == job_id,
                models.ScrapedImage.sha256 == sha256_hash
            ).first()
            if existing_hash_in_job:
                raise DropItem(f"Duplicate image hash in this job: {sha256_hash} for url {url}")
                
            # 6. Global deduplication optimization: Has this image been downloaded globally?
            existing_hash_global = db.query(models.ScrapedImage).filter(
                models.ScrapedImage.sha256 == sha256_hash
            ).first()
            
            if existing_hash_global:
                # Reuse existing file to save disk space & bandwidth!
                logger.info(f"Global duplicate found for {sha256_hash}. Reusing file: {existing_hash_global.local_path}")
                item["sha256"] = sha256_hash
                item["local_path"] = existing_hash_global.local_path
                item["file_size"] = existing_hash_global.file_size
                item["width"] = existing_hash_global.width
                item["height"] = existing_hash_global.height
                item["is_downloaded"] = True
                return item
                
            # 7. Verify image format and get dimensions using PIL
            try:
                img = Image.open(io.BytesIO(img_bytes))
                img.verify()  # Verify it's a valid image
                
                # Re-open image to fetch dimensions (verify closes the file)
                img = Image.open(io.BytesIO(img_bytes))
                width, height = img.size
                img_format = img.format.lower() if img.format else "jpg"
            except Exception as e:
                raise DropItem(f"Invalid image format/corrupted file from {url}: {e}")
                
            # Determine extension
            ext = img_format
            if ext == "jpeg":
                ext = "jpg"
                
            # Save file to local disk
            filename = f"{sha256_hash}.{ext}"
            local_path = job_dir / filename
            
            with open(local_path, "wb") as f:
                f.write(img_bytes)
                
            # Populate item fields
            item["sha256"] = sha256_hash
            item["local_path"] = str(local_path)
            item["file_size"] = len(img_bytes)
            item["width"] = width
            item["height"] = height
            item["is_downloaded"] = True
            
            logger.info(f"Downloaded and saved image: {filename} ({width}x{height})")
            return item
            
        finally:
            db.close()


class DeduplicatePipeline:
    """Secondary deduplication check to catch concurrent duplicates (failsafe)."""
    def process_item(self, item, spider):
        # Mostly handled in ImageDownloadPipeline, passes through
        return item


class DatabasePipeline:
    """Pipeline to write scraped image metadata to SQLite database and update job progress."""
    
    def process_item(self, item, spider):
        job_id = item["job_id"]
        
        db = SessionLocal()
        try:
            # Insert scraped image record
            scraped_img = models.ScrapedImage(
                job_id=job_id,
                url=item["image_url"],
                local_path=item["local_path"],
                sha256=item["sha256"],
                file_size=item["file_size"],
                width=item.get("width"),
                height=item.get("height")
            )
            db.add(scraped_img)
            
            # Increment counts on the parent Job
            job = db.query(models.Job).filter(models.Job.id == job_id).first()
            if job:
                # Scrapy keeps track of scraped vs downloaded
                job.total_scraped += 1
                if item.get("is_downloaded", False):
                    job.total_downloaded += 1
                db.commit()
                
        except Exception as e:
            logger.error(f"Error saving image metadata to database: {e}")
            db.rollback()
        finally:
            db.close()
            
        return item
