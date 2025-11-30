# LoRA Trainer

Image generation scripts using Modal for cloud GPU execution.

## Setup

1. Install dependencies:
```bash
uv sync
```

2. Copy `.env.example` to `.env` and fill in your credentials:
```bash
cp .env.example .env
```

Required environment variables:
- `MODAL_TOKEN_ID` - Modal API token ID
- `MODAL_TOKEN_SECRET` - Modal API token secret
- `HF_TOKEN` - Hugging Face token (for gated models like FLUX.1-dev)

## Scripts

### [FLUX.1-dev](https://huggingface.co/black-forest-labs/FLUX.1-dev) (`flux_dev_gen.py`)
High-quality image generation with 50 inference steps.

```bash
uv run modal run flux_dev_gen.py --prompt "a cyberpunk cityscape at sunset"
```

### [Z-Image-Turbo](https://huggingface.co/Tongyi-MAI/Z-Image-Turbo) (`zimage_turbo_gen.py`)
Fast image generation with 9 inference steps.

```bash
uv run modal run zimage_turbo_gen.py --prompt "a robot in a garden"
```

## Options

Both scripts support:
- `--prompt` - Text prompt for image generation
- `--output` - Output file path (defaults to `output/` directory)
- `--seed` - Random seed for reproducibility

Z-Image-Turbo also supports LoRA and safety checking:
- `--lora` - HuggingFace LoRA repo ID
- `--lora-weight-name` - LoRA weights filename (auto-detected if repo has only one .safetensors file)
- `--lora-scale` - LoRA strength (default: 1.0)
- `--safe` - Block NSFW content (uses [Falconsai/nsfw_image_detection](https://huggingface.co/Falconsai/nsfw_image_detection))

Examples:
```bash
uv run modal run zimage_turbo_gen.py --prompt "a cat astronaut" --output output/cat.png --seed 42
```

With LoRA:
```bash
uv run modal run zimage_turbo_gen.py \
  --prompt "a cat playing piano" \
  --lora "ostris/z_image_turbo_childrens_drawings"
```

## Notes

- First run downloads model weights to a Modal volume (~30GB for FLUX). Subsequent runs load from cache.
- Generated images are saved to `output/` (gitignored).
- Cold start is ~20-60 seconds. Warm containers are instant.
