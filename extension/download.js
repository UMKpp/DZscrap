(async function() {
  const urlParams = new URLSearchParams(window.location.search);
  const jobId = urlParams.get("job_id");
  const filename = urlParams.get("filename") || "dataset.zip";
  
  if (!jobId) {
    console.error("No job ID provided for download.");
    window.close();
    return;
  }
  
  try {
    const zipData = await DZDB.getZip(jobId);
    if (zipData) {
      const blob = new Blob([zipData], { type: "application/zip" });
      const url = URL.createObjectURL(blob);
      
      chrome.downloads.download({
        url: url,
        filename: filename,
        saveAs: false
      }, () => {
        URL.revokeObjectURL(url);
        // Close download tab immediately
        chrome.tabs.getCurrent(tab => {
          if (tab) chrome.tabs.remove(tab.id);
        });
      });
    } else {
      console.error("Failed to retrieve zip data from IndexedDB.");
      window.close();
    }
  } catch (err) {
    console.error("Error retrieving zip from IndexedDB:", err);
    window.close();
  }
})();
