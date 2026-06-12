document.addEventListener("DOMContentLoaded", () => {
  // Config state
  let API_URL = "http://localhost:8000";
  let activePollInterval = null;

  // DOM Elements
  const btnSettings = document.getElementById("btn-settings");
  const settingsPane = document.getElementById("settings-pane");
  const inputApiUrl = document.getElementById("input-api-url");
  const btnSaveSettings = document.getElementById("btn-save-settings");

  const inputQuery = document.getElementById("input-query");
  const selectEngine = document.getElementById("select-engine");
  const inputLimit = document.getElementById("input-limit");
  const btnStartScrape = document.getElementById("btn-start-scrape");

  const btnRefreshJobs = document.getElementById("btn-refresh-jobs");
  const jobsList = document.getElementById("jobs-list");

  const connectionDot = document.getElementById("connection-dot");
  const connectionText = document.getElementById("connection-text");

  // Load API settings from storage on startup
  if (typeof chrome !== "undefined" && chrome.storage && chrome.storage.local) {
    chrome.storage.local.get(["apiUrl"], (result) => {
      if (result.apiUrl) {
        API_URL = result.apiUrl;
        inputApiUrl.value = API_URL;
      }
      initConnection();
    });
  } else {
    // Fallback if running outside of extension context for debugging
    initConnection();
  }

  // Toggle settings
  btnSettings.addEventListener("click", () => {
    settingsPane.classList.toggle("hidden");
  });

  // Save Settings
  btnSaveSettings.addEventListener("click", () => {
    let url = inputApiUrl.value.trim();
    if (url.endsWith("/")) {
      url = url.slice(0, -1);
    }
    API_URL = url;
    
    if (typeof chrome !== "undefined" && chrome.storage && chrome.storage.local) {
      chrome.storage.local.set({ apiUrl: API_URL }, () => {
        settingsPane.classList.add("hidden");
        initConnection();
      });
    } else {
      settingsPane.classList.add("hidden");
      initConnection();
    }
  });

  // Initial connection check
  async function initConnection() {
    updateConnectionStatus(false, "Connecting to Backend...");
    try {
      const response = await fetch(`${API_URL}/health`);
      if (response.ok) {
        updateConnectionStatus(true, "Backend Connected");
        fetchJobs();
      } else {
        updateConnectionStatus(false, "Backend Server Error");
      }
    } catch (e) {
      updateConnectionStatus(false, "Backend Offline");
    }
  }

  function updateConnectionStatus(isOnline, text) {
    if (isOnline) {
      connectionDot.className = "dot online";
      connectionText.innerText = text;
      btnStartScrape.disabled = false;
    } else {
      connectionDot.className = "dot offline";
      connectionText.innerText = text;
      btnStartScrape.disabled = true;
    }
  }

  // Create Scraping Job
  btnStartScrape.addEventListener("click", async () => {
    const query = inputQuery.value.trim();
    const engine = selectEngine.value;
    const limit = parseInt(inputLimit.value, 10);

    if (!query) {
      alert("Please enter a keyword or URL.");
      return;
    }

    btnStartScrape.disabled = true;
    btnStartScrape.querySelector(".btn-text").innerText = "Queueing...";

    try {
      const response = await fetch(`${API_URL}/api/v1/scrape`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ query, limit, engine })
      });

      if (response.ok) {
        inputQuery.value = "";
        fetchJobs();
      } else {
        const err = await response.json();
        alert(`Error: ${err.detail || "Failed to start scraping job"}`);
      }
    } catch (e) {
      alert(`Network Error: ${e.message}`);
    } finally {
      btnStartScrape.disabled = false;
      btnStartScrape.querySelector(".btn-text").innerText = "Queue Scraping Job";
    }
  });

  // Refresh Jobs Trigger
  btnRefreshJobs.addEventListener("click", fetchJobs);

  // Fetch Jobs List
  async function fetchJobs() {
    try {
      const response = await fetch(`${API_URL}/api/v1/jobs`);
      if (!response.ok) throw new Error("Failed to fetch jobs");
      const jobs = await response.json();
      renderJobs(jobs);
      
      // Determine if we need to poll (if any job is running or pending)
      const hasActiveJobs = jobs.some(j => j.status === "running" || j.status === "pending");
      
      if (hasActiveJobs) {
        if (!activePollInterval) {
          activePollInterval = setInterval(fetchJobs, 2500); // Poll every 2.5 seconds
        }
      } else {
        if (activePollInterval) {
          clearInterval(activePollInterval);
          activePollInterval = null;
        }
      }
    } catch (e) {
      console.error(e);
      jobsList.innerHTML = `<div class="empty-state">Error listing jobs. Ensure API is running.</div>`;
    }
  }

  // Render Jobs to UI
  function renderJobs(jobs) {
    if (jobs.length === 0) {
      jobsList.innerHTML = `
        <div class="empty-state">
          <p>No active jobs found. Start a new scrape above!</p>
        </div>`;
      return;
    }

    jobsList.innerHTML = "";
    jobs.forEach(job => {
      const jobCard = document.createElement("div");
      jobCard.className = "job-item";

      const percent = Math.min(Math.round((job.total_downloaded / job.limit) * 100), 100) || 0;
      
      let badgeClass = "pending";
      let statusIcon = "⏳";
      if (job.status === "running") {
        badgeClass = "running";
        statusIcon = "⚙️";
      } else if (job.status === "completed") {
        badgeClass = "completed";
        statusIcon = "✅";
      } else if (job.status === "failed") {
        badgeClass = "failed";
        statusIcon = "❌";
      }

      jobCard.innerHTML = `
        <div class="job-meta">
          <span class="job-query" title="${escapeHtml(job.query)}">${escapeHtml(job.query)}</span>
          <span class="job-engine-tag">${job.engine}</span>
        </div>
        <div class="job-status-row">
          <span class="job-stats">${job.total_downloaded} / ${job.limit} imgs (${percent}%)</span>
          <span class="status-badge ${badgeClass}">${statusIcon} ${job.status}</span>
        </div>
        <div class="progress-container">
          <div class="progress-bar ${job.status}" style="width: ${percent}%"></div>
        </div>
        ${job.error_message ? `<div class="job-error-msg">${escapeHtml(job.error_message)}</div>` : ""}
        <div class="job-actions" data-id="${job.id}">
          ${job.status === "completed" ? `<a href="${API_URL}/api/v1/jobs/${job.id}/export" class="action-btn export-btn" download>📥 Download Dataset</a>` : ""}
          <button class="action-btn delete-btn">🗑️ Delete</button>
        </div>
      `;

      // Bind delete button event
      jobCard.querySelector(".delete-btn").addEventListener("click", async () => {
        if (confirm("Are you sure you want to delete this job and all its scraped images?")) {
          await deleteJob(job.id);
        }
      });

      jobsList.appendChild(jobCard);
    });
  }

  // Delete Job API Call
  async function deleteJob(jobId) {
    try {
      const response = await fetch(`${API_URL}/api/v1/jobs/${jobId}`, {
        method: "DELETE"
      });
      if (response.ok) {
        fetchJobs();
      } else {
        alert("Failed to delete job");
      }
    } catch (e) {
      alert(`Network Error: ${e.message}`);
    }
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
