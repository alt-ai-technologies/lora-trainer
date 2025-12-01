# Book Cover Generator - Output Information

## File Location

**Default Output Directory**: `./book_covers` (relative to where you run the script)

**Full Path**: `/home/nfmil/projects/image_gen/book_cover_cli/book_covers`

## File Naming Convention

Generated files follow this pattern:
- **Image files**: `[timestamp]_[count].png`
  - `[timestamp]` = milliseconds since epoch (e.g., `1701234567890`)
  - `[count]` = zero-padded image number (e.g., `0`, `01`, `02`)
  - Example: `1701234567890_0.png`

- **Prompt files** (if `prompt_file: true`): `[timestamp]_[count].txt`
  - Contains the exact prompt used for generation
  - Example: `1701234567890_0.txt`

## Customizing Output Location

You can specify a custom output directory using the `--output-dir` argument:

```bash
python book_cover_generator.py \
    --title "My Book" \
    --genre thriller \
    --output-dir "/path/to/my/covers"
```

Or use a relative path:
```bash
python book_cover_generator.py \
    --title "My Book" \
    --genre thriller \
    --output-dir "../my_covers"
```

## Current Status

- **Output directory exists**: ✓ `/home/nfmil/projects/image_gen/book_cover_cli/book_covers`
- **Directory is empty**: Currently no generated files
- **Ready for generation**: ✓

## Checking Generated Files

After running generation, check the output directory:

```bash
cd /home/nfmil/projects/image_gen/book_cover_cli
ls -lh book_covers/
```

You should see:
- `.png` files (the generated book cover images)
- `.txt` files (the prompts used, if `prompt_file: true`)

