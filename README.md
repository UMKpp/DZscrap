# Image Scraper Pro – Chrome Extension + Distributed Image Scraping System

Image Scraper Pro is a production-ready, distributed, scalable image scraping system designed to extract and download 1000+ images from Bing, Google, or generic URLs for machine learning dataset creation. 

The system leverages a FastAPI backend, Celery workers running Scrapy + Playwright for dynamic scroll scraping, and a modern Manifest V3 Chrome Extension dashboard.

---

## Architecture Overview

```
Chrome Extension (Frontend)
    │   (Sends Search Query & Limit via REST API)
    ▼
FastAPI Backend (localhost:8000) ────► DB State (SQLite / WAL Mode)
    │   (Creates job and dispatches task)
    ▼
Redis Broker (Port 6379)
    │   (Task picked up by worker)
    ▼
Celery Worker ────► Spawns Scrapy + Playwright Subprocess
                        │   (Dynamic scroll page & extracts high-res URLs)
                        ├──► Downloads images asynchronously
                        ├──► Computes SHA256 hashes to deduplicate globally & locally
                        └──► Writes images to storage/ and updates DB progress
```

---

## Features

- **Distributed Scraping Engine**: Celery + Redis coordinates jobs, keeping backend responsive.
- **Dynamic Scrolling**: Scrapy + Playwright scrolls dynamically and handles "Load More" pagination to scrape 1000+ images.
- **Clean ML-Ready Datasets**:
  - Global and job-level **SHA256 duplicate removal** (saves duplicate file downloads).
  - ZIP dataset exporter generating metadata in both **JSON** and **CSV** alongside clean images.
- **Chrome Extension Frontend**: Glassmorphism dashboard with job listing, real-time progress polling, and direct ZIP exports.

---

## 🛠️ Setup & Running via Docker (Recommended)

The easiest way to run the entire stack (Redis, Backend, and Celery + Playwright Worker) is using Docker Compose.

### 1. Prerequisites
- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)

### 2. Start the Stack
Run the following command in the project root:
```bash
docker-compose up --build
```
This automatically compiles the backend, pulls the Redis container, and builds the Celery worker container (which installs the required Playwright Chromium browsers and Linux dependencies).

- **FastAPI API Server**: http://localhost:8000
- **API Health Check**: http://localhost:8000/health
- **Static Storage File Server**: http://localhost:8000/storage

---

## 🐍 Setup & Running Locally (Python)

If you prefer to run services manually on your host machine:

### 1. Start Redis
Ensure you have Redis running locally.
- **Mac (Homebrew)**: `brew services start redis`
- **Ubuntu**: `sudo systemctl start redis-server`
- **Windows**: Run Redis via WSL or download Redis MSI.

### 2. Configure Virtual Environment & Install Dependencies
```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install requirements
pip install -r requirements.txt

# Install Playwright Chromium browser and its libraries
playwright install chromium
```

### 3. Run FastAPI Backend
```bash
# From project root
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. Run Celery Worker
In a new terminal window (with virtual environment activated):
```bash
# From project root
celery -A worker.celery_app.celery_app worker --loglevel=info
```

---

## 🧩 Installing the Chrome Extension

1. Open Google Chrome.
2. Navigate to `chrome://extensions/`.
3. Enable **Developer mode** (toggle in the top-right corner).
4. Click **Load unpacked** (top-left corner).
5. Select the `extension/` folder inside this project directory.
6. Click the extension icon in your browser to open the Glassmorphism dashboard!

*Note: By default, the extension points to `http://localhost:8000`. You can configure this by clicking the **Settings Gear (⚙️)** in the top right of the popup.*

---

## 📂 Project Structure

```
├── backend/
│   ├── database.py       # SQLAlchemy SQLite Setup (WAL Mode)
│   ├── models.py         # SQLAlchemy Database models (Jobs & Images)
│   ├── schemas.py        # Pydantic validation schemas
│   ├── config.py         # Environment configurations
│   └── main.py           # FastAPI endpoints & Zip exporter
├── worker/
│   ├── celery_app.py     # Celery App configurations
│   └── tasks.py          # Worker task invoking Scrapy
├── scraper/
│   ├── scrapy.cfg        # Scrapy config
│   └── scraper/
│       ├── items.py      # Item schema
│       ├── settings.py   # Scrapy settings with Playwright Launch configuration
│       ├── middlewares.py# Random User Agent rotation
│       ├── pipelines.py  # Asynchronous HTTP downloader, SHA256 check, and SQLite database writer
│       └── spiders/
│           └── image_spider.py # Dynamic dynamic scroll spider for Google, Bing, and Generic sites
├── extension/
│   ├── manifest.json     # Chrome Extension Manifest V3
│   ├── popup.html        # Extension UI layout
│   ├── style.css         # Glassmorphism dark-theme styling
│   └── popup.js          # REST Client and polling controller
├── storage/              # Local storage for images and db.sqlite3
├── logs/                 # Log directories for worker & api
├── docker/
│   ├── backend.Dockerfile
│   └── worker.Dockerfile
├── docker-compose.yml    # Runs Redis, FastAPI, Celery
└── requirements.txt      # Main project dependencies
```

---

## 📡 REST API Documentation

### 1. Health Check
- **URL**: `GET /health`
- **Response**: `{"status": "ok", "message": "Image Scraper Pro API is running"}`

### 2. Start Scraping
- **URL**: `POST /api/v1/scrape`
- **Body**:
  ```json
  {
    "query": "red sports cars",
    "limit": 100,
    "engine": "bing"
  }
  ```
- **Response**: Returns Job metadata with ID, query, limits, and status (`pending`).

### 3. List Jobs
- **URL**: `GET /api/v1/jobs`
- **Response**: List of all scraping jobs.

### 4. Job Details
- **URL**: `GET /api/v1/jobs/{job_id}`
- **Response**: Details of the job including status (`pending`, `running`, `completed`, `failed`), and total scraped image counts.

### 5. Job Results
- **URL**: `GET /api/v1/jobs/{job_id}/results`
- **Response**: List of image files scraped (urls, local path, sha256 hash, width, height, etc.).

### 6. Export Dataset (Zip)
- **URL**: `GET /api/v1/jobs/{job_id}/export`
- **Response**: Serves a ZIP archive named `dataset_{query}_{job_id}.zip` containing:
  - `images/` directory containing all deduplicated images named by their SHA256 hashes.
  - `dataset_metadata.json` containing query metadata and image records.
  - `dataset_metadata.csv` containing dataset logs ready to load into pandas or ML frameworks.

### 7. Delete Job
- **URL**: `DELETE /api/v1/jobs/{job_id}`
- **Response**: Cleans up image files from disk, deletes export archives, and deletes database tables metadata records.
