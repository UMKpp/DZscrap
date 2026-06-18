# DZscraper - Extension Publishing and Distribution Guide

DZscraper is a fully serverless, client-side Chrome Extension. This guide details how to build, test, package, and publish the extension for local distribution or for the Chrome Web Store.

---

## Local Development & Testing

To load and run the extension locally for testing:

1. Open Google Chrome.
2. Navigate to `chrome://extensions/`.
3. Enable **Developer mode** in the top-right corner.
4. Click **Load unpacked** in the top-left corner.
5. Select the `extension/` folder inside your repository.
6. The extension is now loaded and available in your browser toolbar under the name **DZscraper - Dataset Builder**.

---

## Local Packaging

To package the extension into a ZIP file for manual sharing or publication:

1. Run the packaging script in the root directory:
   ```bash
   python package.py
   ```
2. The script compiles and creates `image_scraper_pro_extension.zip` in the root workspace folder, containing only the required manifest, code files, JSZip library, and icons.

---

## Chrome Web Store Publishing Guide

### 1. Developer Console Registration
1. Visit the [Chrome Web Store Developer Console](https://chrome.google.com/webstore/devconsole).
2. Sign in with a Google Account.
3. Pay the one-time developer registration fee if you haven't already.

### 2. Upload the Package
1. In the console, click **New Item**.
2. Click **Upload ZIP File** and select `image_scraper_pro_extension.zip`.
3. The dashboard will automatically parse the `manifest.json` and create a draft store item.

### 3. Permissions and Privacy Justifications
Chrome Web Store requires details on why permissions are requested:

- **`storage`**: Used to save the user's scraping jobs list and status local history.
- **`unlimitedStorage`**: Required to allow saving large local datasets (ZIP archives) in memory/storage before downloading them.
- **`scripting`**: Required to inject `scraper.js` into Bing search pages to execute dynamic scrolling and collect URLs.
- **`tabs`**: Used to open the background Bing search tab and automatically close it once scraping is completed.
- **`downloads`**: Required to invoke the browser's download manager to save the generated dataset ZIP files locally.
- **Host Permissions (`<all_urls>`)**: Required to query and download image bytes from arbitrary third-party image hosts (e.g. Dreamstime, Epic Gardening) where Bing search result images are stored.

### 4. Privacy Policy Requirement
Because the extension uses `<all_urls>` host permissions, you must submit a link to your **Privacy Policy**. You can use the template available in [PRIVACY_POLICY.md](PRIVACY_POLICY.md). 

Ensure you emphasize that:
- All data stays locally inside the browser.
- No network requests are sent to external analytics or tracking servers.
- The scraper runs 100% serverless with zero data collection.
