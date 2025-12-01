# Book Cover LoRA Training - Quick Start Guide

This guide will help you train a LoRA for generating modern book covers using Z-Image Turbo.

## What's Been Set Up

1. **Training Config**: `ai-toolkit-z_image_turbo/config/examples/modal/modal_train_lora_book_covers.yaml`
   - Configured for Z-Image Turbo model
   - Portrait-oriented resolutions (768x1024) for book covers
   - Book cover-specific sample prompts
   - Optimized training parameters

2. **Dataset Prep Script**: `prepare_book_cover_dataset.py`
   - Automates dataset preparation
   - Supports metadata-based captions
   - Optional BLIP auto-captioning
   - Filters low-quality images

3. **Documentation**: `BOOK_COVER_DATASET_PREP.md`
   - Detailed dataset preparation guide
   - Caption guidelines
   - Dataset recommendations

## Quick Start (3 Steps)

### Step 1: Prepare Your Dataset

**Option A: Using Uchida Laboratory Dataset (Recommended)**
```bash
# Download the dataset
git clone https://github.com/uchidalab/book-dataset.git
cd book-dataset

# Prepare the dataset (adjust paths as needed)
python ../prepare_book_cover_dataset.py \
    --input /path/to/book-dataset/images \
    --output /path/to/prepared_dataset \
    --metadata /path/to/metadata.json \
    --min-size 512
```

**Option B: Using Your Own Collection**
```bash
python prepare_book_cover_dataset.py \
    --input /path/to/your/book/covers \
    --output /path/to/prepared_dataset \
    --auto-caption \
    --min-size 512
```

### Step 2: Upload Dataset to Modal (or use local mount)

If using Modal volume:
```bash
# The dataset volume is already configured in modal_train_deploy.py
# Upload your prepared dataset to the Modal volume
# Or mount it when running Modal
```

### Step 3: Update Config and Train

1. **Update the dataset path** in the config file:
   ```yaml
   datasets:
     - folder_path: "/root/datasets/book_covers"  # Your dataset path
   ```

2. **Run training**:
   ```bash
   modal run modal_train_deploy.py config/examples/modal/modal_train_lora_book_covers.yaml
   ```

## Configuration Details

The training config is optimized for book covers:

- **Resolutions**: `[512, 768, 1024]` - Portrait-oriented for book covers
- **Steps**: `3000` - Increased for better style learning
- **Sample Size**: `768x1024` - Portrait aspect ratio
- **Sample Prompts**: 10 book cover-specific prompts for testing

## Expected Results

After training, you'll get:
- LoRA weights saved in `/root/modal_output` (or your configured output folder)
- Sample images generated during training
- Checkpoints saved every 250 steps

## Using Your Trained LoRA

Once training is complete, use your LoRA for generation:

```yaml
model:
  name_or_path: "Tongyi-MAI/Z-Image-Turbo"
  arch: "zimage"
  inference_lora_path: "/path/to/your/trained_lora.safetensors"
```

## Tips for Best Results

1. **Dataset Quality**:
   - Use 1,000-5,000+ high-quality book covers
   - Focus on modern covers (2010-present) for "modern" style
   - Include diverse genres and design styles

2. **Captions**:
   - Be descriptive: include genre, style, colors, typography
   - Example: "modern book cover, thriller novel, dark mysterious atmosphere, minimalist design, bold typography"

3. **Training**:
   - Monitor sample images during training
   - Adjust steps if needed (500-4000 range)
   - Save checkpoints regularly

4. **Generation**:
   - Use portrait aspect ratios (e.g., 768x1024)
   - Include "book cover" in your prompts
   - Reference the style you want: "modern", "minimalist", "bold", etc.

## Troubleshooting

**Out of Memory**:
- Already using quantization (8-bit)
- Try reducing batch size or gradient accumulation

**Poor Results**:
- Check caption quality
- Ensure dataset has consistent style
- Increase training steps
- Verify dataset path is correct

**Dataset Not Found**:
- Check Modal volume is mounted correctly
- Verify dataset path in config matches actual location
- Ensure images and captions are in the same folder

## Next Steps

- See `BOOK_COVER_DATASET_PREP.md` for detailed dataset preparation
- See `HOW_TO_GENERATE_IMAGES.md` for generation instructions
- See `MODAL_LAUNCH.md` for Modal setup

Happy training! 🎨📚

