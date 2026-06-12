import datetime
import uuid
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from backend.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class Job(Base):
    __tablename__ = "jobs"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    query = Column(String, nullable=False)
    limit = Column(Integer, default=100)
    engine = Column(String, default="bing")  # google, bing, generic
    status = Column(String, default="pending", index=True)  # pending, running, completed, failed
    total_scraped = Column(Integer, default=0)
    total_downloaded = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    images = relationship("ScrapedImage", back_populates="job", cascade="all, delete-orphan")

class ScrapedImage(Base):
    __tablename__ = "scraped_images"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    job_id = Column(String, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    url = Column(String, nullable=False)
    local_path = Column(String, nullable=False)
    sha256 = Column(String, nullable=False, index=True)
    file_size = Column(Integer, nullable=False)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    job = relationship("Job", back_populates="images")
