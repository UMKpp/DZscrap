import os
import shutil
import zipfile
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from celery import Celery

from backend import config, models, schemas
from backend.database import engine, get_db

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(config.LOGS_DIR / "backend.log")
    ]
)
logger = logging.getLogger(__name__)

# Initialize database tables
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up FastAPI application. Creating database tables...")
    models.Base.metadata.create_all(bind=engine)
    yield
    logger.info("Shutting down FastAPI application.")

app = FastAPI(
    title="Image Scraper Pro API",
    description="Backend API for Distributed Image Scraping System",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for Chrome Extension and local testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for extension popups
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount storage directory for static access to downloaded images
app.mount("/storage", StaticFiles(directory=config.STORAGE_DIR), name="storage")

# Initialize Celery Client
celery_client = Celery("image_scraper", broker=config.REDIS_URL, backend=config.REDIS_URL)

@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "Image Scraper Pro API is running"}

@app.post("/api/v1/scrape", response_model=schemas.JobResponse, status_code=status.HTTP_201_CREATED)
async def create_scrape_job(payload: schemas.JobCreate, db: Session = Depends(get_db)):
    logger.info(f"Received scrape request: query='{payload.query}', limit={payload.limit}, engine='{payload.engine}'")
    
    # Create database entry
    job = models.Job(
        query=payload.query,
        limit=payload.limit,
        engine=payload.engine.lower(),
        status="pending"
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    
    logger.info(f"Created job {job.id} in database. Dispatching Celery task...")
    
    # Send task to Celery
    try:
        celery_client.send_task(
            "worker.tasks.scrape_images_task",
            args=[job.id, job.query, job.limit, job.engine]
        )
        logger.info(f"Successfully dispatched Celery task for job {job.id}")
    except Exception as e:
        logger.error(f"Failed to dispatch Celery task for job {job.id}: {e}")
        job.status = "failed"
        job.error_message = f"Failed to dispatch task queue: {str(e)}"
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to queue scraping task"
        )
        
    return job

@app.get("/api/v1/jobs", response_model=list[schemas.JobResponse])
async def list_jobs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    jobs = db.query(models.Job).order_by(models.Job.created_at.desc()).offset(skip).limit(limit).all()
    return jobs

@app.get("/api/v1/jobs/{job_id}", response_model=schemas.JobDetailResponse)
async def get_job(job_id: str, db: Session = Depends(get_db)):
    job = db.query(models.Job).filter(models.Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@app.get("/api/v1/jobs/{job_id}/results", response_model=list[schemas.ScrapedImageResponse])
async def get_job_results(job_id: str, db: Session = Depends(get_db)):
    job = db.query(models.Job).filter(models.Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job.images

@app.delete("/api/v1/jobs/{job_id}", status_code=status.HTTP_200_OK)
async def delete_job(job_id: str, db: Session = Depends(get_db)):
    job = db.query(models.Job).filter(models.Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    logger.info(f"Deleting job {job_id} and clean up storage")
    
    # Clean up files from disk
    job_images_dir = config.IMAGES_DIR / job_id
    if job_images_dir.exists() and job_images_dir.is_dir():
        try:
            shutil.rmtree(job_images_dir)
            logger.info(f"Deleted storage directory: {job_images_dir}")
        except Exception as e:
            logger.error(f"Error deleting directory {job_images_dir}: {e}")
            
    # Delete associated exports if they exist
    export_file = config.STORAGE_DIR / "exports" / f"{job_id}.zip"
    if export_file.exists():
        try:
            os.remove(export_file)
            logger.info(f"Deleted export archive: {export_file}")
        except Exception as e:
            logger.error(f"Error deleting export {export_file}: {e}")
            
    db.delete(job)
    db.commit()
    return {"status": "success", "message": f"Job {job_id} and all related files deleted successfully"}

def create_dataset_archive(job_id: str, query: str, images: list[models.ScrapedImage], export_zip_path: str):
    """Background helper to create dataset zip archive containing images, JSON and CSV metadata."""
    os.makedirs(os.path.dirname(export_zip_path), exist_ok=True)
    
    import json
    import csv
    
    # Build metadata structures
    metadata_list = []
    for img in images:
        metadata_list.append({
            "id": img.id,
            "url": img.url,
            "sha256": img.sha256,
            "file_size_bytes": img.file_size,
            "width": img.width,
            "height": img.height,
            "filename": os.path.basename(img.local_path)
        })
        
    # Write temporary metadata files inside storage
    temp_dir = config.STORAGE_DIR / "temp" / job_id
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    json_path = temp_dir / "dataset_metadata.json"
    with open(json_path, "w") as f:
        json.dump({"query": query, "total_images": len(images), "images": metadata_list}, f, indent=4)
        
    csv_path = temp_dir / "dataset_metadata.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["image_id", "url", "sha256", "file_size_bytes", "width", "height", "filename"])
        for img in metadata_list:
            writer.writerow([
                img["id"], img["url"], img["sha256"], img["file_size_bytes"],
                img["width"], img["height"], img["filename"]
            ])

    # Package files into zip
    with zipfile.ZipFile(export_zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        # Add metadata
        z.write(json_path, "dataset_metadata.json")
        z.write(csv_path, "dataset_metadata.csv")
        
        # Add images
        for img in images:
            img_path = img.local_path
            if os.path.exists(img_path):
                # Put in images/ subfolder inside zip
                z.write(img_path, f"images/{os.path.basename(img_path)}")
                
    # Clean up temp files
    try:
        shutil.rmtree(temp_dir)
    except Exception as e:
        logger.error(f"Error cleaning up temp export directory: {e}")
    logger.info(f"Created export zip dataset archive at: {export_zip_path}")

@app.get("/api/v1/jobs/{job_id}/export")
async def export_job_dataset(job_id: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    job = db.query(models.Job).filter(models.Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.status != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Cannot export dataset for job in '{job.status}' status. Job must be 'completed'."
        )
        
    images = job.images
    if not images:
        raise HTTPException(status_code=404, detail="No scraped images found for this job")
        
    export_dir = config.STORAGE_DIR / "exports"
    export_zip_path = export_dir / f"{job_id}.zip"
    
    # If zip doesn't exist, create it synchronously or add as background task.
    # To be safe and quick, if it exists we return, else we generate it.
    if not export_zip_path.exists():
        logger.info(f"Generating export archive for job {job_id}...")
        create_dataset_archive(job_id, job.query, images, str(export_zip_path))
        
    return FileResponse(
        path=export_zip_path,
        media_type="application/zip",
        filename=f"dataset_{job.query.replace(' ', '_')}_{job_id[:8]}.zip"
    )
