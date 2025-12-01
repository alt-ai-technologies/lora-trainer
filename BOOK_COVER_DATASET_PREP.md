# Book Cover Dataset Preparation Guide

This guide will help you prepare a book cover dataset for training a LoRA on Z-Image Turbo.

## Recommended Dataset: Uchida Laboratory Book Cover Dataset

The **Uchida Laboratory Book Cover Dataset** is the largest available with 207,572 book covers from Amazon, including:
- Cover images
- Titles
- Authors
- Categories

**Source**: https://github.com/uchidalab/book-dataset

## Dataset Format Requirements

The training system requires:
- **Images**: `.jpg`, `.jpeg`, `.png`, or `.webp` format
- **Captions**: `.txt` files with the **exact same name** as the image
  - Example: `book_001.jpg` → `book_001.txt`
  - Caption file should contain a text description of the book cover

## Dataset Preparation Steps

### Option 1: Using Uchida Laboratory Dataset

1. **Download the dataset**:
   ```bash
   git clone https://github.com/uchidalab/book-dataset.git
   cd book-dataset
   ```

2. **Extract images** (if compressed):
   - The dataset may come in compressed format
   - Extract all book cover images to a single folder

3. **Create captions**:
   The dataset includes metadata (titles, authors, categories). You'll need to create caption files.
   
   You can use the provided Python script (see below) or manually create captions.

4. **Organize the dataset**:
   ```
   /root/datasets/book_covers/
     ├── book_001.jpg
     ├── book_001.txt
     ├── book_002.jpg
     ├── book_002.txt
     └── ...
   ```

### Option 2: Using Your Own Book Cover Collection

1. **Collect book cover images**:
   - Gather modern book covers (2010-present recommended for "modern" style)
   - Ensure images are high quality (at least 512px on shortest side)
   - Save as `.jpg`, `.jpeg`, or `.png`

2. **Create captions**:
   - For each image, create a `.txt` file with the same name
   - Include descriptive text about the cover design, genre, style, etc.
   - Example caption: "modern book cover, thriller novel, dark mysterious atmosphere, minimalist design, bold typography"

## Caption Guidelines

Good captions for book covers should include:
- **Genre/style**: thriller, romance, sci-fi, fantasy, etc.
- **Visual style**: minimalist, bold, elegant, vintage, modern, etc.
- **Color palette**: dark, vibrant, pastel, etc.
- **Design elements**: typography style, illustrations, patterns, etc.
- **Atmosphere/mood**: mysterious, inspiring, dramatic, etc.

**Example captions**:
- "modern book cover, science fiction novel, futuristic cityscape, vibrant neon colors, geometric patterns, bold sans-serif typography"
- "contemporary book cover, romance novel, elegant serif typography, soft pastel colors, floral decorative elements, clean layout"
- "book cover design, thriller novel, noir aesthetic, dramatic shadows, vintage film grain, bold lettering, dark atmosphere"

## Automated Caption Generation Script

If you have metadata (titles, authors, categories), you can use this Python script to generate captions:

```python
import os
from pathlib import Path
import json

def create_captions_from_metadata(dataset_path, metadata_file, output_path):
    """
    Create caption files from metadata JSON.
    
    Args:
        dataset_path: Path to folder containing book cover images
        metadata_file: Path to JSON file with metadata (title, author, category)
        output_path: Path where caption files will be created
    """
    # Load metadata
    with open(metadata_file, 'r') as f:
        metadata = json.load(f)
    
    # Create output directory
    os.makedirs(output_path, exist_ok=True)
    
    # Process each image
    for image_file in Path(dataset_path).glob('*.{jpg,jpeg,png}'):
        image_name = image_file.stem
        
        # Find matching metadata (adjust based on your metadata structure)
        # This is a placeholder - adjust to match your metadata format
        book_info = metadata.get(image_name, {})
        
        title = book_info.get('title', 'book')
        author = book_info.get('author', '')
        category = book_info.get('category', 'book')
        
        # Create caption
        caption_parts = [
            f"book cover",
            f"{category} novel" if category else "",
            f"by {author}" if author else "",
            "modern design",
            "professional typography"
        ]
        caption = ", ".join([p for p in caption_parts if p])
        
        # Save caption file
        caption_path = Path(output_path) / f"{image_name}.txt"
        with open(caption_path, 'w') as f:
            f.write(caption)
        
        print(f"Created caption: {caption_path}")

# Usage example:
# create_captions_from_metadata(
#     dataset_path="/path/to/images",
#     metadata_file="/path/to/metadata.json",
#     output_path="/path/to/images"  # same folder as images
# )
```

## Using BLIP or CLIP for Auto-Captioning

If you don't have metadata, you can use image captioning models:

1. **BLIP (Bootstrapping Language-Image Pre-training)**:
   ```python
   from transformers import BlipProcessor, BlipForConditionalGeneration
   from PIL import Image
   
   processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
   model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")
   
   def caption_image(image_path):
       image = Image.open(image_path)
       inputs = processor(image, return_tensors="pt")
       out = model.generate(**inputs, max_length=50)
       caption = processor.decode(out[0], skip_special_tokens=True)
       return f"book cover, {caption}"
   ```

2. **CLIP Interrogator** (can extract style/artistic descriptions)

## Uploading Dataset to Modal

### Option 1: Upload to Modal Volume (Recommended for Large Datasets)

```bash
# Create a Modal volume mount point
modal volume create zimage-datasets

# Upload your dataset (example using Modal CLI)
# You may need to write a script to upload files
```

### Option 2: Mount Local Dataset

If running Modal from your local machine, you can mount the dataset:

```python
# In modal_train_deploy.py, the dataset volume is already set up:
# DATASET_DIR = "/root/datasets"
# dataset_volume = modal.Volume.from_name("zimage-datasets", create_if_missing=True)
```

## Dataset Quality Tips

1. **Filter low-quality images**:
   - Remove images smaller than 512px on shortest side
   - Remove corrupted or unreadable images
   - Remove non-book-cover images if dataset is mixed

2. **Focus on modern covers** (for "modern book cover" training):
   - Prioritize covers from 2010-present
   - Look for contemporary design trends
   - Include diverse genres and styles

3. **Caption quality**:
   - Be descriptive but concise
   - Include genre, style, and key visual elements
   - Consistent formatting helps training

4. **Dataset size**:
   - Minimum: 100-200 images (for basic LoRA)
   - Recommended: 1,000-5,000 images (for good results)
   - Optimal: 10,000+ images (for comprehensive style learning)

## Training Configuration

Once your dataset is prepared, update the config file:

```yaml
datasets:
  - folder_path: "/root/datasets/book_covers"  # Your dataset path
    caption_ext: "txt"
    resolution: [ 512, 768, 1024 ]  # Portrait-oriented for book covers
```

Then run training:

```bash
modal run modal_train_deploy.py config/examples/modal/modal_train_lora_book_covers.yaml
```

## Next Steps

1. Download and prepare your book cover dataset
2. Create caption files for each image
3. Upload to Modal volume or mount locally
4. Update the config file with your dataset path
5. Start training!

For questions or issues, refer to the main training documentation.

