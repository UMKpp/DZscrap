import os
import sys
import subprocess
import logging
from backend import config, models
from backend.database import SessionLocal
from worker.celery_app import celery_app

logger = logging.getLogger(__name__)

@celery_app.task(name="worker.tasks.scrape_images_task", bind=True)
def scrape_images_task(self, job_id: str, query: str, limit: int, engine: str):
    logger.info(f"Starting Celery task {self.request.id} for job {job_id} ({query})")
    
    # Create DB Session
    db = SessionLocal()
    
    # Get the job
    job = db.query(models.Job).filter(models.Job.id == job_id).first()
    if not job:
        logger.error(f"Job {job_id} not found in database.")
        db.close()
        return f"Job {job_id} not found"
    
    # Update job status to running
    job.status = "running"
    db.commit()
    
    # Define paths
    scraper_cwd = str(config.SCRAPER_DIR)
    
    # Set up Scrapy crawler environment variables
    # Add database URL so Scrapy pipeline can connect to the database
    # Inject PYTHONPATH so scraper can import from backend
    env = os.environ.copy()
    env["DATABASE_URL"] = config.DATABASE_URL
    env["STORAGE_DIR"] = str(config.STORAGE_DIR)
    
    base_dir_str = str(config.BASE_DIR)
    current_pythonpath = env.get("PYTHONPATH", "")
    if current_pythonpath:
        env["PYTHONPATH"] = f"{base_dir_str}{os.pathsep}{current_pythonpath}"
    else:
        env["PYTHONPATH"] = base_dir_str
    
    # Define cmd to launch scrapy spider
    cmd = [
        sys.executable, "-m", "scrapy", "crawl", "image_spider",
        "-a", f"job_id={job_id}",
        "-a", f"query={query}",
        "-a", f"limit={limit}",
        "-a", f"engine={engine}"
    ]
    
    logger.info(f"Launching scraper command: {' '.join(cmd)} in CWD: {scraper_cwd}")
    
    try:
        # Run Scrapy spider subprocess
        process = subprocess.Popen(
            cmd,
            cwd=scraper_cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env
        )
        
        # Stream logs in real-time
        while True:
            stdout_line = process.stdout.readline()
            stderr_line = process.stderr.readline()
            
            if stdout_line:
                # Log scraper stdout
                logger.debug(f"[Scraper STDOUT] {stdout_line.strip()}")
            if stderr_line:
                # Log scraper stderr
                logger.info(f"[Scraper LOG] {stderr_line.strip()}")
                
            if stdout_line == "" and stderr_line == "" and process.poll() is not None:
                break
                
        return_code = process.wait()
        logger.info(f"Scraper subprocess finished with return code {return_code}")
        
        # Refresh job instance from database to get latest scraped stats from Scrapy pipeline
        db.refresh(job)
        
        if return_code == 0:
            job.status = "completed"
            logger.info(f"Job {job_id} completed successfully. Scraped: {job.total_scraped}, Downloaded: {job.total_downloaded}")
        else:
            job.status = "failed"
            job.error_message = f"Scraper subprocess exited with error code {return_code}"
            logger.error(f"Job {job_id} failed: Scraper subprocess exited with code {return_code}")
            
    except Exception as e:
        logger.exception(f"Unexpected error running scraping task for job {job_id}")
        db.refresh(job)
        job.status = "failed"
        job.error_message = f"Task execution error: {str(e)}"
        
    finally:
        db.commit()
        db.close()
        
    return f"Job {job_id} processing finished"
