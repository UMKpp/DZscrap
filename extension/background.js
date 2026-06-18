// DZscraper MV3 Background Service Worker
importScripts("lib/db.js", "lib/jszip.min.js");

const tabIdMap = {};

// Helper to generate unique job IDs
function generateJobId() {
  return "job_" + Date.now() + "_" + Math.random().toString(36).substr(2, 9);
}

// Convert ArrayBuffer to Base64 string for storage
function arrayBufferToBase64(buffer) {
  const bytes = new Uint8Array(buffer);
  let binary = "";
  const len = bytes.byteLength;
  const chunk = 8192;
  for (let i = 0; i < len; i += chunk) {
    binary += String.fromCharCode.apply(null, bytes.subarray(i, i + chunk));
  }
  return btoa(binary);
}

// Helper to update job status in storage
async function updateJobInStorage(jobId, updateFields) {
  const data = await chrome.storage.local.get("jobs");
  let jobs = data.jobs || [];
  
  jobs = jobs.map(job => {
    if (job.id === jobId) {
      const updatedJob = {
        ...job,
        ...updateFields,
        updated_at: new Date().toISOString()
      };
      return DZDB.sanitizeJob(updatedJob);
    }
    return DZDB.sanitizeJob(job);
  }).filter(Boolean);
  
  await chrome.storage.local.set({ jobs });
  return jobs;
}

// Fetch image blob with timeout and error handling
async function fetchImageBlob(url) {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 10000); // 10s timeout
  
  try {
    const response = await fetch(url, {
      signal: controller.signal,
      headers: {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
      }
    });
    clearTimeout(timeoutId);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return await response.blob();
  } catch (err) {
    clearTimeout(timeoutId);
    throw err;
  }
}

// Validate image using size, format, aspect ratio, and keyword rules
async function validateImageBlob(blob, url) {
  if (blob.size < 1024) {
    throw new Error("Image size too small (< 1KB)");
  }
  
  const urlLower = url.toLowerCase();
  const excludeKeywords = [
    "/logo.", "/logo/", "/logo_", "avatar", "icon", "banner", "header", "footer", 
    "profile-displayphoto", "linkedin", "licdn.com", "doubleclick", "adsystem", 
    "adsense", "/ad-", "/ads-", "promotional", "sponsored", "slideshare", "csdnimg"
  ];
  for (let kw of excludeKeywords) {
    if (urlLower.includes(kw)) {
      throw new Error(`Excluded URL pattern matches '${kw}'`);
    }
  }
  
  try {
    const bitmap = await createImageBitmap(blob);
    const w = bitmap.width;
    const h = bitmap.height;
    bitmap.close();
    
    if (w < 250 || h < 250) {
      throw new Error(`Image resolution too low (${w}x${h})`);
    }
    
    const aspect = w / h;
    if (aspect > 2.2 || aspect < 0.45) {
      throw new Error(`Unusual aspect ratio typical of banner/header (${aspect.toFixed(2)})`);
    }
    
    return true;
  } catch (err) {
    throw new Error(`Failed to parse image dimensions: ${err.message}`);
  }
}

