# Book Cover Generator CLI

A simple command-line tool to generate book covers using the trained LoRA model (step 500 checkpoint).

## Features

- **Interactive Mode**: Answer prompts to build your book cover
- **Command Line Mode**: Pass all parameters via command line
- **Customizable**: Control title, author, genre, colors, mood, style, and more
- **Uses Trained LoRA**: Automatically uses the step 500 checkpoint from training

## Installation

The CLI uses the AI Toolkit from the parent directory. Make sure you have:
- Python 3.11+
- All dependencies installed (see parent directory)
- Access to the trained LoRA checkpoint

## Usage

### Interactive Mode

```bash
cd book_cover_cli
python book_cover_generator.py --interactive
```

You'll be prompted for:
- Book Title (required)
- Author Name (optional)
- Genre (optional)
- Color Scheme (optional)
- Mood/Atmosphere (optional)
- Style (optional)
- Typography Style (optional)
- Additional Elements (optional)

### Command Line Mode

```bash
# Basic example
python book_cover_generator.py --title "The Dark Forest" --author "Liu Cixin" --genre "science fiction"

# Full example with all options
python book_cover_generator.py \
    --title "The Dark Forest" \
    --author "Liu Cixin" \
    --genre "science fiction" \
    --color-scheme "dark cosmic" \
    --mood "mysterious" \
    --style "minimalist" \
    --typography "bold" \
    --elements "geometric patterns"

# Minimal example
python book_cover_generator.py --title "My Novel" --genre thriller
```

## Options

### Required
- `--title`: Book title (required unless using `--interactive`)

### Optional Inputs
- `--author`: Author name
- `--genre`: Genre (thriller, romance, sci-fi, fantasy, mystery, horror, etc.)
- `--color-scheme`: Color scheme (dark, vibrant, pastel, monochrome, neon, etc.)
- `--mood`: Mood/atmosphere (mysterious, inspiring, dramatic, playful, dark, etc.)
- `--style`: Design style (minimalist, bold, elegant, vintage, modern, etc.)
- `--typography`: Typography style (bold, elegant, modern, classic, sans-serif, etc.)
- `--elements`: Additional design elements (geometric patterns, floral, illustrations, etc.)

### Generation Options
- `--width`: Image width in pixels (default: 768)
- `--height`: Image height in pixels (default: 1024)
- `--steps`: Number of inference steps (default: 8, range: 4-8 recommended)
- `--seed`: Random seed (-1 for random, default: -1)
- `--output-dir`: Output directory (default: ./book_covers)
- `--lora-path`: Path to LoRA checkpoint (default: step 500 checkpoint)

## Examples

### Thriller Novel
```bash
python book_cover_generator.py \
    --title "The Silent Witness" \
    --author "Jane Smith" \
    --genre thriller \
    --color-scheme dark \
    --mood mysterious \
    --style minimalist
```

### Romance Novel
```bash
python book_cover_generator.py \
    --title "Summer Love" \
    --genre romance \
    --color-scheme pastel \
    --mood romantic \
    --elements floral
```

### Science Fiction
```bash
python book_cover_generator.py \
    --title "Beyond the Stars" \
    --genre "science fiction" \
    --color-scheme "vibrant neon" \
    --mood futuristic \
    --elements "geometric patterns"
```

### Fantasy Novel
```bash
python book_cover_generator.py \
    --title "The Magic Realm" \
    --genre fantasy \
    --color-scheme vibrant \
    --mood epic \
    --elements "ornate borders"
```

## Output

Generated book covers are saved to the output directory (default: `./book_covers/`) with:
- Image file (PNG format)
- Prompt text file (same name with .txt extension)

## Notes

- The tool uses the step 500 LoRA checkpoint by default
- Portrait orientation (768x1024) is optimized for book covers
- Generation is fast (8 steps) thanks to Z-Image Turbo
- The prompt is automatically constructed from your inputs

## Troubleshooting

**Error: LoRA not found**
- Check that the LoRA path is correct
- The default path assumes Modal volume is mounted
- Use `--lora-path` to specify a different location

**Out of Memory**
- Reduce image size: `--width 512 --height 768`
- Reduce steps: `--steps 4`

**Model not loading**
- Ensure you're in the correct directory
- Check that ai-toolkit-z_image_turbo is accessible
- Verify model path in the config

