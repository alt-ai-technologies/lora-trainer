#!/usr/bin/env python3
"""
Setup book cover dataset directly on Modal volume.

This script will download and prepare the book cover dataset on Modal,
avoiding the need to upload large datasets from local machine.

Usage:
    modal run setup_book_dataset_on_modal.py --max-images 1000
"""

import modal
from pathlib import Path

# Lightweight image for dataset preparation
image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("git", "wget", "curl")
    .pip_install("tqdm", "pillow", "requests", "pandas")
)

# Get the dataset volume
DATASET_DIR = "/root/datasets"
dataset_volume = modal.Volume.from_name("zimage-datasets", create_if_missing=True)

app = modal.App(
    name="setup-book-dataset",
    image=image
)


@app.function(
    volumes={DATASET_DIR: dataset_volume},
    timeout=7200,  # 2 hours for large downloads
)
def setup_dataset(max_images: int = None, use_test_data: bool = False):
    """
    Setup book cover dataset on Modal volume.
    
    Args:
        max_images: Maximum number of images to download (None for all)
        use_test_data: If True, create a small test dataset instead
    """
    import os
    import json
    import requests
    from pathlib import Path
    from tqdm import tqdm
    from PIL import Image
    import io
    
    remote_path = Path(DATASET_DIR) / "book_covers"
    remote_path.mkdir(parents=True, exist_ok=True)
    
    print("=" * 60)
    print("Setting up Book Cover Dataset on Modal")
    print("=" * 60)
    print(f"Target directory: {remote_path}")
    print()
    
    if use_test_data:
        print("Creating test dataset with sample book covers...")
        create_test_dataset(remote_path, max_images or 50)
    else:
        print("Downloading from Uchida Laboratory dataset...")
        print("Note: This will download images from Amazon URLs")
        print()
        download_uchida_dataset(remote_path, max_images)
    
    # Commit volume
    print()
    print("Committing volume...")
    dataset_volume.commit()
    print("✓ Volume committed")
    
    # Verify
    image_files = list(remote_path.glob("*.{jpg,jpeg,png}"))
    txt_files = list(remote_path.glob("*.txt"))
    
    print()
    print("=" * 60)
    print("Dataset setup complete!")
    print(f"  - Images: {len(image_files)}")
    print(f"  - Captions: {len(txt_files)}")
    print(f"  - Location: {remote_path}")
    print("=" * 60)


def create_test_dataset(output_path: Path, num_images: int):
    """Create a small test dataset with generated captions."""
    from PIL import Image
    
    print(f"Creating {num_images} test entries...")
    
    # Sample book cover descriptions for testing
    sample_captions = [
        "modern book cover, thriller novel, dark mysterious atmosphere, minimalist design, bold typography",
        "contemporary book cover, science fiction, futuristic cityscape, vibrant colors, geometric patterns",
        "book cover design, romance novel, elegant typography, soft pastel colors, floral elements",
        "modern book cover, fantasy novel, magical landscape, epic illustration, ornate borders",
        "contemporary book cover, mystery novel, noir style, dramatic shadows, vintage aesthetic",
        "book cover design, young adult fiction, bright colors, modern illustration, playful typography",
        "modern book cover, historical fiction, period-appropriate artwork, elegant design, classic typography",
        "book cover design, self-help book, clean minimalist style, inspirational imagery, modern typography",
        "contemporary book cover, horror novel, dark atmosphere, unsettling imagery, bold lettering",
        "modern book cover, business book, professional design, clean layout, corporate aesthetic",
    ]
    
    # Create placeholder images and captions
    for i in range(num_images):
        # Create a simple colored image as placeholder
        img = Image.new('RGB', (512, 768), color=(i*10 % 255, (i*20) % 255, (i*30) % 255))
        
        img_path = output_path / f"book_cover_{i:05d}.png"
        img.save(img_path)
        
        # Create caption
        caption = sample_captions[i % len(sample_captions)]
        caption_path = output_path / f"book_cover_{i:05d}.txt"
        caption_path.write_text(caption)
    
    print(f"✓ Created {num_images} test images with captions")


