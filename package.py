import os
import zipfile
from pathlib import Path

def package_zip():
    print("Packaging serverless extension into zip archive...")
    root_dir = Path(__file__).resolve().parent
    extension_dir = root_dir / "extension"
    zip_path = root_dir / "image_scraper_pro_extension.zip"
    
    # Files to include in the submission package (relative to extension_dir)
    include_files = [
        "manifest.json",
        "popup.html",
        "popup.js",
        "style.css",
        "background.js",
        "scraper.js",
        "download.html",
        "download.js",
        "lib/db.js",
        "lib/jszip.min.js",
        "icons/icon16.png",
        "icons/icon48.png",
        "icons/icon128.png",
        "icons/settings.png",
        "icons/completed.png",
        "icons/failed.png",
        "icons/delete_zip_file.png",
        "icons/refresh.png"
    ]
    
    # Check if all files exist
    missing_files = []
    for rel_path in include_files:
        full_path = extension_dir / rel_path
        if not full_path.exists():
            missing_files.append(rel_path)
            
    if missing_files:
        print(f"Error: Missing required files for package: {missing_files}")
        return False
        
    try:
        # If exists, delete it first to start clean
        if zip_path.exists():
            os.remove(zip_path)
            
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for rel_path in include_files:
                full_path = extension_dir / rel_path
                zf.write(full_path, arcname=rel_path)
                print(f"Added to zip: {rel_path}")
        print(f"\nSuccess! Created extension package at: {zip_path}")
        return True
    except Exception as e:
        print(f"Error zipping package: {e}")
        return False

if __name__ == "__main__":
    package_zip()
