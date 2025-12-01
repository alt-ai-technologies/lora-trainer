# Z-Image Turbo Integration Plan

**Date:** 2025-11-30  
**Repository:** `ai-toolkit-z_image_turbo`  
**Target:** Full integration of Z-Image Turbo with training adapter support

---

## Current Status

✅ **Already Implemented:**
- Core `ZImageModel` class (`extensions_built_in/diffusion_models/z_image/z_image.py`)
- Training adapter loading logic
- UI integration (`ui/src/app/jobs/new/options.ts`)
- Model registration in `AI_TOOLKIT_MODELS`

⚠️ **Needs Fixing:**
- ModelArch type definition missing `'zimage'`
- Config parsing logic missing `'zimage'` handling
- Missing example config file

---

## Integration Tasks

### Phase 1: Fix Configuration System (Priority: High)

#### Task 1.1: Add 'zimage' to ModelArch Type
**File:** `toolkit/config_modules.py`  
**Line:** 556

**Change:**
```python
# Before
ModelArch = Literal['sd1', 'sd2', 'sd3', 'sdxl', 'pixart', 'pixart_sigma', 'auraflow', 'flux', 'flex1', 'flex2', 'lumina2', 'vega', 'ssd', 'wan21']

# After
ModelArch = Literal['sd1', 'sd2', 'sd3', 'sdxl', 'pixart', 'pixart_sigma', 'auraflow', 'flux', 'flex1', 'flex2', 'lumina2', 'vega', 'ssd', 'wan21', 'zimage']
```

**Estimated Time:** 5 minutes  
**Risk:** Low

---

#### Task 1.2: Add 'zimage' Handling in Config Parsing
**File:** `toolkit/config_modules.py`  
**Lines:** 682-728

**Change:**
```python
# Add after line 703 (after 'ssd' handling)
elif self.arch == 'zimage':
    # Z-Image doesn't need special flags, but we document it for consistency
    pass
```

**Estimated Time:** 5 minutes  
**Risk:** Low

---

### Phase 2: Create Example Config (Priority: Medium)

#### Task 2.1: Create Example Config File
**File:** `config/examples/train_lora_zimage_turbo_24gb.yaml`

**Content:** See suggested config below

**Estimated Time:** 15 minutes  
**Risk:** Low

---

### Phase 3: Download Required Models (Priority: High)

#### Task 3.1: Download Base Model
**Model:** `Tongyi-MAI/Z-Image-Turbo`  
**Location:** `/home/nfmil/model_vault/Tongyi-MAI/Z-Image-Turbo`

**Components to download:**
- `transformer/` directory (main model weights)
- `text_encoder/` directory (Qwen3ForCausalLM)
- `tokenizer/` directory
- `vae/` directory (AutoencoderKL)
- `scheduler/` directory (if exists)
- Model card and config files

**Estimated Time:** 30-60 minutes (depends on download speed)  
**Size:** ~20-30 GB

---

#### Task 3.2: Download Training Adapter
**Model:** `ostris/zimage_turbo_training_adapter`  
**Location:** `/home/nfmil/model_vault/ostris/zimage_turbo_training_adapter`

**Files to download:**
- `zimage_turbo_training_adapter_v1.safetensors`
- Model card and README

**Estimated Time:** 5-10 minutes  
**Size:** ~100-500 MB

---

### Phase 4: Testing & Validation (Priority: High)

#### Task 4.1: Unit Tests
- [ ] Test model loading with local paths
- [ ] Test training adapter loading
- [ ] Test model loading without adapter
- [ ] Test LoRA weight conversion

**Estimated Time:** 2-3 hours

---

#### Task 4.2: Integration Tests
- [ ] Test end-to-end training run (short, 1-2 epochs)
- [ ] Test inference with trained LoRA
- [ ] Test checkpoint save/load
- [ ] Test with different VRAM configurations

**Estimated Time:** 4-6 hours

---

#### Task 4.3: Manual Testing
- [ ] Test UI workflow: create job → train → generate samples
- [ ] Test with different dataset sizes
- [ ] Test with different resolutions
- [ ] Verify training adapter is properly removed during inference

**Estimated Time:** 2-3 hours

---

### Phase 5: Documentation (Priority: Medium)

#### Task 5.1: Update README.md
**File:** `README.md`

**Add section:**
```markdown
## Z-Image Turbo Training

### Requirements
- GPU with at least 24GB VRAM (with quantization)
- Hugging Face account with access to Tongyi-MAI/Z-Image-Turbo

### Setup
1. Accept the model license on Hugging Face: [Tongyi-MAI/Z-Image-Turbo](https://huggingface.co/Tongyi-MAI/Z-Image-Turbo)
2. Run `huggingface-cli login` with your READ token
3. Download models to your model vault (see below)

### Training
1. Copy `config/examples/train_lora_zimage_turbo_24gb.yaml` to `config/`
2. Edit the config with your dataset path
3. Run: `python run.py config/your_config.yaml`

### Training Adapter
The training adapter (`ostris/zimage_turbo_training_adapter`) is required for training. It preserves the turbo speed while allowing fine-tuning. See [Training Adapter Explanation](../Z-Image-Turbo/TRAINING_ADAPTER_EXPLANATION.md) for details.
```