// Handles downloading the list of image URLs, zipping them, and triggering download
async function processDownloads(jobId, query, urls, limit) {
  console.log(`[DZscraper] Downloading results for job ${jobId}. Limit: ${limit}. Total URLs: ${urls.length}`);
  
  await updateJobInStorage(jobId, { status: "downloading" });
  
  const zip = new JSZip();
  let downloadedCount = 0;
  
  // Package images folders
  const imgFolder = zip.folder("images");
  
  // Create metadata files
  const metadataList = [];
  
  // Download in parallel with concurrency chunks of 10
  const chunkSize = 10;
  for (let i = 0; i < urls.length && downloadedCount < limit; i += chunkSize) {
    const chunk = urls.slice(i, i + chunkSize);
    
    const promises = chunk.map(async (url, idx) => {
      if (downloadedCount >= limit) return;
      
      try {
        const blob = await fetchImageBlob(url);
        await validateImageBlob(blob, url);
        
        // Determine file extension from type or URL
        let ext = "jpg";
        if (blob.type.includes("png")) ext = "png";
        else if (blob.type.includes("webp")) ext = "webp";
        else if (blob.type.includes("gif")) ext = "gif";
        
        // Hash filename using simple checksum to prevent overlap
        const filename = `img_${downloadedCount + 1}_${Math.random().toString(36).substr(2, 5)}.${ext}`;
        
        const arrayBuffer = await blob.arrayBuffer();
        imgFolder.file(filename, arrayBuffer);
        
        metadataList.push({
          id: downloadedCount + 1,
          url: url,
          filename: filename,
          file_size_bytes: blob.size
        });
        
        downloadedCount++;
        
        // Update stats
        await updateJobInStorage(jobId, {
          total_downloaded: downloadedCount
        });
      } catch (err) {
        console.warn(`[DZscraper] Skipped image download from ${url}: ${err.message}`);
      }
    });
    
    await Promise.all(promises);
  }
  
  if (downloadedCount === 0) {
    console.error("[DZscraper] No images were successfully downloaded.");
    await updateJobInStorage(jobId, {
      status: "failed",
      error_message: "No images were successfully downloaded (all failed validation or size filters)."
    });
    return;
  }
  
  // Add CSV & JSON metadata to ZIP
  // JSON metadata
  const jsonContent = JSON.stringify({
    query,
    total_images: downloadedCount,
    images: metadataList
  }, null, 2);
  zip.file("dataset_metadata.json", jsonContent);
  
  // CSV metadata
  let csvContent = "image_id,url,filename,file_size_bytes\n";
  metadataList.forEach(m => {
    csvContent += `${m.id},"${m.url.replace(/"/g, '""')}",${m.filename},${m.file_size_bytes}\n`;
  });
  zip.file("dataset_metadata.csv", csvContent);
  
  try {
    // Generate Zip ArrayBuffer
    console.log("[DZscraper] Generating local ZIP archive...");
    const contentBuffer = await zip.generateAsync({ type: "arraybuffer" });
    
    // Save ZIP in IndexedDB (bypasses chrome.storage JSON serialization error and limits)
    await DZDB.saveZip(jobId, contentBuffer);
    
    // Mark completed
    await updateJobInStorage(jobId, {
      status: "completed",
      total_downloaded: downloadedCount
    });
    
    // Trigger download tab
    const cleanQuery = query.replace(/[^a-z0-9]/gi, "_").toLowerCase();
    const filename = `dataset_${cleanQuery}_${jobId.substr(-4)}.zip`;
    
    chrome.tabs.create({
      url: `download.html?job_id=${jobId}&filename=${encodeURIComponent(filename)}`,
      active: false
    });
  } catch (err) {
    console.error("[DZscraper] Error packing ZIP archive:", err);
    await updateJobInStorage(jobId, {
      status: "failed",
      error_message: `Failed to compile ZIP file: ${err.message}`
    });
  }
}

// Listen for runtime messages from popup, scraper, or download scripts
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === "start_scrape") {
    const { query, limit } = message;
    const jobId = generateJobId();
    
    const newJob = {
      id: jobId,
      query: query,
      limit: parseInt(limit) || 100,
      engine: "bing",
      status: "pending",
      total_scraped: 0,
      total_downloaded: 0,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      error_message: null
    };
    
    // Add job to storage list
    chrome.storage.local.get("jobs", async (data) => {
      const jobs = (data.jobs || []).map(j => DZDB.sanitizeJob(j)).filter(Boolean);
      const sanitizedNewJob = DZDB.sanitizeJob(newJob);
      jobs.unshift(sanitizedNewJob);
      
      // Save updated list and set as current active job configuration
      await chrome.storage.local.set({
        jobs: jobs,
        active_job: sanitizedNewJob
      });
      
      // Open Bing Images tab in background
      const bingUrl = `https://www.bing.com/images/search?q=${encodeURIComponent(query)}&form=HDRSC2`;
      chrome.tabs.create({ url: bingUrl, active: false }, (tab) => {
        tabIdMap[jobId] = tab.id;
        
        // Wait for page load completion before injecting scraper
        chrome.tabs.onUpdated.addListener(function listener(tabId, info) {
          if (tabId === tab.id && info.status === "complete") {
            chrome.tabs.onUpdated.removeListener(listener);
            chrome.scripting.executeScript({
              target: { tabId: tab.id },
              files: ["scraper.js"]
            });
          }
        });
      });
      
      sendResponse({ status: "success", job: newJob });
    });
    
    return true; // Keep message channel open for async response
  }
  
  else if (message.action === "scrape_progress") {
    const { job_id, urls } = message;
    updateJobInStorage(job_id, {
      status: "running",
      total_scraped: urls.length
    });
  }
  
  else if (message.action === "scrape_complete") {
    const { job_id, urls } = message;
    const tabId = tabIdMap[job_id];
    
    // Close background scraping tab
    if (tabId) {
      chrome.tabs.remove(tabId);
      delete tabIdMap[job_id];
    }
    
    // Get query and limit, and start downloading
    chrome.storage.local.get("jobs", (data) => {
      const jobs = data.jobs || [];
      const currentJob = jobs.find(j => j.id === job_id);
      if (currentJob) {
        processDownloads(job_id, currentJob.query, urls, currentJob.limit);
      }
    });
  }
});
