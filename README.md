# DZscraper – Serverless Bing Image Scraper

DZscraper is a serverless, production-ready Chrome Extension (Manifest V3) designed to build machine learning-ready datasets by extracting, filtering, and downloading images directly from Bing Images.

Since the extension runs entirely client-side, it requires **no backend servers, APIs, databases, or container services**. All scraping, content filtering, and ZIP archive packaging happen locally inside your browser.

---

## Architecture Overview

```
Chrome Extension (Serverless)
    │
    ├── Popup UI (Keyword & Limit Entry)
    │     │
    │     ▼ (Sends runtime message)
    │
    ├── Background Service Worker (background.js)
    │     │
    │     ├── Spawns Bing Images tab in background (active: false)
    │     ├── Injects scraper.js into the tab
    │     │
    │     ▼
    │
    ├── Scraper Script (scraper.js)
    │     │
    │     ├── Scrolls page & clicks Bing "Load More" (.btn_seemore)
    │     └── Extracts unique image URLs from anchors (a.iusc)
    │
    ├── Image Fetcher & Filter (Fetch API + createImageBitmap)
    │     │
    │     ├── Downloads images in parallel
    │     ├── Filters by size (>= 250px), aspect ratio (0.45 to 2.2), & URL keyword
    │     └── Compiles ZIP archive locally in memory using JSZip
    │
    └── Download Handler (download.html + chrome.downloads)
          │
          └── Prompts user to save the completed dataset.zip locally
```

---

## Features

- **100% Serverless**: No FastAPI, SQLite, Redis, Celery, or Docker required. Runs entirely on your browser using standard Extension APIs.
- **Dynamic Scroll & Scrape**: Injected script automatically scrolls Bing Images, handles pagination, clicks "Show More" buttons, and extracts high-resolution URLs.
- **ML-Ready Content Filtering Heuristics**:
  - **Resolution Filter**: Automatically drops small images, icons, and social avatars (requires `width >= 250px` and `height >= 250px`).
  - **Aspect Ratio Filter**: Discards banners, headers, dividers, and tall stripes (requires `0.45 <= width/height <= 2.2`).
  - **Keyword Exclusions**: Automatically excludes site logos, web headers, footer graphics, LinkedIn profile pics, Alibaba ads, and SlideShare presentation slides.
- **Local ZIP Exporter**: Compiles image files locally in memory alongside CSV and JSON metadata containing source URLs and size statistics using `JSZip`.
- **Storage Persistence**: Saves scraping history and jobs locally using `chrome.storage.local`. Includes a utility to clear storage.
- **Compact UI**: Sleek, off-white high-contrast theme layout with black borders, progress bars, and dataset actions.

---

## 🧩 Installing the Extension

1. Clone or download this repository.
2. Open Google Chrome.
3. Navigate to `chrome://extensions/`.
4. Enable **Developer mode** (toggle in the top-right corner).
5. Click **Load unpacked** (top-left corner).
6. Select the `extension/` folder inside this project directory.
7. Open the extension from your browser toolbar!

---

## 📦 Packaging for Chrome Web Store

The project includes a lightweight utility script `package.py` to bundle the extension files for CWS publication.

To pack the extension:
```bash
python package.py
```

This generates a publication-ready ZIP bundle `image_scraper_pro_extension.zip` in the root folder. You can upload this zip file directly to the [Chrome Developer Dashboard](https://chrome.google.com/webstore/devconsole).

For Web Store submission details and justifications, see [STORE_LISTING.md](STORE_LISTING.md).

---

## 📂 Project Structure

```
├── extension/
│   ├── manifest.json     # Chrome Extension Manifest V3 metadata
│   ├── popup.html        # Extension UI layout
│   ├── popup.js          # Main popup UI state and event listeners
│   ├── style.css         # Minimalist high-contrast variable stylesheet
│   ├── background.js     # Service worker managing tabs, fetches, & JSZip
│   ├── scraper.js        # Content script injected into Bing pages to scroll & extract
│   ├── download.html     # Helper download tab interface
│   ├── download.js       # Downloads the locally generated ZIP archive
│   ├── lib/
│   │   └── jszip.min.js  # JSZip library (v3.10.1)
│   └── icons/            # Chrome Web Store compliant icons (16, 48, 128)
│       ├── icon16.png
│       ├── icon48.png
│       ├── icon128.png
│       ├── settings.png
│       ├── completed.png
│       ├── failed.png
│       ├── delete_zip_file.png
│       └── refresh.png
├── package.py            # Packages the extension directory
└── README.md             # Project documentation
```
