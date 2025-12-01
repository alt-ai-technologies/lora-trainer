# How to Generate Images with Z-Image Turbo

This guide explains how to generate images using your Z-Image Turbo integration.

## Quick Start

### 1. Create a Generation Config File

Create a YAML configuration file (e.g., `config/generate_zimage.yaml`) with the following structure:

```yaml
---
job: generate  # tells the runner this is a generation job
config:
  name: "generate_zimage"
  process:
    - type: to_folder  # process images to a folder
      output_folder: "output/gen"  # where to save generated images
      device: cuda:0  # use cuda:0, or cpu if no GPU
      generate:
        sampler: "ddpm"  # sampler type (for Z-Image Turbo, flow matching is used internally)
        width: 1024
        height: 1024
        neg: ""  # negative prompt (not used for Z-Image Turbo flow matching, but can be left empty)
        seed: -1  # -1 for random seed, or specific number for reproducible results
        guidance_scale: 1  # Z-Image Turbo uses flow matching, guidance_scale should be 1
        sample_steps: 8  # 4-8 steps work well for turbo models (fast generation!)
        ext: ".png"  # output format: .png, .jpg, .jpeg, .webp
        prompt_file: false  # if true, creates a .txt file next to each image with the prompt
        
        # Your prompts - can be a list or a path to a text file
        prompts:
          - "a beautiful landscape with mountains and a lake"
          - "a cat wearing sunglasses, cyberpunk style"
          - "a futuristic city at sunset"
      
      model:
        # Use one of these options:
        # Option 1: Hugging Face Hub (downloads automatically)
        name_or_path: "Tongyi-MAI/Z-Image-Turbo"
        
        # Option 2: Local path (faster, no download needed)
        # name_or_path: "/home/nfmil/model_vault/Tongyi-MAI/Z-Image-Turbo"
        
        arch: "zimage"  # REQUIRED: identifies this as Z-Image Turbo model
        quantize: true  # recommended for 24GB VRAM
        quantize_te: true  # quantize text encoder
        dtype: bf16  # or float16
```

### 2. Run Image Generation

Navigate to the AI Toolkit directory and run:

```bash
cd ai-toolkit-z_image_turbo
python run.py config/generate_zimage.yaml
```

Or if your config is in a different location:

```bash
python run.py /path/to/your/config.yaml
```

### 3. Find Your Generated Images

Images will be saved to the `output_folder` specified in your config (e.g., `output/gen/`).

## Advanced Options

### Using a Prompt File

Instead of listing prompts in the YAML, you can use a text file with one prompt per line:

```yaml
generate:
  prompts: "/path/to/prompts.txt"
```

Example `prompts.txt`:
```
a photo of a cat
a photo of a dog
a beautiful sunset over the ocean
```

### Prompt Flags (Inline Overrides)

You can override settings per-prompt using flags:

```yaml
prompts:
  - "a cat --w 512 --h 512 --seed 42 --steps 4"
  - "a dog --w 1024 --h 1024 --steps 8"
```

Available flags:
- `--w` or `--width`: Image width
- `--h` or `--height`: Image height
- `--seed` or `--d`: Seed value
- `--steps` or `--s`: Number of inference steps
- `--cfg` or `--l`: Guidance scale (usually 1 for Z-Image Turbo)
- `--n`: Negative prompt

### Using a Trained LoRA

If you've trained a LoRA, you can load it during generation:

```yaml
model:
  name_or_path: "Tongyi-MAI/Z-Image-Turbo"
  arch: "zimage"
  inference_lora_path: "/path/to/your/trained_lora.safetensors"
  # or from Hub:
  # inference_lora_path: "username/lora-name"
```

### Multiple Sizes

Generate images at random sizes from a list:

```yaml
generate:
  size_list:
    - [512, 768]
    - [768, 1024]
    - [1024, 1024]
```

### Multiple Repeats

Generate multiple images from the same prompts:

```yaml
generate:
  num_repeats: 3  # generates 3 images per prompt
```

## Example Config Files

### Minimal Example

```yaml
---
job: generate
config:
  name: "simple_generate"
  process:
    - type: to_folder
      output_folder: "output/simple"
      device: cuda:0
      generate:
        width: 1024
        height: 1024
        sample_steps: 8
        guidance_scale: 1
        prompts:
          - "a beautiful landscape"
      model:
        name_or_path: "Tongyi-MAI/Z-Image-Turbo"
        arch: "zimage"
        quantize: true
```

### Full-Featured Example

```yaml
---
job: generate
config:
  name: "advanced_generate"
  process:
    - type: to_folder
      output_folder: "output/advanced"
      device: cuda:0
      generate:
        width: 1024
        height: 1024
        sample_steps: 8
        guidance_scale: 1
        seed: 42
        ext: ".png"
        prompt_file: true
        num_repeats: 2
        prompts:
          - "a cat wearing sunglasses --w 512 --h 512"
          - "a futuristic city --steps 4"
          - "a beautiful sunset"
      model:
        name_or_path: "/home/nfmil/model_vault/Tongyi-MAI/Z-Image-Turbo"
        arch: "zimage"
        quantize: true
        quantize_te: true
        dtype: bf16
        # inference_lora_path: "/path/to/lora.safetensors"  # uncomment to use a LoRA
```

## Important Notes for Z-Image Turbo

1. **Guidance Scale**: Z-Image Turbo uses flow matching, so `guidance_scale` should be set to `1` (it's not actually used, but the parameter is required).

2. **Steps**: Turbo models work well with 4-8 steps. More steps don't necessarily improve quality.

3. **Architecture**: Always set `arch: "zimage"` in your model config - this is required for the system to recognize and load the Z-Image Turbo model correctly.

4. **Training Adapter**: You don't need the training adapter (`assistant_lora_path`) for inference/generation - that's only needed during training.

5. **Memory**: With quantization enabled, you need at least 24GB VRAM. Without quantization, you'll need more.

## Troubleshooting

### Model Not Found
- Check that the model path is correct
- If using Hub path, ensure you're logged in: `huggingface-cli login`
- If using local path, verify the model exists: `ls -lh /home/nfmil/model_vault/Tongyi-MAI/Z-Image-Turbo/`

### Out of Memory
- Enable quantization: `quantize: true`
- Reduce image size: `width: 512, height: 512`
- Use CPU (slow): `device: cpu`

### Images Not Generating
- Check that `arch: "zimage"` is set in model config
- Verify your prompts are valid (not empty)
- Check the output folder exists and is writable

## Using the Web UI

The codebase also includes a web UI. You can access it by running the UI server (check the README for UI setup instructions). In the UI:
1. Select "Z-Image Turbo (w/ Training Adapter)" from the model dropdown
2. Enter your prompts
3. Configure generation settings
4. Generate images

## Next Steps

- **Train a LoRA**: See the README.md for training instructions
- **Use Modal**: See `modal_train_deploy.py` for cloud-based training/generation
- **Customize**: Modify the config to experiment with different settings

