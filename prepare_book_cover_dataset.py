#!/usr/bin/env python3
"""
Script to prepare book cover dataset for LoRA training.

This script helps convert book cover datasets (especially Uchida Laboratory dataset)
into the format required for training: images with matching .txt caption files.

Usage:
    python prepare_book_cover_dataset.py --input /path/to/book/dataset --output /path/to/output
    python prepare_book_cover_dataset.py --input /path/to/book/dataset --output /path/to/output --metadata metadata.json
    python prepare_book_cover_dataset.py --input /path/to/book/dataset --output /path/to/output --auto-caption
"""

import argparse
import json
import os
import shutil
from pathlib import Path
from typing import Dict, Optional
import sys

try:
    from PIL import Image
    from transformers import BlipProcessor, BlipForConditionalGeneration
    BLIP_AVAILABLE = True
except ImportError:
    BLIP_AVAILABLE = False
    print("Warning: BLIP not available. Install with: pip install transformers pillow torch")


def load_metadata(metadata_path: str) -> Dict:
    """Load metadata from JSON file."""
    with open(metadata_path, 'r') as f:
        if metadata_path.endswith('.jsonl'):
            # JSONL format (one JSON object per line)
            metadata = {}
            for line in f:
                item = json.loads(line.strip())
                # Try to find image identifier
                img_id = item.get('image_id') or item.get('id') or item.get('file_name', '').split('.')[0]
                metadata[img_id] = item
            return metadata
        else:
            # Regular JSON format
            return json.load(f)


def create_caption_from_metadata(book_info: Dict, image_name: str) -> str:
    """Create a caption from book metadata."""
    title = book_info.get('title', '')
    author = book_info.get('author', '')
    category = book_info.get('category', '') or book_info.get('genre', '')
    
    # Build caption parts
    caption_parts = ["book cover"]
    
    if category:
        caption_parts.append(f"{category.lower()} novel")
    
    if title:
        # Add title context (but keep it short)
        title_words = title.split()[:3]  # First 3 words
        if len(title_words) < len(title.split()):
            caption_parts.append(f"titled '{' '.join(title_words)}...'")
    
    # Add style descriptors based on category
    style_map = {
        'thriller': 'dark mysterious atmosphere',
        'mystery': 'noir style, dramatic shadows',
        'romance': 'elegant, soft colors',
        'science fiction': 'futuristic, vibrant colors',
        'fantasy': 'magical, epic illustration',
        'horror': 'dark atmosphere, unsettling',
        'young adult': 'bright colors, modern illustration',
        'historical': 'period-appropriate, classic design',
        'business': 'professional, clean layout',
        'self-help': 'inspirational, minimalist'
    }
    
    for key, style in style_map.items():
        if key in category.lower():
            caption_parts.append(style)
            break
    
    # Always add modern/professional descriptors
    caption_parts.extend([
        "modern design",
        "professional typography"
    ])
    
    caption = ", ".join([p for p in caption_parts if p])
    return caption


def auto_caption_image(image_path: Path, blip_processor, blip_model) -> str:
    """Generate caption using BLIP model."""
    try:
        image = Image.open(image_path).convert('RGB')
        inputs = blip_processor(image, return_tensors="pt")
        out = blip_model.generate(**inputs, max_length=50, num_beams=3)
        caption = blip_processor.decode(out[0], skip_special_tokens=True)
        return f"book cover, {caption}"
    except Exception as e:
        print(f"Error captioning {image_path}: {e}")
        return "book cover, modern design, professional typography"


