import os
import sys
import unittest
from pathlib import Path

# Add project root to python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend import models, config, schemas
from backend.database import engine, SessionLocal

class TestImageScraperPro(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        # Setup temporary sqlite database for tests
        cls.test_db_path = config.STORAGE_DIR / "test_db.sqlite3"
        config.DATABASE_URL = f"sqlite:///{cls.test_db_path}"
        models.Base.metadata.create_all(bind=engine)
        cls.db = SessionLocal()

    @classmethod
    def tearDownClass(cls):
        cls.db.close()
        # Clean up test database
        if cls.test_db_path.exists():
            os.remove(cls.test_db_path)

    def test_database_creation(self):
        # Create a job
        job = models.Job(
            query="test kittens",
            limit=50,
            engine="bing",
            status="pending"
        )
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)

        self.assertIsNotNone(job.id)
        self.assertEqual(job.query, "test kittens")
        self.assertEqual(job.limit, 50)
        self.assertEqual(job.status, "pending")

        # Create a scraped image
        img = models.ScrapedImage(
            job_id=job.id,
            url="https://example.com/kitty.jpg",
            local_path="/app/storage/images/test_job/abc.jpg",
            sha256="abc123sha256",
            file_size=1024,
            width=640,
            height=480
        )
        self.db.add(img)
        self.db.commit()
        self.db.refresh(img)

        self.assertIsNotNone(img.id)
        self.assertEqual(img.job_id, job.id)
        self.assertEqual(img.sha256, "abc123sha256")
        self.assertEqual(len(job.images), 1)

    def test_schemas(self):
        # Validate Pydantic schema JobCreate
        payload = {"query": "pandas", "limit": 200, "engine": "google"}
        schema = schemas.JobCreate(**payload)
        self.assertEqual(schema.query, "pandas")
        self.assertEqual(schema.limit, 200)
        self.assertEqual(schema.engine, "google")

if __name__ == "__main__":
    unittest.main()
