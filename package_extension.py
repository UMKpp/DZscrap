import os
import zipfile
from pathlib import Path
from PIL import Image

def resize_icons():
    print("Resizing extension icons...")
    extension_dir = Path(__file__).resolve().parent / "extension"
    icons_dir = extension_dir / "icons"
    raw_logo_path = icons_dir / "logo_raw.png"
    
    if not raw_logo_path.exists():
        print(f"Error: Raw logo not found at {raw_logo_path}")
        return False
        
    sizes = [16, 48, 128]
    try:
        with Image.open(raw_logo_path) as img:
            for size in sizes:
                resized = img.resize((size, size), Image.Resampling.LANCZOS)
                output_path = icons_dir / f"icon{size}.png"
                resized.save(output_path, "PNG")
                print(f"Generated {output_path.name} ({size}x{size})")
        return True
    except Exception as e:
        print(f"Error generating icons: {e}")
        return False

def package_zip():
    print("\nPackaging extension into zip archive...")
    root_dir = Path(__file__).resolve().parent
    extension_dir = root_dir / "extension"
    zip_path = root_dir / "image_scraper_pro_extension.zip"
    
    # Files to include in the submission package (relative to extension_dir)
    include_files = [
        "manifest.json",
        "popup.html",
        "popup.js",
        "style.css",
        "icons/icon16.png",
        "icons/icon48.png",
        "icons/icon128.png"
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
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for rel_path in include_files:
                full_path = extension_dir / rel_path
                # Write to zip, keeping the same relative structure
                zf.write(full_path, arcname=rel_path)
                print(f"Added to zip: {rel_path}")
        print(f"\nSuccess! Created extension package at: {zip_path}")
        return True
    except Exception as e:
        print(f"Error zipping package: {e}")
        return False

if __name__ == "__main__":
    if resize_icons():
        package_zip()
