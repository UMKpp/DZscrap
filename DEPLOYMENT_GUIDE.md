# Render Deployment Guide

This guide covers deploying the Image Scraper Pro backend components to **Render**. We will use their managed Redis service, and set up two Docker-based services for the FastAPI Backend and Celery Worker.

## Prerequisites
- A GitHub account with this repository pushed to it.
- A Render account (https://render.com).

## Step 1: Create Managed Redis
1. On your Render dashboard, click **New +** and select **Redis**.
2. Name it (e.g., `isp-redis`).
3. Select your region and instance type (Free tier works for small queues).
4. Click **Create Redis**.
5. Once created, copy the **Internal Redis URL** (e.g., `redis://red-xxxxxxxxxxxx:6379`). You will need this for the backend and worker.

## Step 2: Deploy the FastAPI Backend
1. Click **New +** and select **Web Service**.
2. Connect your GitHub repository.
3. In the setup page, configure the following:
   - **Name**: `isp-backend`
   - **Environment**: `Docker`
   - **Region**: Same as your Redis instance
   - **Dockerfile path**: `./docker/backend.Dockerfile`
4. Expand **Advanced**, and click **Add Environment Variable**. Add the following:
   - `REDIS_URL` = `<Your Internal Redis URL from Step 1>`
   - `DATABASE_URL` = `sqlite:////app/storage/db.sqlite3`
   - `STORAGE_DIR` = `/app/storage`
   - `ALLOWED_ORIGINS` = `chrome-extension://<your-extension-id>,https://isp-backend.onrender.com`
     *(Note: Ensure you include your Render domain and your Chrome Extension ID if loaded via unpacked extension).*
5. Expand **Disks** (Requires paid tier to persist data across restarts! If you don't use disks, scraped files will be lost when Render restarts the container):
   - **Name**: `isp-storage`
   - **Mount Path**: `/app/storage`
   - **Size**: `1 GB` (or larger depending on your scraping volume)
6. Click **Create Web Service**.
7. Wait for the deploy to finish. Copy the public URL (e.g., `https://isp-backend.onrender.com`).

## Step 3: Deploy the Celery Worker
1. Click **New +** and select **Background Worker**.
2. Connect the same GitHub repository.
3. Configure the following:
   - **Name**: `isp-worker`
   - **Environment**: `Docker`
   - **Region**: Same as your Redis instance
   - **Dockerfile path**: `./docker/worker.Dockerfile`
4. Expand **Advanced** and add the same Environment Variables:
   - `REDIS_URL` = `<Your Internal Redis URL from Step 1>`
   - `DATABASE_URL` = `sqlite:////app/storage/db.sqlite3`
   - `STORAGE_DIR` = `/app/storage`
5. Expand **Disks** (IMPORTANT: You must mount the SAME disk or a shared disk if you want the backend to be able to serve the files the worker downloaded. However, Render Background Workers and Web Services cannot mount the *same* disk. For true distributed storage, consider replacing the local SQLite and file storage with Amazon S3 and PostgreSQL. For now, the worker will run and save files, but you may need an object store for full persistence).
6. Click **Create Background Worker**.

## Step 4: Chrome Extension Setup
1. Open the Chrome Extension code.
2. In `extension/manifest.json`, verify the `host_permissions` match your Render web service URL (e.g., `"https://isp-backend.onrender.com/*"`).
3. In `extension/popup.js`, verify `API_URL` points to your deployed backend (e.g., `let API_URL = "https://isp-backend.onrender.com";`).
4. Reload your extension in `chrome://extensions/`.

> **Scaling Notice**: Playwright instances require at least 512MB to 1GB of RAM. The worker instance size on Render should be configured accordingly (Starter tier or above recommended). Concurrency has been set to 2 to minimize memory usage.
