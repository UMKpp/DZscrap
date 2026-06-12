# Chrome Web Store - Listing Metadata

This document contains the text and configuration details required for submitting the extension to the Chrome Developer Dashboard.

---

### 1. General Info
* **Extension Name:** Image Scraper Pro Client
* **Version:** 1.0.0
* **Short Description (max 150 chars):** Connects to your local Image Scraper Pro server to queue scrape jobs and download datasets.
* **Category:** Productivity / Developer Tools
* **Language:** English (United States)

---

### 2. Full Description (max 16,000 chars)
```markdown
Image Scraper Pro Client is the official browser companion for your self-hosted Image Scraper Pro distributed scraping system. Designed for developers, data scientists, and ML engineers, this extension provides a visual dashboard to create and download image datasets directly from your browser.

**PREREQUISITE:**
This extension requires you to have the Image Scraper Pro backend server running on your machine (via Docker Compose or local python server). It will not function without the local API connection.

**KEY FEATURES:**
* **One-Click Queueing:** Start image scraping tasks on your local server directly from the extension panel.
* **Real-Time Progress Tracking:** Monitor active jobs, view exact image download metrics, and track completion progress bars in real-time.
* **Instant ZIP Downloads:** Export complete, cleaned, and machine-learning-ready ZIP datasets (containing raw files + metadata JSON) directly from your active jobs dashboard.
* **No Background Resources:** The extension has zero background workers, running only when you open the popup to minimize browser resource consumption.
* **Local & Private:** Zero third-party telemetry, tracking, or cloud uploads. All network requests go straight to your local server.

**HOW TO USE:**
1. Startup your local Image Scraper Pro Docker Compose environment.
2. Click the gear icon in the extension to set your local FastAPI backend URL (default: http://localhost:8000).
3. Enter your scraping keyword and target limit.
4. Click "Queue Scraping Job" to dispatch the crawl to your local worker.
5. Download your processed dataset ZIP as soon as the status indicates completed.
```

---

### 3. Permissions Justifications (Required during CWS submission)

#### Permission: `storage`
* **Purpose:** Stores the backend API Server URL locally.
* **Justification:** Allows the extension to remember the user's custom server URL (e.g., `http://localhost:8000`) across sessions so it doesn't need to be re-entered each time the popup is opened.

#### Permission: `host_permissions` (`http://localhost:8000/*`, `http://127.0.0.1:8000/*`)
* **Purpose:** Allows communication with the local backend APIs.
* **Justification:** The extension must make HTTP requests (`GET`/`POST`/`DELETE`) to check backend server health, fetch job logs, and start scraping tasks. Since the server runs locally on the host machine, these specific localhost patterns are required.
