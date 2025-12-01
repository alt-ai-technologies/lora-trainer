#!/usr/bin/env python3
"""
Upload book cover dataset to Modal volume.

Usage:
    modal run upload_dataset_to_modal.py --local-path /path/to/dataset --remote-path book_covers
    modal run upload_dataset_to_modal.py --local-path ./datasets/book_covers --remote-path book_covers
"""

import modal
import os
from pathlib import Path

# Use the same image as training (lightweight for upload)
image = modal.Image.debian_slim(python_version="3.11").pip_install("tqdm")

# Get the dataset volume (same as in modal_train_deploy.py)
DATASET_DIR = "/root/datasets"
dataset_volume = modal.Volume.from_name("zimage-datasets", create_if_missing=True)

app = modal.App(
    name="upload-dataset",
    image=image
)


@app.function(
    volumes={DATASET_DIR: dataset_volume},
    timeout=3600,  # 1 hour timeout for large uploads
)
def upload_dataset(local_path: str, remote_path: str = "book_covers"):
    """
    Upload dataset from local path to Modal volume.
    
    Args:
        local_path: Local path to dataset directory (will be mounted)
        remote_path: Remote path in volume (e.g., "book_covers")
    """
    import shutil
    from tqdm import tqdm
    
    remote_full_path = Path(DATASET_DIR) / remote_path
    remote_full_path.mkdir(parents=True, exist_ok=True)
    
    local_path_obj = Path(local_path)
    
    if not local_path_obj.exists():
        raise FileNotFoundError(f"Local path does not exist: {local_path}")
    
    if not local_path_obj.is_dir():
        raise ValueError(f"Local path must be a directory: {local_path}")
    
    print(f"Uploading dataset from: {local_path}")
    print(f"To Modal volume: {remote_full_path}")
    print()
    
    # Count files first
    image_extensions = {'.jpg', '.jpeg', '.png', '.webp'}
    text_extensions = {'.txt'}
    
    all_files = []
    for root, dirs, files in os.walk(local_path):
        for file in files:
            file_path = Path(root) / file
            rel_path = file_path.relative_to(local_path_obj)
            all_files.append((file_path, rel_path))
    
    print(f"Found {len(all_files)} files to upload")
    print()
    
    # Upload files
    uploaded = 0
    skipped = 0
    
    for local_file, rel_path in tqdm(all_files, desc="Uploading"):
        remote_file = remote_full_path / rel_path
        
        # Create parent directory if needed
        remote_file.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            # Copy file
            shutil.copy2(local_file, remote_file)
            uploaded += 1
        except Exception as e:
            print(f"Error copying {local_file}: {e}")
            skipped += 1
    
    # Commit the volume
    print()
    print("Committing volume...")
    dataset_volume.commit()
    print("✓ Volume committed")
    
    print()
    print("=" * 60)
    print(f"Upload complete!")
    print(f"  - Uploaded: {uploaded} files")
    print(f"  - Skipped: {skipped} files")
    print(f"  - Remote path: {remote_full_path}")
    print("=" * 60)
    
    # List some files to verify
    print()
    print("Sample files in dataset:")
    sample_files = list(remote_full_path.glob("*"))[:10]
    for f in sample_files:
        size = f.stat().st_size if f.is_file() else 0
        print(f"  - {f.name} ({size:,} bytes)" if f.is_file() else f"  - {f.name}/ (directory)")


@app.local_entrypoint()
def main(local_path: str, remote_path: str = "book_covers"):
    """
    Local entrypoint to upload dataset.
    
    Usage:
        modal run upload_dataset_to_modal.py --local-path /path/to/dataset --remote-path book_covers
    """
    # Mount the local directory
    local_mount = modal.Mount.from_local_dir(
        local_path,
        remote_path="/mnt/local_dataset"
    )
    
    # Create a function that uses the mount
    @app.function(
        mounts=[local_mount],
        volumes={DATASET_DIR: dataset_volume},
        timeout=3600,
    )
    def upload_from_mount(remote_path: str):
        """Upload from mounted local directory."""
        import shutil
        from tqdm import tqdm
        
        local_mount_path = Path("/mnt/local_dataset")
        remote_full_path = Path(DATASET_DIR) / remote_path
        remote_full_path.mkdir(parents=True, exist_ok=True)
        
        print(f"Uploading dataset from mounted: {local_mount_path}")
        print(f"To Modal volume: {remote_full_path}")
        print()
        
        # Get all files
        all_files = []
        for root, dirs, files in os.walk(local_mount_path):
            for file in files:
                file_path = Path(root) / file
                rel_path = file_path.relative_to(local_mount_path)
                all_files.append((file_path, rel_path))
        
        print(f"Found {len(all_files)} files to upload")
        print()
        
        # Upload files
        uploaded = 0
        skipped = 0
        
        for local_file, rel_path in tqdm(all_files, desc="Uploading"):
            remote_file = remote_full_path / rel_path
            remote_file.parent.mkdir(parents=True, exist_ok=True)
            
            try:
                shutil.copy2(local_file, remote_file)
                uploaded += 1
            except Exception as e:
                print(f"Error copying {local_file}: {e}")
                skipped += 1
        
        # Commit the volume
        print()
        print("Committing volume...")
        dataset_volume.commit()
        print("✓ Volume committed")
        
        print()
        print("=" * 60)
        print(f"Upload complete!")
        print(f"  - Uploaded: {uploaded} files")
        print(f"  - Skipped: {skipped} files")
        print(f"  - Remote path: {remote_full_path}")
        print("=" * 60)
        
        # Verify upload
        print()
        print("Verifying upload...")
        image_files = list(remote_full_path.glob("*.{jpg,jpeg,png,webp}"))
        txt_files = list(remote_full_path.glob("*.txt"))
        print(f"  - Image files: {len(image_files)}")
        print(f"  - Caption files: {len(txt_files)}")
        
        if len(image_files) > 0:
            print()
            print("Sample files:")
            for f in image_files[:5]:
                print(f"  - {f.name}")
    
    # Run the upload
    upload_from_mount.remote(remote_path)

