#!/usr/bin/env python3
"""Download training sample images from Modal volume."""

import modal
import subprocess
from pathlib import Path

app = modal.App("download-training-samples")

image = modal.Image.debian_slim(python_version="3.11")

MOUNT_DIR = "/root/modal_output"
training_output_volume = modal.Volume.from_name("zimage-training-outputs", create_if_missing=True)

@app.function(
    volumes={MOUNT_DIR: training_output_volume},
    timeout=300,
)
def download_samples_to_mount(local_output_path: str):
    """Copy samples to a mounted directory for download."""
    from pathlib import Path
    import shutil
    
    samples_dir = Path(MOUNT_DIR) / "zimage_turbo_book_covers_lora_v1" / "samples"
    output_dir = Path(local_output_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("=" * 60)
    print("Downloading Training Sample Images")
    print("=" * 60)
    print(f"Source: {samples_dir}")
    print(f"Destination: {output_dir}")
    print()
    
    if not samples_dir.exists():
        print("❌ Samples directory not found!")
        return {"count": 0, "files": []}
    
    image_files = sorted(samples_dir.glob("*.{jpg,jpeg,png}"))
    
    print(f"Found {len(image_files)} sample images")
    print()
    
    copied = []
    for img in image_files:
        dest = output_dir / img.name
        shutil.copy2(img, dest)
        size = img.stat().st_size / 1024  # KB
        copied.append(img.name)
        print(f"  ✅ {img.name} ({size:.1f} KB)")
    
    print()
    print(f"✅ Copied {len(copied)} images to {output_dir}")
    
    return {"count": len(copied), "files": copied}

@app.local_entrypoint()
def main(output_dir: str = "./downloaded_training_samples"):
    """Download training sample images."""
    import os
    
    # Create output directory locally
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Mount the local output directory
    local_mount = modal.Mount.from_local_dir(
        str(output_path.absolute()),
        remote_path="/mnt/download_output"
    )
    
    # Create a function that uses the mount
    @app.function(
        mounts=[local_mount],
        volumes={MOUNT_DIR: training_output_volume},
        timeout=300,
    )
    def download_with_mount():
        from pathlib import Path
        import shutil
        
        samples_dir = Path(MOUNT_DIR) / "zimage_turbo_book_covers_lora_v1" / "samples"
        output_dir = Path("/mnt/download_output")
        
        print("=" * 60)
        print("Downloading Training Sample Images")
        print("=" * 60)
        print(f"Source: {samples_dir}")
        print(f"Destination: {output_dir}")
        print()
        
        if not samples_dir.exists():
            print("❌ Samples directory not found!")
            return {"count": 0, "files": []}
        
        image_files = sorted(samples_dir.glob("*.{jpg,jpeg,png}"))
        
        print(f"Found {len(image_files)} sample images")
        print()
        
        copied = []
        for img in image_files:
            dest = output_dir / img.name
            shutil.copy2(img, dest)
            size = img.stat().st_size / 1024  # KB
            copied.append(img.name)
            print(f"  ✅ {img.name} ({size:.1f} KB)")
        
        print()
        print(f"✅ Copied {len(copied)} images")
        
        return {"count": len(copied), "files": copied}
    
    # Run the download
    result = download_with_mount.remote()
    
    print()
    print("=" * 60)
    print(f"Download complete!")
    print(f"  ✅ Downloaded: {result['count']} images")
    print(f"  📁 Location: {output_path.absolute()}")
    print("=" * 60)

if __name__ == "__main__":
    import sys
    output_dir = sys.argv[1] if len(sys.argv) > 1 else "./downloaded_training_samples"
    main(output_dir)

