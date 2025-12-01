# Modal Deployment Plan for Z-Image Turbo LoRA Training

## 📋 Overview

This plan outlines the complete deployment of the Z-Image Turbo training project to Modal, enabling cloud-based LoRA training with persistent model caching and output storage.

---

## 🎯 Objectives

1. **Deploy AI Toolkit with Z-Image Turbo** to Modal
2. **Enable LoRA training** on Modal's GPU infrastructure
3. **Cache models** to speed up subsequent runs
4. **Persist training outputs** (LoRAs, samples, checkpoints)
5. **Support dataset uploads** for training

---

## 🏗️ Architecture

### Components

1. **Modal App**: `zimage-turbo-training`
2. **Volumes**:
   - `hf-model-cache`: Hugging Face model cache (persistent)
   - `zimage-training-outputs`: Training outputs (LoRAs, samples, checkpoints)
   - `zimage-datasets`: Dataset storage (optional, for reusable datasets)
3. **Secrets**:
   - `huggingface`: HF_TOKEN for model access
4. **GPU**: A100 (40GB) - recommended for Z-Image Turbo with quantization

### File Structure

```
image_gen/
├── modal_train_deploy.py          # Main Modal deployment script
├── config/
│   └── modal/
│       └── modal_train_lora_zimage_turbo_24gb.yaml  # Modal-specific config
└── MODAL_DEPLOYMENT_PLAN.md        # This file
```

---

## 📝 Implementation Plan

### Phase 1: Create Modal Deployment Script

**File**: `modal_train_deploy.py`

**Features**:
- ✅ Modal image with all dependencies (PyTorch, AI Toolkit, etc.)
- ✅ Mount AI Toolkit code directory
- ✅ Mount config directory
- ✅ Mount dataset directory (optional)
- ✅ Volume for HF model cache
- ✅ Volume for training outputs
- ✅ GPU configuration (A100)
- ✅ Environment variables (HF_HUB_ENABLE_HF_TRANSFER, etc.)
- ✅ Job execution using `get_job()` from AI Toolkit

**Key Differences from `run_modal.py`**:
- Updated dependencies for Z-Image Turbo
- Z-Image Turbo specific model paths
- Training adapter support
- Updated volume names

### Phase 2: Create Modal-Specific Config

**File**: `ai-toolkit-z_image_turbo/config/examples/modal/modal_train_lora_zimage_turbo_24gb.yaml`

**Features**:
- ✅ Training folder set to Modal volume path
- ✅ Dataset path pointing to mounted dataset directory
- ✅ Z-Image Turbo model configuration
- ✅ Training adapter path (Hub or local)
- ✅ Optimized settings for 24GB VRAM
- ✅ Sample prompts for monitoring training

### Phase 3: Dataset Management

**Options**:

1. **Mount Local Dataset** (Recommended for small datasets)
   - Mount dataset folder from local machine
   - Fast for small datasets (< 1GB)
   - No upload time

2. **Upload to Modal Volume** (Recommended for large/reusable datasets)
   - Upload dataset to `zimage-datasets` volume
   - Reusable across training runs
   - Persistent storage

3. **Use Hugging Face Datasets** (Future enhancement)
   - Load datasets directly from Hugging Face Hub

### Phase 4: Model Caching Strategy

**HF Model Cache Volume**:
- Location: `/root/.cache/huggingface`
- Volume: `hf-model-cache`
- Caches:
  - Base model: `Tongyi-MAI/Z-Image-Turbo` (~31 GB)
  - Training adapter: `ostris/zimage_turbo_training_adapter` (~163 MB)
- **First run**: Downloads models (~5-10 minutes)
- **Subsequent runs**: Uses cache (~30 seconds to load)

---

## 🚀 Deployment Steps

### Step 1: Setup Modal Secrets

```bash
# Set up Hugging Face token (if not already done)
modal secret create huggingface HF_TOKEN=your_token_here
```

### Step 2: Prepare Dataset

**Option A: Local Dataset (Small)**
```bash
# Organize your dataset locally
dataset/
├── image1.jpg
├── image1.txt
├── image2.jpg
├── image2.txt
└── ...
```

**Option B: Upload to Volume (Large/Reusable)**
```bash
# Upload dataset to Modal volume (after deployment script is ready)
# This will be done via Modal CLI or script
```

### Step 3: Create Training Config

```bash
# Copy the Modal example config
cp ai-toolkit-z_image_turbo/config/examples/modal/modal_train_lora_zimage_turbo_24gb.yaml \
   ai-toolkit-z_image_turbo/config/my_training.yaml

# Edit the config:
# - Update dataset path
# - Adjust training parameters (steps, batch size, etc.)
# - Set output name
```

### Step 4: Deploy and Run

```bash
# Run training on Modal
modal run modal_train_deploy.py config/my_training.yaml
```

---

## 📊 Expected Performance

### First Run (Cold Start)
- **Image build**: ~5-10 minutes (one-time)
- **Model download**: ~5-10 minutes (one-time, cached after)
- **Training setup**: ~2-3 minutes
- **Training**: Depends on steps (2000 steps ≈ 30-60 minutes)

### Subsequent Runs (Warm Start)
- **Image build**: Skipped (cached)
- **Model load**: ~30 seconds (from cache)
- **Training setup**: ~1-2 minutes
- **Training**: Same as first run

### Cost Estimate (A100 GPU)
- **A100**: ~$1.10/hour
- **2000 steps training**: ~$0.50-$1.00 per run
- **Volume storage**: ~$0.10/GB/month

