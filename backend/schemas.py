from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

class JobCreate(BaseModel):
    query: str = Field(..., min_length=1, description="Search keyword or generic URL to scrape")
    limit: int = Field(100, ge=1, le=2000, description="Max number of images to scrape")
    engine: str = Field("bing", description="Scraping engine: 'google', 'bing', or 'generic'")

class ScrapedImageResponse(BaseModel):
    id: str
    job_id: str
    url: str
    local_path: str
    sha256: str
    file_size: int
    width: Optional[int] = None
    height: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True

class JobResponse(BaseModel):
    id: str
    query: str
    limit: int
    engine: str
    status: str
    total_scraped: int
    total_downloaded: int
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class JobDetailResponse(JobResponse):
    images: List[ScrapedImageResponse] = []

    class Config:
        from_attributes = True