def prepare_dataset(
    input_path: str,
    output_path: str,
    metadata_path: Optional[str] = None,
    auto_caption: bool = False,
    min_size: int = 512,
    max_images: Optional[int] = None
):
    """
    Prepare book cover dataset for training.
    
    Args:
        input_path: Path to input images
        output_path: Path to output directory
        metadata_path: Optional path to metadata JSON/JSONL file
        auto_caption: Use BLIP to auto-generate captions
        min_size: Minimum image size (shortest side)
        max_images: Maximum number of images to process (None for all)
    """
    input_dir = Path(input_path)
    output_dir = Path(output_path)
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load metadata if provided
    metadata = {}
    if metadata_path:
        print(f"Loading metadata from {metadata_path}...")
        metadata = load_metadata(metadata_path)
        print(f"Loaded metadata for {len(metadata)} items")
    
    # Load BLIP model if auto-captioning
    blip_processor = None
    blip_model = None
    if auto_caption:
        if not BLIP_AVAILABLE:
            print("Error: BLIP not available. Install with: pip install transformers pillow torch")
            sys.exit(1)
        print("Loading BLIP model for auto-captioning...")
        blip_processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
        blip_model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")
        print("BLIP model loaded")
    
    # Find all images
    image_extensions = {'.jpg', '.jpeg', '.png', '.webp'}
    image_files = []
    for ext in image_extensions:
        image_files.extend(input_dir.rglob(f'*{ext}'))
        image_files.extend(input_dir.rglob(f'*{ext.upper()}'))
    
    print(f"Found {len(image_files)} images")
    
    if max_images:
        image_files = image_files[:max_images]
        print(f"Processing first {max_images} images")
    
    # Process images
    copied = 0
    skipped = 0
    errors = 0
    
    for img_path in image_files:
        try:
            # Check image size
            with Image.open(img_path) as img:
                width, height = img.size
                min_dim = min(width, height)
                
                if min_dim < min_size:
                    skipped += 1
                    continue
            
            # Copy image
            img_name = img_path.name
            output_img_path = output_dir / img_name
            shutil.copy2(img_path, output_img_path)
            
            # Create caption
            img_stem = img_path.stem
            
            if metadata_path and img_stem in metadata:
                caption = create_caption_from_metadata(metadata[img_stem], img_stem)
            elif auto_caption:
                caption = auto_caption_image(img_path, blip_processor, blip_model)
            else:
                # Default caption
                caption = "book cover, modern design, professional typography"
            
            # Save caption
            caption_path = output_dir / f"{img_stem}.txt"
            with open(caption_path, 'w', encoding='utf-8') as f:
                f.write(caption)
            
            copied += 1
            if copied % 100 == 0:
                print(f"Processed {copied} images...")
        
        except Exception as e:
            print(f"Error processing {img_path}: {e}")
            errors += 1
            continue
    
    print("\n" + "="*60)
    print(f"Dataset preparation complete!")
    print(f"  - Copied: {copied} images")
    print(f"  - Skipped (too small): {skipped} images")
    print(f"  - Errors: {errors} images")
    print(f"  - Output directory: {output_dir}")
    print("="*60)
    
    # Create a summary file
    summary = {
        "total_images": copied,
        "skipped": skipped,
        "errors": errors,
        "output_path": str(output_dir),
        "min_size": min_size
    }
    
    with open(output_dir / "dataset_summary.json", 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\nSummary saved to: {output_dir / 'dataset_summary.json'}")


def main():
    parser = argparse.ArgumentParser(
        description="Prepare book cover dataset for LoRA training"
    )
    parser.add_argument(
        '--input',
        required=True,
        help='Input directory containing book cover images'
    )
    parser.add_argument(
        '--output',
        required=True,
        help='Output directory for prepared dataset'
    )
    parser.add_argument(
        '--metadata',
        help='Path to metadata JSON/JSONL file (optional)'
    )
    parser.add_argument(
        '--auto-caption',
        action='store_true',
        help='Use BLIP to auto-generate captions (requires transformers)'
    )
    parser.add_argument(
        '--min-size',
        type=int,
        default=512,
        help='Minimum image size (shortest side) in pixels (default: 512)'
    )
    parser.add_argument(
        '--max-images',
        type=int,
        help='Maximum number of images to process (for testing)'
    )
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input):
        print(f"Error: Input directory does not exist: {args.input}")
        sys.exit(1)
    
    prepare_dataset(
        input_path=args.input,
        output_path=args.output,
        metadata_path=args.metadata,
        auto_caption=args.auto_caption,
        min_size=args.min_size,
        max_images=args.max_images
    )


if __name__ == '__main__':
    main()