---

## 🔧 Configuration Details

### Modal Deployment Script (`modal_train_deploy.py`)

**Key Features**:
```python
# Volumes
hf_cache_volume = modal.Volume.from_name("hf-model-cache", create_if_missing=True)
training_output_volume = modal.Volume.from_name("zimage-training-outputs", create_if_missing=True)
dataset_volume = modal.Volume.from_name("zimage-datasets", create_if_missing=True)  # Optional

# Mounts
- AI Toolkit code: /root/ai-toolkit-z_image_turbo
- Config directory: /root/config
- Dataset directory: /root/datasets (optional)

# GPU
gpu="A100"  # 40GB VRAM

# Timeout
timeout=7200  # 2 hours (adjust based on training steps)
```

### Training Config (`modal_train_lora_zimage_turbo_24gb.yaml`)

**Key Settings**:
```yaml
training_folder: "/root/modal_output"  # Must match volume mount
datasets:
  - folder_path: "/root/datasets/my_dataset"  # Or volume path
model:
  name_or_path: "Tongyi-MAI/Z-Image-Turbo"  # Hub path (auto-downloads)
  arch: "zimage"
  assistant_lora_path: "ostris/zimage_turbo_training_adapter/zimage_turbo_training_adapter_v1.safetensors"
  quantize: true
train:
  steps: 2000
  batch_size: 1
  gradient_accumulation_steps: 4
```

---

## 📦 Volume Management

### Creating Volumes

Volumes are created automatically on first use with `create_if_missing=True`.

### Viewing Volume Contents

```bash
# View training outputs
modal volume show zimage-training-outputs

# View model cache
modal volume show hf-model-cache
```

### Downloading Results

```bash
# Download trained LoRA
modal volume download zimage-training-outputs /path/to/output /local/path
```

### Clearing Cache (if needed)

```bash
# Delete and recreate volume (WARNING: Deletes all cached models)
modal volume delete hf-model-cache
```

---

## 🐛 Troubleshooting

### Issue: Models Not Downloading

**Solution**:
- Check HF token is set: `modal secret list`
- Verify token has access to models
- Check model license acceptance on Hugging Face

### Issue: Out of Memory

**Solution**:
- Ensure `quantize: true` in config
- Reduce `batch_size` to 1
- Increase `gradient_accumulation_steps`
- Enable `low_vram: true` (slower but uses less VRAM)

### Issue: Dataset Not Found

**Solution**:
- Verify dataset path in config matches mount path
- Check dataset is mounted or uploaded to volume
- Ensure image/caption pairs exist

### Issue: Training Adapter Not Loading

**Solution**:
- Verify `assistant_lora_path` is correct
- Check Hub path format: `org/repo/filename.safetensors`
- Ensure HF token has access

---

## 🔄 Workflow Example

### Complete Training Workflow

```bash
# 1. Setup (one-time)
modal secret create huggingface HF_TOKEN=your_token

# 2. Prepare dataset locally
mkdir -p dataset
# Add images and captions...

# 3. Create config
cp ai-toolkit-z_image_turbo/config/examples/modal/modal_train_lora_zimage_turbo_24gb.yaml \
   ai-toolkit-z_image_turbo/config/my_style_lora.yaml

# Edit config:
# - name: "my_style_lora_v1"
# - folder_path: "/root/datasets/my_style"
# - steps: 2000

# 4. Run training
modal run modal_train_deploy.py config/my_style_lora.yaml

# 5. Monitor progress
# View logs in Modal dashboard or terminal output

# 6. Download results
modal volume download zimage-training-outputs \
  /root/modal_output/my_style_lora_v1 \
  ./outputs/my_style_lora_v1
```

---

## 📈 Optimization Tips

### Speed Up Training

1. **Use cached models**: First run downloads, subsequent runs are faster
2. **Optimize dataset**: Pre-process and cache latents
3. **Adjust batch size**: Balance between speed and memory
4. **Use gradient accumulation**: Simulate larger batch sizes

### Reduce Costs

1. **Monitor training**: Stop early if results are good
2. **Use appropriate GPU**: A100 for 24GB, H100 for larger models
3. **Clean up volumes**: Delete old outputs periodically
4. **Share model cache**: Same cache works for multiple training runs

### Improve Results

1. **Quality dataset**: Clean, well-captioned images
2. **Appropriate steps**: 500-4000 steps typically good
3. **Learning rate**: 1e-4 is a good starting point
4. **EMA**: Keep enabled for smoother training

---

## 🔐 Security Considerations

1. **Secrets**: Never commit HF tokens to git
2. **Private models**: Use Modal secrets for private model access
3. **Dataset privacy**: Be aware datasets are uploaded to Modal
4. **Output privacy**: Training outputs stored in Modal volumes

---

## 📚 Next Steps

1. ✅ Create `modal_train_deploy.py`
2. ✅ Create `modal_train_lora_zimage_turbo_24gb.yaml`
3. ⏭ Test deployment with small dataset
4. ⏭ Verify model caching works
5. ⏭ Test full training run
6. ⏭ Document any issues and solutions
7. ⏭ Create helper scripts for common tasks

---

## 🎯 Success Criteria

- ✅ Training runs successfully on Modal
- ✅ Models are cached between runs
- ✅ Training outputs are persisted
- ✅ Datasets can be easily uploaded/used
- ✅ Cost is reasonable (< $2 per training run)
- ✅ Results are downloadable
- ✅ Documentation is complete

---

**Last Updated**: 2025-11-30

