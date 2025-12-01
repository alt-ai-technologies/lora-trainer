#!/usr/bin/env python3
"""
Download Uchida Laboratory Book Cover Dataset and upload to Modal.

This script will:
1. Download the dataset from GitHub
2. Prepare it (create captions from metadata)
3. Upload to Modal volume

Usage:
    python download_and_upload_book_dataset.py
    python download_and_upload_book_dataset.py --max-images 1000  # Limit for testing
"""

import argparse
import subprocess
import sys
from pathlib import Path

def check_modal_installed():
    """Check if modal is installed."""
    try:
        subprocess.run(["modal", "--version"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def download_uchida_dataset(output_dir: Path, max_images: int = None):
    """Download and prepare Uchida Laboratory dataset."""
    print("=" * 60)
    print("Downloading Uchida Laboratory Book Cover Dataset")
    print("=" * 60)
    print()
    print("Note: This dataset is large (207,572 book covers)")
    print("Source: https://github.com/uchidalab/book-dataset")
    print()
    
    dataset_dir = output_dir / "uchida_book_dataset"
    dataset_dir.mkdir(parents=True, exist_ok=True)
    
    # Check if already downloaded
    if (dataset_dir / "images").exists() and len(list((dataset_dir / "images").glob("*.jpg"))) > 0:
        print(f"Dataset already exists at {dataset_dir}")
        response = input("Re-download? (y/N): ").strip().lower()
        if response != 'y':
            return dataset_dir
    
    print("To download the dataset:")
    print("1. Clone the repository:")
    print(f"   git clone https://github.com/uchidalab/book-dataset.git {dataset_dir}")
    print()
    print("2. Or download manually from:")
    print("   https://github.com/uchidalab/book-dataset")
    print()
    print("The dataset should contain:")
    print("  - images/ folder with book cover images")
    print("  - metadata (JSON/CSV) with book information")
    print()
    
    # Try to clone if git is available
    try:
        print("Attempting to clone repository...")
        subprocess.run(
            ["git", "clone", "https://github.com/uchidalab/book-dataset.git", str(dataset_dir)],
            check=True,
            capture_output=True
        )
        print("✓ Repository cloned")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠ Git clone failed. Please download manually.")
        print(f"   Place the dataset in: {dataset_dir}")
        response = input("Continue with manual download? (y/N): ").strip().lower()
        if response != 'y':
            sys.exit(1)
    
    return dataset_dir

def prepare_dataset_with_script(dataset_dir: Path, prepared_dir: Path, max_images: int = None):
    """Use the prepare_book_cover_dataset.py script to prepare the dataset."""
    print()
    print("=" * 60)
    print("Preparing dataset (creating captions)")
    print("=" * 60)
    print()
    
    # Find images directory
    images_dir = None
    for possible_dir in [dataset_dir / "images", dataset_dir / "book-covers", dataset_dir]:
        if (possible_dir).exists():
            image_files = list(possible_dir.glob("*.{jpg,jpeg,png}"))
            if len(image_files) > 0:
                images_dir = possible_dir
                break
    
    if not images_dir:
        raise FileNotFoundError(f"Could not find images in {dataset_dir}")
    
    print(f"Found images in: {images_dir}")
    print(f"Found {len(list(images_dir.glob('*.{jpg,jpeg,png}'))) } images")
    print()
    
    # Find metadata
    metadata_file = None
    for possible_file in [
        dataset_dir / "metadata.json",
        dataset_dir / "metadata.jsonl",
        dataset_dir / "books.csv",
        dataset_dir / "data.csv"
    ]:
        if possible_file.exists():
            metadata_file = possible_file
            break
    
    # Prepare using the script
    script_path = Path(__file__).parent / "prepare_book_cover_dataset.py"
    
    cmd = [
        sys.executable,
        str(script_path),
        "--input", str(images_dir),
        "--output", str(prepared_dir),
        "--min-size", "512"
    ]
    
    if metadata_file:
        print(f"Using metadata: {metadata_file}")
        cmd.extend(["--metadata", str(metadata_file)])
    else:
        print("No metadata found, using auto-captioning")
        cmd.append("--auto-caption")
    
    if max_images:
        cmd.extend(["--max-images", str(max_images)])
    
    print(f"Running: {' '.join(cmd)}")
    print()
    
    result = subprocess.run(cmd, check=False)
    
    if result.returncode != 0:
        raise RuntimeError(f"Dataset preparation failed with exit code {result.returncode}")
    
    return prepared_dir

def upload_to_modal(prepared_dir: Path):
    """Upload prepared dataset to Modal."""
    print()
    print("=" * 60)
    print("Uploading to Modal")
    print("=" * 60)
    print()
    
    if not check_modal_installed():
        print("Error: Modal is not installed or not in PATH")
        print("Install with: pip install modal")
        print("Or activate your virtual environment")
        sys.exit(1)
    
    upload_script = Path(__file__).parent / "upload_dataset_to_modal.py"
    
    cmd = [
        "modal", "run",
        str(upload_script),
        "--local-path", str(prepared_dir),
        "--remote-path", "book_covers"
    ]
    
    print(f"Running: {' '.join(cmd)}")
    print()
    
    subprocess.run(cmd, check=True)

def main():
    parser = argparse.ArgumentParser(
        description="Download and upload book cover dataset to Modal"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="./datasets",
        help="Directory to store downloaded dataset (default: ./datasets)"
    )
    parser.add_argument(
        "--max-images",
        type=int,
        help="Maximum number of images to process (for testing)"
    )
    parser.add_argument(
        "--skip-download",
        action="store_true",
        help="Skip download, use existing dataset"
    )
    parser.add_argument(
        "--skip-prepare",
        action="store_true",
        help="Skip preparation, use existing prepared dataset"
    )
    parser.add_argument(
        "--skip-upload",
        action="store_true",
        help="Skip upload to Modal"
    )
    
    args = parser.parse_args()
    
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    
    prepared_dir = output_dir / "prepared_book_covers"
    
    try:
        # Step 1: Download
        if not args.skip_download:
            dataset_dir = download_uchida_dataset(output_dir, args.max_images)
        else:
            dataset_dir = output_dir / "uchida_book_dataset"
            if not dataset_dir.exists():
                print(f"Error: Dataset directory not found: {dataset_dir}")
                sys.exit(1)
        
        # Step 2: Prepare
        if not args.skip_prepare:
            prepare_dataset_with_script(dataset_dir, prepared_dir, args.max_images)
        else:
            if not prepared_dir.exists():
                print(f"Error: Prepared dataset not found: {prepared_dir}")
                sys.exit(1)
        
        # Step 3: Upload
        if not args.skip_upload:
            upload_to_modal(prepared_dir)
        else:
            print()
            print("Skipping upload. To upload manually, run:")
            print(f"  modal run upload_dataset_to_modal.py --local-path {prepared_dir} --remote-path book_covers")
        
        print()
        print("=" * 60)
        print("✓ Complete!")
        print("=" * 60)
        print()
        print("Your dataset is ready at:")
        print(f"  Local: {prepared_dir}")
        print(f"  Modal: /root/datasets/book_covers")
        print()
        print("You can now run training with:")
        print("  modal run modal_train_deploy.py config/examples/modal/modal_train_lora_book_covers.yaml")
        
    except KeyboardInterrupt:
        print("\n\nCancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

