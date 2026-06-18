(async function() {
  // Extract search query and job_id from storage/context
  const urlParams = new URLSearchParams(window.location.search);
  const query = urlParams.get("q");
  
  if (!query) {
    console.error("[DZscraper] No search query found in URL.");
    return;
  }
  
  console.log(`[DZscraper] Starting scraper for query: "${query}"`);
  
  // Get active job configuration from storage
  const data = await chrome.storage.local.get("active_job");
  const activeJob = data.active_job;
  if (!activeJob || activeJob.query !== query) {
    console.error("[DZscraper] No matching active job config found in storage.");
    return;
  }
  
  const jobId = activeJob.id;
  const limit = activeJob.limit || 100;
  
  // Scraper extraction logic for Bing
  function extractBingUrls() {
    const urls = [];
    const anchors = document.querySelectorAll("a.iusc");
    anchors.forEach(a => {
      try {
        const mStr = a.getAttribute("m");
        if (mStr) {
          const mData = JSON.parse(mStr);
          const murl = mData.murl;
          if (murl && murl.startsWith("http")) {
            urls.push(murl);
          }
        }
      } catch (e) {
        // Skip invalid metadata
      }
    });
    // Deduplicate
    return [...new Set(urls)];
  }
  
  // Scroll and click "load more" loop
  let scrollAttempts = 0;
  const maxScrolls = 40;
  let lastCount = 0;
  let consecutiveNoNew = 0;
  
  // We target 1.33x of requested limit to compensate for download drops/duplicates
  const targetCount = Math.max(limit * 4 / 3, limit + 10);
  
  while (scrollAttempts < maxScrolls) {
    window.scrollTo(0, document.body.scrollHeight);
    
    // Wait for content loading
    await new Promise(resolve => setTimeout(resolve, 800));
    
    // Click Bing "Show more results" button if visible
    const btn = document.querySelector(".btn_seemore, a.mye");
    if (btn && (btn.offsetWidth > 0 || btn.offsetHeight > 0)) {
      console.log("[DZscraper] Clicking load-more button...");
      btn.click();
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
    
    const currentUrls = extractBingUrls();
    const currentCount = currentUrls.length;
    console.log(`[DZscraper] Scroll ${scrollAttempts + 1}: Found ${currentCount} URLs (Target: ${targetCount})`);
    
    // Send progress update
    chrome.runtime.sendMessage({
      action: "scrape_progress",
      job_id: jobId,
      urls: currentUrls
    });
    
    if (currentCount >= targetCount) {
      console.log("[DZscraper] Target count reached.");
      break;
    }
    
    if (currentCount === lastCount) {
      consecutiveNoNew++;
      if (consecutiveNoNew >= 4) {
        console.log("[DZscraper] No new images found in last 4 scrolls. Stopping.");
        break;
      }
    } else {
      consecutiveNoNew = 0;
    }
    
    lastCount = currentCount;
    scrollAttempts++;
  }
  
  const finalUrls = extractBingUrls();
  console.log(`[DZscraper] Scraping completed. Found ${finalUrls.length} total unique URLs.`);
  
  // Send completion message
  chrome.runtime.sendMessage({
    action: "scrape_complete",
    job_id: jobId,
    urls: finalUrls
  });
})();
