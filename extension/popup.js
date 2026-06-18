/**
 * DZscraper Client - popup.js
 * Coordinates UI events, storage loads, job requests, and polling
 * entirely client-side using Chrome Storage and Service Worker.
 */
document.addEventListener("DOMContentLoaded", () => {
  let activePollInterval = null;

  // DOM Elements
  const btnSettings = document.getElementById("btn-settings");
  const settingsPane = document.getElementById("settings-pane");
  const btnClearHistory = document.getElementById("btn-clear-history");
  const btnSaveSettings = document.getElementById("btn-save-settings");

  const scrapingFormCard = document.getElementById("scraping-form-card");
  const jobsSection = document.getElementById("jobs-section");
  const inputQuery = document.getElementById("input-query");
  const selectEngine = document.getElementById("select-engine");
  const inputLimit = document.getElementById("input-limit");
  const btnStartScrape = document.getElementById("btn-start-scrape");

  const btnRefreshJobs = document.getElementById("btn-refresh-jobs");
  const jobsList = document.getElementById("jobs-list");

  const connectionDot = document.getElementById("connection-dot");
  const connectionText = document.getElementById("connection-text");

  // Initial setup: offline indicator turns green for serverless mode
  connectionDot.className = "dot online";
  connectionDot.style.backgroundColor = "#22c55e";
  connectionText.innerText = "Serverless Mode";
  btnStartScrape.disabled = false;

  // Load jobs on popup open
  fetchJobs();

  // Toggle settings
  btnSettings.addEventListener("click", () => {
    const isSettingsHidden = settingsPane.classList.toggle("hidden");
    if (isSettingsHidden) {
      scrapingFormCard.classList.remove("hidden");
      jobsSection.classList.remove("hidden");
    } else {
      scrapingFormCard.classList.add("hidden");
      jobsSection.classList.add("hidden");
    }
  });

  // Save/Close Settings
  btnSaveSettings.addEventListener("click", () => {
    settingsPane.classList.add("hidden");
    scrapingFormCard.classList.remove("hidden");
    jobsSection.classList.remove("hidden");
  });

  // Clear Job History
  btnClearHistory.addEventListener("click", () => {
    if (confirm("Are you sure you want to clear all jobs and downloaded zip files?")) {
      chrome.storage.local.get("jobs", (data) => {
        const jobs = data.jobs || [];
        const keysToRemove = jobs.map(j => `zip_${j.id}`);
        keysToRemove.push("jobs");
        keysToRemove.push("active_job");
        
        chrome.storage.local.remove(keysToRemove, async () => {
          try {
            await DZDB.clearAllZips();
          } catch (e) {
            console.error("Failed to clear IndexedDB:", e);
          }
          fetchJobs();
          alert("All job history cleared successfully.");
        });
      });
    }
  });

  // Create Scraping Job
  btnStartScrape.addEventListener("click", () => {
    const query = inputQuery.value.trim();
    const limit = parseInt(inputLimit.value, 10) || 100;

    if (!query) {
      alert("Please enter a keyword.");
      return;
    }

    btnStartScrape.disabled = true;
    btnStartScrape.querySelector(".btn-text").innerText = "Queueing...";

    // Send start scrape message to background service worker
    chrome.runtime.sendMessage({ action: "start_scrape", query, limit }, (response) => {
      btnStartScrape.disabled = false;
      btnStartScrape.querySelector(".btn-text").innerText = "SCRAPE NOW";
      
      if (response && response.status === "success") {
        inputQuery.value = "";
        fetchJobs();
      } else {
        alert("Failed to queue scraping task in the extension background.");
      }
    });
  });

  // Refresh Jobs Trigger
  btnRefreshJobs.addEventListener("click", fetchJobs);

  // Fetch Jobs List from chrome.storage.local
  function fetchJobs() {
    chrome.storage.local.get("jobs", (data) => {
      const jobs = data.jobs || [];
      renderJobs(jobs);
      
      // Determine if we need to poll (if any job is running or pending or downloading)
      const hasActiveJobs = jobs.some(j => j.status === "running" || j.status === "pending" || j.status === "downloading");
      
      if (hasActiveJobs) {
        if (!activePollInterval) {
          activePollInterval = setInterval(fetchJobs, 1000); // Poll every 1 second for instant progress bar update
        }
      } else {
        if (activePollInterval) {
          clearInterval(activePollInterval);
          activePollInterval = null;
        }
      }
    });
  }

  // Render Jobs to UI
  function renderJobs(jobs) {
    if (jobs.length === 0) {
      jobsList.innerHTML = `
        <div class="empty-state">
          No active jobs found. Start a new scrape above!
        </div>`;
      return;
    }

    jobsList.innerHTML = "";
    jobs.forEach(job => {
      const jobCard = document.createElement("div");
      jobCard.className = "job-item";

      const percent = Math.min(Math.round((job.total_downloaded / job.limit) * 100), 100) || 0;
      
      let badgeClass = "pending";
      let statusHtml = "pending";
      
      if (job.status === "running") {
        badgeClass = "running";
        statusHtml = `<img src="icons/settings.png" class="status-icon status-icon-spin" alt="running"> running (${job.total_scraped || 0})`;
      } else if (job.status === "downloading") {
        badgeClass = "running";
        statusHtml = `<img src="icons/settings.png" class="status-icon status-icon-spin" alt="downloading"> downloading`;
      } else if (job.status === "completed") {
        badgeClass = "completed";
        statusHtml = `<img src="icons/completed.png" class="status-icon" alt="done"> done`;
      } else if (job.status === "failed") {
        badgeClass = "failed";
        statusHtml = `<img src="icons/failed.png" class="status-icon" alt="failed"> failed`;
      }

      // Generate clean filename
      const cleanQuery = job.query.replace(/[^a-z0-9]/gi, "_").toLowerCase();
      const filename = `dataset_${cleanQuery}_${job.id.substr(-4)}.zip`;

      jobCard.innerHTML = `
        <div class="job-top-row">
          <span class="job-keyword-badge" title="${escapeHtml(job.query)}">${escapeHtml(job.query)}</span>
          <span class="job-status-badge ${badgeClass}">${statusHtml}</span>
        </div>
        <div class="progress-container">
          <div class="progress-bar" style="width: ${percent}%"></div>
        </div>
        <div class="progress-labels">
          <span class="progress-stats">${job.total_downloaded}/${job.limit} img</span>
          <span class="progress-percent">${percent}%</span>
        </div>
        ${job.error_message ? `<div class="job-error-msg">${escapeHtml(job.error_message)}</div>` : ""}
        <div class="job-bottom-row" data-id="${job.id}">
          ${job.status === "completed" && job.total_downloaded > 0 ? 
            `<a href="download.html?job_id=${job.id}&filename=${encodeURIComponent(filename)}" target="_blank" class="download-zip-btn">Download zip</a>` : 
            `<span></span>`
          }
          <button class="delete-btn" title="Delete job">
            <img src="icons/delete_zip_file.png" alt="Delete">
          </button>
        </div>
      `;

      // Bind delete button event
      jobCard.querySelector(".delete-btn").addEventListener("click", () => {
        if (confirm("Are you sure you want to delete this job and all its scraped images?")) {
          deleteJob(job.id);
        }
      });

      jobsList.appendChild(jobCard);
    });
  }

  // Delete Job from Local Storage
  function deleteJob(jobId) {
    chrome.storage.local.get("jobs", (data) => {
      let jobs = (data.jobs || []).map(j => DZDB.sanitizeJob(j)).filter(Boolean);
      jobs = jobs.filter(j => j.id !== jobId);
      
      // Delete zip binary from storage
      chrome.storage.local.remove([`zip_${jobId}`, `zip_data_${jobId}`], async () => {
        try {
          await DZDB.deleteZip(jobId);
        } catch (e) {
          console.error("Failed to delete zip from IndexedDB:", e);
        }
        chrome.storage.local.set({ jobs }, () => {
          fetchJobs();
        });
      });
    });
  }

  // HTML escape helper
  function escapeHtml(str) {
    if (!str) return "";
    return str
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }
});