def download_uchida_dataset(output_path: Path, max_images: int = None):
    """Download images from Uchida dataset URLs."""
    import subprocess
    import codecs
    
    # Clone the repository to get metadata
    repo_path = Path("/tmp/uchida_dataset")
    if not repo_path.exists():
        print("Cloning Uchida dataset repository...")
        subprocess.run(
            ["git", "clone", "https://github.com/uchidalab/book-dataset.git", str(repo_path)],
            check=True,
            capture_output=True
        )
        print("✓ Repository cloned")
    
    # Find CSV files - prefer Task2 (full dataset) over Task1
    csv_files = []
    task2_csv = repo_path / "Task2" / "book32-listing.csv"
    if task2_csv.exists():
        csv_files.append(task2_csv)
    csv_files.extend(list((repo_path / "Task1").glob("*.csv")))
    
    if not csv_files:
        print("⚠ No CSV files found. Creating test dataset instead...")
        create_test_dataset(output_path, max_images or 100)
        return
    
    print(f"Found {len(csv_files)} CSV files")
    print(f"Using: {csv_files[0].name}")
    
    # Read CSV with proper format
    import pandas as pd
    
    header_names = ['Amazon ID (ASIN)', 'Filename', 'Image URL', 'Title', 'Author', 'Category ID', 'Category']
    
    downloaded = 0
    failed = 0
    
    csv_file = csv_files[0]
    try:
        print(f"Reading {csv_file.name}...")
        with codecs.open(csv_file, mode='r', encoding='utf-8', errors='ignore') as f:
            df = pd.read_csv(f, delimiter=",", header=None, names=header_names, quotechar='"')
        
        print(f"Found {len(df)} entries in CSV")
        
        # Download images
        total = min(len(df), max_images) if max_images else len(df)
        
        for idx, row in tqdm(df.iterrows(), total=total, desc="Downloading"):
            if max_images and downloaded >= max_images:
                break
            
            try:
                url = str(row['Image URL']).strip()
                if not url or 'http' not in url:
                    failed += 1
                    continue
                
                # Try to download image
                # Note: Amazon URLs might be outdated, so we'll try with a timeout
                try:
                    response = requests.get(url, timeout=15, stream=True, headers={
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                    })
                    
                    if response.status_code == 200:
                        img_data = response.content
                        if len(img_data) < 1000:  # Too small, probably error page
                            failed += 1
                            continue
                        
                        img = Image.open(io.BytesIO(img_data))
                        
                        # Convert to RGB if needed
                        if img.mode != 'RGB':
                            img = img.convert('RGB')
                        
                        # Check minimum size
                        if min(img.size) < 256:
                            failed += 1
                            continue
                        
                        # Save image
                        filename = str(row['Filename']).strip() or f"book_{downloaded:06d}.jpg"
                        if not filename.endswith(('.jpg', '.jpeg', '.png')):
                            filename = f"{filename}.jpg"
                        
                        img_path = output_path / filename
                        img.save(img_path, "JPEG", quality=90)
                        
                        # Create caption from metadata
                        title = str(row['Title']).strip()
                        author = str(row['Author']).strip()
                        category = str(row['Category']).strip()
                        
                        caption_parts = ["book cover"]
                        if category:
                            # Clean category name
                            category_clean = category.lower().replace('_', ' ').title()
                            caption_parts.append(f"{category_clean}")
                        if title:
                            # Use first few words of title
                            title_words = title.split()[:4]
                            if len(title_words) < len(title.split()):
                                caption_parts.append(f"titled '{' '.join(title_words)}...'")
                            else:
                                caption_parts.append(f"titled '{title}'")
                        caption_parts.extend(["modern design", "professional typography"])
                        
                        caption = ", ".join([p for p in caption_parts if p and p != ''])
                        
                        caption_path = output_path / f"{img_path.stem}.txt"
                        caption_path.write_text(caption)
                        
                        downloaded += 1
                    else:
                        failed += 1
                except requests.exceptions.RequestException:
                    failed += 1
                except Exception as e:
                    failed += 1
                    if failed % 50 == 0 and failed > 0:
                        print(f"  (Failed: {failed}, Downloaded: {downloaded})")
                    continue
                    
            except Exception as e:
                failed += 1
                continue
                
    except Exception as e:
        print(f"Error processing {csv_file}: {e}")
        import traceback
        traceback.print_exc()
        print("⚠ Error reading CSV. Creating test dataset instead...")
        create_test_dataset(output_path, max_images or 100)
        return
    
    print()
    print(f"Downloaded: {downloaded} images")
    print(f"Failed: {failed} URLs")
    
    if downloaded == 0:
        print("⚠ No images downloaded (URLs may be outdated). Creating test dataset instead...")
        create_test_dataset(output_path, max_images or 100)
    elif downloaded < 10:
        print("⚠ Very few images downloaded. You may want to use test dataset or check URLs.")


@app.local_entrypoint()
def main(max_images: int = None, use_test_data: bool = False):
    """
    Local entrypoint to setup dataset on Modal.
    
    Usage:
        modal run setup_book_dataset_on_modal.py --max-images 1000
        modal run setup_book_dataset_on_modal.py --use-test-data  # Create test dataset
    """
    setup_dataset.remote(max_images=max_images, use_test_data=use_test_data)

