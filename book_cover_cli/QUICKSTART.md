# Book Cover Generator - Quick Start

## Setup

1. **Download the LoRA checkpoint** (if running locally):
   ```bash
   python download_lora.py
   ```
   This downloads the step 500 checkpoint to `./lora_checkpoints/`

2. **Or use on Modal** (if running on Modal):
   The CLI will automatically find the LoRA in the Modal volume.

## Usage

### Interactive Mode (Easiest)

```bash
cd book_cover_cli
python book_cover_generator.py --interactive
```

Answer the prompts:
- Book Title: `The Dark Forest`
- Author Name: `Liu Cixin`
- Genre: `science fiction`
- Color Scheme: `dark cosmic`
- Mood: `mysterious`
- Style: `minimalist`
- Typography: `bold`
- Additional Elements: `geometric patterns`

### Command Line Mode

```bash
python book_cover_generator.py \
    --title "The Dark Forest" \
    --author "Liu Cixin" \
    --genre "science fiction" \
    --color-scheme "dark cosmic" \
    --mood "mysterious" \
    --style "minimalist"
```

### Minimal Example

```bash
python book_cover_generator.py --title "My Novel" --genre thriller
```

## Output

Generated covers are saved to `./book_covers/` (or your specified `--output-dir`) with:
- Image file (PNG)
- Prompt text file (.txt)

## Tips

- **Genre**: thriller, romance, sci-fi, fantasy, mystery, horror, young adult, historical, business, self-help
- **Color Schemes**: dark, vibrant, pastel, monochrome, neon, warm, cool, earthy
- **Moods**: mysterious, inspiring, dramatic, playful, dark, romantic, epic, professional
- **Styles**: minimalist, bold, elegant, vintage, modern, classic, contemporary
- **Typography**: bold, elegant, modern, classic, sans-serif, serif, decorative

## Examples by Genre

### Thriller
```bash
python book_cover_generator.py \
    --title "The Silent Witness" \
    --genre thriller \
    --color-scheme dark \
    --mood mysterious \
    --style minimalist
```

### Romance
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

### Fantasy
```bash
python book_cover_generator.py \
    --title "The Magic Realm" \
    --genre fantasy \
    --color-scheme vibrant \
    --mood epic \
    --elements "ornate borders"
```

## Using on Modal

If you want to run generation on Modal (for GPU access), you can use the existing `modal_generate_deploy.py` with a config that includes the LoRA path.

