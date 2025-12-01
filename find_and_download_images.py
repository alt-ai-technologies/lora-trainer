#!/usr/bin/env python3
"""Find and download generated images from Modal volume."""
import modal
import os
from pathlib import Path

app = modal.App("find-images")

volume = modal.Volume.from_name("zimage-generation-outputs")

@app.function(volumes={"/root/modal_output": volume})
def find_images():
    import os
    import shutil
    from pathlib import Path
    
    output_dir = "/root/modal_output"
    
    print("=" * 60)
    print("Searching for generated images...")
    print("=" * 60)
    
    all_files = []
    image_files = []
    
    if os.path.exists(output_dir):
        print(f"\n✓ Found output directory: {output_dir}\n")
        
        # Walk through all directories
        for root, dirs, files in os.walk(output_dir):
            level = root.replace(output_dir, '').count(os.sep)
            indent = ' ' * 2 * level
            rel_path = os.path.relpath(root, output_dir)
            if rel_path == '.':
                print(f"{indent}modal_output/")
            else:
                print(f"{indent}{os.path.basename(root)}/")
            
            subindent = ' ' * 2 * (level + 1)
            for file in sorted(files):
                file_path = os.path.join(root, file)
                file_size = os.path.getsize(file_path)
                all_files.append(file_path)
                
                if file.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                    image_files.append(file_path)
                    print(f"{subindent}🖼️  {file} ({file_size:,} bytes)")
                else:
                    print(f"{subindent}📄 {file} ({file_size:,} bytes)")
    
    print("\n" + "=" * 60)
    print(f"Summary:")
    print(f"  Total files found: {len(all_files)}")
    print(f"  Image files: {len(image_files)}")
    print("=" * 60)
    
    if image_files:
        print("\n✓ Image files found:")
        for img in image_files:
            rel_path = os.path.relpath(img, output_dir)
            # Path relative to volume root (remove /root/modal_output prefix)
            volume_path = img.replace(output_dir, '').lstrip('/')
            print(f"  - {rel_path}")
            print(f"    Volume path: {volume_path}")
    
    return {
        'all_files': all_files,
        'image_files': image_files,
        'image_paths': [img.replace(output_dir, '').lstrip('/') for img in image_files],
        'output_dir': output_dir
    }

if __name__ == "__main__":
    with app.run():
        result = find_images.remote()
        if result['image_files']:
            print(f"\n✅ Found {len(result['image_files'])} image(s)!")
            print("\nImage paths in volume:")
            for i, path in enumerate(result['image_paths'], 1):
                print(f"  {i}. {path}")
            
            print("\n" + "=" * 60)
            print("Downloading images...")
            print("=" * 60)
            
            # Download each image
            import subprocess
            os.makedirs("downloaded_images", exist_ok=True)
            
            for i, (img_path, volume_path) in enumerate(zip(result['image_files'], result['image_paths']), 1):
                filename = os.path.basename(img_path)
                local_path = f"downloaded_images/{filename}"
                
                print(f"\nDownloading {i}/{len(result['image_files'])}: {filename}...")
                try:
                    # Use modal volume get command
                    # The volume path should be relative to the mount point
                    # Since we mounted /root/modal_output, the path in volume is just the filename or subpath
                    cmd = ["modal", "volume", "get", "zimage-generation-outputs", 
                           f"/root/modal_output/{volume_path}", local_path]
                    result_cmd = subprocess.run(cmd, capture_output=True, text=True)
                    if result_cmd.returncode == 0:
                        print(f"  ✅ Saved to: {local_path}")
                    else:
                        print(f"  ⚠️  Error: {result_cmd.stderr}")
                        # Try alternative path
                        alt_cmd = ["modal", "volume", "get", "zimage-generation-outputs", 
                                   volume_path, local_path]
                        alt_result = subprocess.run(alt_cmd, capture_output=True, text=True)
                        if alt_result.returncode == 0:
                            print(f"  ✅ Saved to: {local_path} (alternative path)")
                        else:
                            print(f"  ❌ Failed: {alt_result.stderr}")
                except Exception as e:
                    print(f"  ❌ Error downloading: {e}")
            
            print("\n" + "=" * 60)
            print("Download complete!")
            print(f"Images saved to: downloaded_images/")
            print("=" * 60)
        else:
            print("\n⚠️  No image files found in the volume.")

