# Modal Image Generation Guide

This guide explains how to deploy and run Z-Image Turbo image generation on Modal cloud GPUs.

## 🚀 Quick Start

### 1. Prerequisites

**Install Modal CLI:**
```bash
pip install modal
```

**Authenticate with Modal:**
```bash
modal token new
```

**Set up Hugging Face secret (for model access):**
```bash
modal secret create huggingface \
  HF_TOKEN=your_huggingface_token_here
```

Get your token from: https://huggingface.co/settings/tokens

### 2. Run Image Generation

**Simple config:**
```bash
modal run modal_generate_deploy.py config/generate_zimage_simple.yaml
```

**Full-featured config:**
```bash
modal run modal_generate_deploy.py config/generate_zimage.yaml
```

**Multiple configs:**
```bash
modal run modal_generate_deploy.py config/gen1.yaml config/gen2.yaml --recover
```

## 📁 Generated Images

Images are saved to a persistent Modal volume. To download them:

```bash
# Download all generated images
modal volume download zimage-generation-outputs ./downloaded_images

# Or mount the volume to browse
modal volume mount zimage-generation-outputs ./mounted_volume
```

## ⚙️ Configuration

The Modal deployment script:
- Uses **A100 GPU** (40GB VRAM) - plenty for Z-Image Turbo
- Caches models in persistent volume (faster subsequent runs)
- Saves generated images to persistent volume
- Timeout: 1 hour (adjustable in script)

### Customize Config

Edit your config file before running:

```yaml
generate:
  prompts:
    - "your custom prompt here"
    - "another prompt"
  width: 1024
  height: 1024
  sample_steps: 8
```

## 💰 Cost Estimate

- **A100 GPU**: ~$1.10/hour
- **Generation time**: ~5-10 minutes (first run with model download)
- **Subsequent runs**: ~2-5 minutes (model cached)
- **Estimated cost per generation**: $0.10 - $0.20

## 🔍 Monitoring

**View logs in real-time:**
```bash
modal logs zimage-turbo-generation
```

**Check Modal dashboard:**
Visit https://modal.com/apps to see running functions and logs.

## 🎯 Features

- ✅ **Model Caching**: Models cached in persistent volume (first run downloads, subsequent runs use cache)
- ✅ **Persistent Storage**: Generated images saved to volume, accessible after job completes
- ✅ **High Memory**: A100 GPU with 40GB VRAM - no OOM issues
- ✅ **Fast**: Cloud GPU is much faster than local if you have memory constraints
- ✅ **Scalable**: Can run multiple generation jobs in parallel

## 📝 Example Workflow

1. **Create/edit config:**
   ```bash
   # Edit prompts in config file
   nano ai-toolkit-z_image_turbo/config/generate_zimage_simple.yaml
   ```

2. **Run generation:**
   ```bash
   modal run modal_generate_deploy.py config/generate_zimage_simple.yaml
   ```

3. **Wait for completion** (check Modal dashboard or logs)

4. **Download images:**
   ```bash
   modal volume download zimage-generation-outputs ./my_images
   ```

## 🔧 Troubleshooting

### "Secret not found"
Make sure you created the Hugging Face secret:
```bash
modal secret create huggingface HF_TOKEN=your_token
```

### "Config file not found"
Make sure you're running from the project root and the config path is correct:
```bash
# From project root
modal run modal_generate_deploy.py config/generate_zimage_simple.yaml
```

### "Timeout"
If generation takes longer than 1 hour, increase timeout in `modal_generate_deploy.py`:
```python
timeout=7200,  # 2 hours
```

### Model download slow
First run downloads the model (~31GB). Subsequent runs use cached model from volume.

## 🆚 Local vs Modal

| Feature | Local | Modal |
|---------|-------|-------|
| Memory | Limited (OOM issues) | 40GB VRAM |
| Speed | Depends on GPU | Fast (A100) |
| Cost | Free | ~$0.10-0.20 per run |
| Setup | Complex dependencies | Simple (just Modal CLI) |
| Storage | Local disk | Persistent volumes |

**Use Modal if:**
- You're running out of memory locally
- You want faster generation
- You don't want to manage dependencies
- You need to generate many images

## 📚 Related Files

- `modal_generate_deploy.py` - Main deployment script
- `config/generate_zimage_simple.yaml` - Simple generation config
- `config/generate_zimage.yaml` - Full-featured config
- `HOW_TO_GENERATE_IMAGES.md` - General generation guide

