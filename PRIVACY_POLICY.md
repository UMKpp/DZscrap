# Privacy Policy

**Effective Date: June 19, 2026**

This Privacy Policy explains how **DZscraper** ("the Extension") handles data when you install and use it. 

We take user privacy extremely seriously. The Extension is designed to operate as a local tool under your control.

---

### 1. No Collection of Personal Information
The Extension **does not collect, store, or transmit** any personal data, credentials, browsing activity, or telemetry. No tracking mechanisms, cookies, or analytics are embedded in the code.

### 2. Local-Only Storage
The Extension utilizes the following APIs for local storage under your control:
* **chrome.storage.local API**: Retains job history metadata (lists of past queries, limits, and job statuses).
* **IndexedDB Store**: Retains temporary ZIP archive data in the browser's local sandbox to support file download.
* **Clear Action**: A button is provided inside Settings to completely clear all history logs and cached ZIP data from both storage systems.

### 3. Outgoing Connections
The Extension only communicates directly with:
* **Bing Images**: To load search results in a background tab.
* **Image Source Hosts**: To download the raw image bytes for compilation.
* **No data** is ever sent to developer-controlled remote servers, third-party analytics trackers, or external marketing platforms.

### 4. Third-Party Services
When downloading images from Bing or external hosts, you are connecting directly to those third-party websites. Their privacy policies and terms of service govern those connections.

### 5. Policy Compliance
The Extension complies fully with the **Chrome Web Store User Data Policy**, including the principles of minimal permissions usage and single-purpose extension design.

---

### Contact & Support
For any questions regarding this policy or the extension source code, please review the repository files.
