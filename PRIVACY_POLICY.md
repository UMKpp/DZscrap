# Privacy Policy

**Effective Date: June 12, 2026**

This Privacy Policy explains how **Image Scraper Pro Client** ("the Extension") handles data when you install and use it. 

We take user privacy extremely seriously. The Extension is designed to operate as a local tool under your control.

---

### 1. No Collection of Personal Information
The Extension **does not collect, store, or transmit** any personal data, credentials, browsing activity, or telemetry. No tracking mechanisms, cookies, or analytics are embedded in the code.

### 2. Local-Only Storage
The Extension utilizes the `chrome.storage.local` API for the sole purpose of retaining your configuration settings:
* **Saved Backend URL**: The API server endpoint address (default: `http://localhost:8000`) is saved locally on your browser to maintain connectivity.
* No job histories, scraped image metadata, or downloaded files are stored within the extension itself.

### 3. Outgoing Connections
The Extension only communicates with the **FastAPI Backend URL** that you explicitly specify:
* Communication is strictly restricted to sending scraping requests and fetching job status updates.
* By default, this traffic is directed to your local machine (`http://localhost:8000` or `http://127.0.0.1:8000`).
* **No data** is ever sent to developer-controlled remote servers, third-party analytics trackers, or external marketing platforms.

### 4. Third-Party Services
The Extension operates in conjunction with your self-hosted backend system. The backend may make requests to public domains (like Bing) to collect images. These backend operations are governed by your own hosting configurations and are not controlled by this Extension.

### 5. Policy Compliance
The Extension complies fully with the **Chrome Web Store User Data Policy**, including the principles of minimal permissions usage and single-purpose extension design.

---

### Contact & Support
For any questions regarding this policy or the extension source code, please review the repository files or contact the administrator of your self-hosted instance.
