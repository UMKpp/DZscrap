// DZscraper IndexedDB Utility
// Handles local storage of raw binary ZIP archives without JSON serialization limits.
const DZDB = {
  dbName: "DZscraperDB",
  storeName: "zips",
  version: 1,

  sanitizeJob(job) {
    if (!job || typeof job !== "object") return null;
    
    const safeJob = {};
    const fields = [
      { key: "id", type: "string", default: "" },
      { key: "query", type: "string", default: "" },
      { key: "limit", type: "number", default: 100 },
      { key: "engine", type: "string", default: "bing" },
      { key: "status", type: "string", default: "pending" },
      { key: "total_scraped", type: "number", default: 0 },
      { key: "total_downloaded", type: "number", default: 0 },
      { key: "created_at", type: "string", default: () => new Date().toISOString() },
      { key: "updated_at", type: "string", default: () => new Date().toISOString() },
      { key: "error_message", type: "string_or_null", default: null }
    ];

    for (const field of fields) {
      const val = job[field.key];
      if (field.type === "string") {
        safeJob[field.key] = typeof val === "string" ? val : (val !== undefined && val !== null ? String(val) : (typeof field.default === "function" ? field.default() : field.default));
      } else if (field.type === "number") {
        safeJob[field.key] = typeof val === "number" ? val : (val !== undefined && val !== null ? (parseInt(val, 10) || 0) : field.default);
      } else if (field.type === "string_or_null") {
        safeJob[field.key] = (val === null || val === undefined) ? null : String(val);
      }
    }
    return safeJob;
  },

  open() {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(this.dbName, this.version);
      request.onerror = () => reject(request.error);
      request.onsuccess = () => resolve(request.result);
      request.onupgradeneeded = (e) => {
        const db = e.target.result;
        if (!db.objectStoreNames.contains(this.storeName)) {
          db.createObjectStore(this.storeName);
        }
      };
    });
  },

  async saveZip(jobId, arrayBuffer) {
    const db = await this.open();
    return new Promise((resolve, reject) => {
      const tx = db.transaction(this.storeName, "readwrite");
      const store = tx.objectStore(this.storeName);
      const request = store.put(arrayBuffer, jobId);
      request.onsuccess = () => resolve();
      request.onerror = () => reject(request.error);
    });
  },

  async getZip(jobId) {
    const db = await this.open();
    return new Promise((resolve, reject) => {
      const tx = db.transaction(this.storeName, "readonly");
      const store = tx.objectStore(this.storeName);
      const request = store.get(jobId);
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
  },

  async deleteZip(jobId) {
    const db = await this.open();
    return new Promise((resolve, reject) => {
      const tx = db.transaction(this.storeName, "readwrite");
      const store = tx.objectStore(this.storeName);
      const request = store.delete(jobId);
      request.onsuccess = () => resolve();
      request.onerror = () => reject(request.error);
    });
  },

  async clearAllZips() {
    const db = await this.open();
    return new Promise((resolve, reject) => {
      const tx = db.transaction(this.storeName, "readwrite");
      const store = tx.objectStore(this.storeName);
      const request = store.clear();
      request.onsuccess = () => resolve();
      request.onerror = () => reject(request.error);
    });
  }
};
