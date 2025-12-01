#!/usr/bin/env python3
"""Get generated images from Modal volume."""
import modal
import os

app = modal.App("get-images")

volume = modal.Volume.from_name("zimage-generation-outputs")

@app.function(volumes={"/vol": volume})
def get_images():
    import os
    import shutil
    from pathlib import Path
    
    # The output should be in /root/modal_output
    # But let's check the actual structure
    output_base = "/root/modal_output"
    
    print("Checking output directory structure...")
    
    if os.path.exists(output_base):
        print(f"\n✓ Found: {output_base}")
        
        # List everything
        for root, dirs, files in os.walk(output_base):
            level = root.replace(output_base, '').count(os.sep)
            indent = ' ' * 2 * level
            print(f'{indent}{os.path.basename(root) if root != output_base else "modal_output"}/')
            subindent = ' ' * 2 * (level + 1)
            for file in sorted(files):
                file_path = os.path.join(root, file)
                file_size = os.path.getsize(file_path)
                print(f'{subindent}{file} ({file_size:,} bytes)')
        
        # Find all image files
        image_files = []
        for root, dirs, files in os.walk(output_base):
            for file in files:
                if file.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                    image_files.append(os.path.join(root, file))
        
        print(f"\n✓ Found {len(image_files)} image file(s)")
        for img in image_files:
            print(f"  - {img}")
        
        return image_files
    else:
        print(f"\n✗ Directory not found: {output_base}")
        # List root
        print("\nListing /root:")
        if os.path.exists("/root"):
            for item in os.listdir("/root"):
                item_path = os.path.join("/root", item)
                if os.path.isdir(item_path):
                    print(f"  Directory: {item}")
                else:
                    print(f"  File: {item}")
        return []

if __name__ == "__main__":
    with app.run():
        files = get_images.remote()
        if files:
            print(f"\n✓ Successfully found {len(files)} image(s)")
            print("\nTo download, the images are in the volume at the paths shown above.")
            print("You can access them via Modal dashboard or use volume commands.")
        else:
            print("\n⚠ No image files found in expected location.")

