# DZscraper – Serverless Bing Image Scraper

DZscraper is a serverless Chrome Extension (Manifest V3) that helps you collect, filter, and download images from Bing Images for building machine learning datasets.

It runs entirely in your browser, so there are no backend servers, APIs, databases, or external services involved. Everything—scraping, filtering, and ZIP creation—happens locally.

## Architecture Overview

The extension works as a fully client-side pipeline inside Chrome:

```
Chrome Extension (Serverless)

Popup UI
→ Takes user input (search keyword + image limit)
→ Sends request to background script

Background Service Worker (background.js)
→ Opens Bing Images in a hidden tab
→ Injects scraper script into the page

Scraper Script (scraper.js)
→ Scrolls the page automatically
→ Clicks “Show More” when available
→ Extracts image URLs from Bing results

Image Processing Layer
→ Downloads images using Fetch API
→ Validates images using size + aspect ratio rules
→ Filters out irrelevant or low-quality images

ZIP Builder (JSZip)
→ Packs images + metadata into a ZIP file in memory

Download Handler
→ Lets the user download the final dataset locally
```

## Features

### Fully Serverless
No backend infrastructure needed. The extension runs completely inside Chrome using built-in browser APIs.

### Smart Scraping
* Automatically scrolls Bing Images
* Handles pagination and “Show More” buttons
* Extracts high-quality image URLs

### Dataset Quality Filtering
To keep datasets clean and useful for ML training:
* Removes small images (below 250×250)
* Filters extreme aspect ratios (keeps 0.45–2.2 range)
* Excludes logos, banners, ads, avatars, and irrelevant visuals

### Local ZIP Export
* Downloads images directly into a ZIP file
* Includes metadata (CSV + JSON with URLs and image details)
* Built entirely in memory using JSZip

### Local Storage Support
* Saves scraping history using Chrome storage
* Stores generated ZIP files using IndexedDB
* Includes tools to clear history and stored datasets

### Simple User Interface
A clean and minimal interface focused on usability, showing progress, status, and download actions.

---

## Installing the Extension

1. Download or clone the project
2. Open Chrome
3. Go to `chrome://extensions/`
4. Enable **Developer mode**
5. Click **Load unpacked**
6. Select the `extension/` folder
7. Open the extension from the toolbar

---

## Packaging for Chrome Web Store

A helper script is included to prepare the extension for publishing:

```bash
python package.py
```

This creates a ready-to-upload ZIP file:

`image_scraper_pro_extension.zip`

You can upload it directly to the Chrome Web Store Developer Dashboard.

For submission details, check `STORE_LISTING.md`.

---

## Project Structure

```
extension/
├── manifest.json        Chrome Extension configuration
├── popup.html           Main UI
├── popup.js             UI logic and events
├── style.css            Styling
├── background.js        Service worker (core logic)
├── scraper.js           Bing scraping logic
├── download.html        Download interface
├── download.js          ZIP download handler
├── lib/
│   ├── db.js            IndexedDB helper library
│   └── jszip.min.js     ZIP library
└── icons/               Extension icons

package.py               Packaging script
README.md                Documentation
```