**Estimated Time:** 30 minutes

---

#### Task 5.2: Create Quick Start Guide
**File:** `docs/Z_IMAGE_TURBO_QUICKSTART.md`

**Content:**
- Quick setup instructions
- Example dataset preparation
- Common issues and solutions

**Estimated Time:** 1 hour

---

## Example Config File

**File:** `config/examples/train_lora_zimage_turbo_24gb.yaml`

```yaml
# Example config for training Z-Image Turbo LoRA
# Based on the UI defaults and similar to FLUX schnell config
# Requires: 24GB+ VRAM with quantization enabled

config:
  output_name: "zimage_turbo_lora"
  output_folder: "./output"
  
  process:
    - type: "train"
      model:
        name_or_path: "Tongyi-MAI/Z-Image-Turbo"  # Or local path: "/home/nfmil/model_vault/Tongyi-MAI/Z-Image-Turbo"
        arch: "zimage"
        assistant_lora_path: "ostris/zimage_turbo_training_adapter/zimage_turbo_training_adapter_v1.safetensors"  # Or local path
        quantize: true
        quantize_te: true
        low_vram: true
        qtype: "qfloat8"
        # Optional: layer_offloading for even lower VRAM usage
        # layer_offloading: true
        # layer_offloading_transformer_percent: 0.5
      
      train:
        dataset_folder: "./dataset"  # Update with your dataset path
        batch_size: 1
        gradient_accumulation: 4
        epochs: 10
        save_every_n_epochs: 1
        noise_scheduler: "flowmatch"
        timestep_type: "weighted"
        unload_text_encoder: false
        learning_rate: 1e-4
        optimizer: "adamw8bit"
      
      network:
        type: "lora"
        linear: 128
        linear_alpha: 128
        transformer_only: true
      
      sample:
        sampler: "flowmatch"
        sample_steps: 8  # Turbo models use fewer steps
        guidance_scale: 1  # Turbo models typically use guidance_scale: 1
        width: 1024
        height: 1024
        sample_every_n_epochs: 1
        prompts:
          - "a photo of a cat"
          - "a photo of a dog"
```

---

## Model Download Script

**File:** `scripts/download_zimage_models.sh`

```bash
#!/bin/bash

# Download Z-Image Turbo models to model vault
MODEL_VAULT="/home/nfmil/model_vault"

echo "Downloading Z-Image Turbo models..."

# Download base model
echo "Downloading Tongyi-MAI/Z-Image-Turbo..."
huggingface-cli download Tongyi-MAI/Z-Image-Turbo \
    --local-dir "${MODEL_VAULT}/Tongyi-MAI/Z-Image-Turbo" \
    --local-dir-use-symlinks False

# Download training adapter
echo "Downloading ostris/zimage_turbo_training_adapter..."
huggingface-cli download ostris/zimage_turbo_training_adapter \
    --local-dir "${MODEL_VAULT}/ostris/zimage_turbo_training_adapter" \
    --local-dir-use-symlinks False

echo "Download complete!"
echo "Models are available at:"
echo "  Base: ${MODEL_VAULT}/Tongyi-MAI/Z-Image-Turbo"
echo "  Adapter: ${MODEL_VAULT}/ostris/zimage_turbo_training_adapter"
```

---

## Implementation Order

1. ✅ **Phase 3: Download Models** (Do first - takes longest)
2. ✅ **Phase 1: Fix Configuration** (Quick fixes)
3. ✅ **Phase 2: Create Example Config** (Quick)
4. ✅ **Phase 4: Testing** (Validate everything works)
5. ✅ **Phase 5: Documentation** (Final polish)

---

## Success Criteria

- [ ] Models downloaded to model vault
- [ ] Type definitions fixed (no type errors)
- [ ] Example config file created
- [ ] Can load model from local paths
- [ ] Can train a short LoRA successfully
- [ ] Can generate images with trained LoRA
- [ ] Training adapter properly removed during inference
- [ ] Documentation updated

---

## Estimated Total Time

- **Phase 1:** 10 minutes
- **Phase 2:** 15 minutes
- **Phase 3:** 1-2 hours (download time)
- **Phase 4:** 8-12 hours (testing)
- **Phase 5:** 1.5-2 hours

**Total:** ~11-16 hours (mostly testing and downloads)

---

## Notes

- The base model is large (~20-30 GB), so download time depends on connection speed
- The training adapter is small (~100-500 MB)
- Both models can be downloaded via `huggingface-cli` or Python `huggingface_hub`
- Local paths can be used in config files instead of Hugging Face Hub paths
- The implementation is already functional - these are polish and fixes

---

## References

- [Training Adapter Model Card](https://huggingface.co/ostris/zimage_turbo_training_adapter)
- [Base Model](https://huggingface.co/Tongyi-MAI/Z-Image-Turbo)
- [GitHub Commit](https://github.com/ostris/ai-toolkit/commit/4e62c38df5eb25dcf6a9ba3011113521f1f20c10)
- [Tutorial Video](https://youtu.be/Kmve1_jiDpQ)

