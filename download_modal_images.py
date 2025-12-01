#!/usr/bin/env python3
"""Download generated images from Modal volume."""
import modal
import os
from pathlib import Path

app = modal.App("download-images")

volume = modal.Volume.from_name("zimage-generation-outputs")

@app.function(volumes={"/vol": volume})
def find_and_list_images():
    import os
    from pathlib import Path
    
    print("Searching for generated images...")
    
    # Search in common locations
    search_paths = [
        "/root/modal_output",
        "/vol",
        "/root",
    ]
    
    found_files = []
    for search_path in search_paths:
        if os.path.exists(search_path):
            print(f"\nSearching in: {search_path}")
            for root, dirs, files in os.walk(search_path):
                for file in files:
                    if file.endswith(('.png', '.jpg', '.jpeg', '.webp')):
                        full_path = os.path.join(root, file)
                        found_files.append(full_path)
                        print(f"  Found: {full_path}")
    
    if not found_files:
        print("\nNo image files found. Listing all files in /root/modal_output:")
        if os.path.exists("/root/modal_output"):
            for item in os.listdir("/root/modal_output"):
                item_path = os.path.join("/root/modal_output", item)
                if os.path.isdir(item_path):
                    print(f"  Directory: {item_path}")
                    for subitem in os.listdir(item_path):
                        print(f"    - {subitem}")
                else:
                    print(f"  File: {item_path}")
    
    return found_files

if __name__ == "__main__":
    with app.run():
        files = find_and_list_images.remote()
        print(f"\nTotal images found: {len(files)}")

