# Chrome Web Store - Listing Metadata

This document contains the text and configuration details required for submitting the extension to the Chrome Developer Dashboard.

---

### 1. General Info
* **Extension Name:** DZscraper - Dataset Builder
* **Version:** 2.0.0
* **Short Description (max 150 chars):** Serverless image scraper that extracts, filters, and downloads Bing Image datasets directly in your browser.
* **Category:** Productivity / Developer Tools
* **Language:** English (United States)

---

### 2. Full Description (max 16,000 chars)
```markdown
DZscraper is a serverless image scraping tool designed for developers, data scientists, and ML engineers. It allows you to build machine-learning-ready image datasets directly from your browser, completely offline with zero server dependencies.

No need to configure databases, Celery queues, Redis, or FastAPI servers. DZscraper does all the work directly in your browser.

**KEY FEATURES:**
* **Instant Scraping:** Simply enter a keyword and the number of images, then click "SCRAPE NOW" to start.
* **Automatic Tab Scrolling:** The extension opens Bing Images in the background, scrolls through results, handles pagination, and extracts image source URLs automatically.
* **Content Filtering Heuristics:** Automatically filters out small images (< 250px), banners/headers (aspect ratio checks), and site decorations/avatars/logos using integrated URL keyword checks and image dimension validation.
* **Local ZIP Generation:** Packages all successfully downloaded images, metadata in CSV format, and metadata in JSON format into a clean, structured ZIP file locally in your browser using JSZip.
* **Zero Server Overhead:** Zero third-party telemetry, tracking, or external API dependencies. All network fetches go directly from your browser to Bing and the image hosts.
* **Job History Persistence:** Keeps track of your active and historical datasets using the local browser storage.

**HOW TO USE:**
1. Load the extension in Google Chrome.
2. Enter your target keyword (e.g., "tomato leaf blight").
3. Set your desired image count limit.
4. Click "SCRAPE NOW".
5. Wait for the progress bar to complete and check your browser's download folder for the generated dataset ZIP file.
```

---

### 3. Permissions Justifications (Required during CWS submission)

#### Permission: `storage` & `unlimitedStorage`
* **Purpose:** Stores the local job logs and historical progress.
* **Justification:** Allows the extension to persist the jobs dashboard list and store the generated ZIP ArrayBuffers temporarily in browser memory across sessions.

#### Permission: `scripting`
* **Purpose:** Runs content script injection.
* **Justification:** The extension must inject the scrolling and extraction script (`scraper.js`) into the background Bing Image search tabs to collect image URLs.

#### Permission: `tabs`
* **Purpose:** Spawns and manages tabs.
* **Justification:** Required to load the search page in a background tab and close it automatically once scraping completes.

#### Permission: `downloads`
* **Purpose:** Triggers browser file download manager.
* **Justification:** Required to save the locally generated ZIP files onto the user's hard drive automatically.

#### Host Permissions (`<all_urls>`)
* **Purpose:** Permits cross-origin image download requests.
* **Justification:** Because Bing Image search results point to arbitrary external domains (e.g., Dreamstime, Wikipedia, seed websites), the extension must make `fetch()` requests to these diverse domains to download the raw image bytes for ZIP compilation.
