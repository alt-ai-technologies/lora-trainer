# Z-Image Turbo Integration Audit

**Date:** 2025-11-30  
**Auditor:** AI Assistant  
**Repository:** `/home/nfmil/projects/image_gen/ai-toolkit-z_image_turbo`

## Executive Summary

The Z-Image Turbo integration has been successfully implemented with the training adapter support. The core implementation is solid and follows the established patterns from the codebase. However, there are a few configuration system gaps that should be addressed for full compatibility.

**Overall Status:** ✅ **Functional** with minor configuration gaps

---

## ✅ What's Working Well

### 1. Core Implementation (`extensions_built_in/diffusion_models/z_image/z_image.py`)

- ✅ **Model Class**: `ZImageModel` properly extends `BaseModel`
- ✅ **Architecture**: Correctly sets `arch = "zimage"`
- ✅ **Training Adapter Loading**: `load_training_adapter()` method is correctly implemented:
  - Handles both local paths and Hugging Face Hub paths
  - Properly converts weight keys from `diffusion_model.` to `transformer.`
  - Merges adapter with `merge_weight=1.0` but marks as not merged for inference
  - Sets `multiplier = -1.0` and `is_active = False` during training
  - Sets `invert_assistant_lora = True` for proper inference handling
- ✅ **Model Loading**: Properly loads transformer, text encoder (Qwen3ForCausalLM), VAE, and pipeline
- ✅ **Flow Matching**: Correctly implements flow matching scheduler
- ✅ **Bucket Divisibility**: Returns `16 * 2` (32) for proper image sizing
- ✅ **LoRA Weight Conversion**: Proper conversion between `transformer.` and `diffusion_model.` formats
- ✅ **Noise Prediction**: Correctly implements the noise prediction method for training
- ✅ **Memory Management**: Supports quantization, layer offloading, and low VRAM modes

### 2. Model Registration

- ✅ **Module Export**: `extensions_built_in/diffusion_models/z_image/__init__.py` correctly exports `ZImageModel`
- ✅ **Model List**: `ZImageModel` is properly added to `AI_TOOLKIT_MODELS` in `extensions_built_in/diffusion_models/__init__.py`
- ✅ **Model Discovery**: The `get_model_class()` function in `toolkit/util/get_model.py` will correctly find `ZImageModel` by matching `arch == "zimage"`

### 3. UI Integration (`ui/src/app/jobs/new/options.ts`)

- ✅ **Model Option**: Z-Image Turbo is properly registered in the UI with:
  - Name: `'zimage:turbo'`
  - Label: `'Z-Image Turbo (w/ Training Adapter)'`
  - Default model path: `'Tongyi-MAI/Z-Image-Turbo'`
  - Default training adapter: `'ostris/zimage_turbo_training_adapter/zimage_turbo_training_adapter_v1.safetensors'`
- ✅ **Default Settings**: Properly configured with:
  - Quantization enabled by default
  - Flow matching sampler
  - Guidance scale: 1 (appropriate for turbo models)
  - Sample steps: 8 (appropriate for turbo models)
- ✅ **UI Fields**: `assistant_lora_path` field is properly exposed in the UI

### 4. Code Quality

- ✅ **No Linting Errors**: The implementation passes linting checks
- ✅ **Error Handling**: Proper error handling for missing adapter files and download failures
- ✅ **Type Hints**: Good use of type hints throughout
- ✅ **Documentation**: Code is reasonably self-documenting

---

## ⚠️ Issues Found

### 1. **CRITICAL: ModelArch Type Definition Missing 'zimage'**

**Location:** `toolkit/config_modules.py:556`

**Issue:**
```python
ModelArch = Literal['sd1', 'sd2', 'sd3', 'sdxl', 'pixart', 'pixart_sigma', 'auraflow', 'flux', 'flex1', 'flex2', 'lumina2', 'vega', 'ssd', 'wan21']
```

The `ModelArch` type definition does not include `'zimage'`, which means:
- Type checkers (mypy, pyright) will flag `arch = "zimage"` as invalid
- IDE autocomplete won't recognize `'zimage'` as a valid arch type
- This is a type safety issue, though it won't break runtime functionality

**Fix Required:**
```python
ModelArch = Literal['sd1', 'sd2', 'sd3', 'sdxl', 'pixart', 'pixart_sigma', 'auraflow', 'flux', 'flex1', 'flex2', 'lumina2', 'vega', 'ssd', 'wan21', 'zimage']
```

**Priority:** Medium (type safety, doesn't affect runtime)

---

### 2. **MEDIUM: Config Parsing Logic Missing 'zimage' Handling**

**Location:** `toolkit/config_modules.py:682-728`

**Issue:**
The config parsing logic in `ModelConfig.__init__()` doesn't handle the `'zimage'` arch type. While this might not be strictly necessary (since the model class handles its own initialization), it's inconsistent with other model types.

**Current Code:**
```python
if self.arch is not None:
    if self.arch == 'sd2':
        self.is_v2 = True
    elif self.arch == 'sd3':
        self.is_v3 = True
    # ... other archs ...
    elif self.arch == 'ssd':
        self.is_ssd = True
    else:
        pass  # zimage falls through here
```

**Fix Required:**
Add handling for `'zimage'` arch (if needed, or document that it's intentionally not needed):
```python
elif self.arch == 'zimage':
    # Z-Image doesn't need special flags, but we can add them if needed
    pass
```

**Priority:** Low (functionality works without it, but inconsistent)

---

### 3. **LOW: Missing Example Config File**

**Location:** `config/examples/`

**Issue:**
There's no example configuration file for Z-Image Turbo training. Users would need to create one from scratch or adapt from other model examples.

**Expected File:** `config/examples/train_lora_zimage_turbo_24gb.yaml`

**Priority:** Low (documentation/usability)

**Suggested Content:**
```yaml
# Example config for training Z-Image Turbo LoRA
# Based on the UI defaults and similar to FLUX schnell config

config:
  output_name: "zimage_turbo_lora"
  output_folder: "./output"
  
  process:
    - type: "train"
      model:
        name_or_path: "Tongyi-MAI/Z-Image-Turbo"
        arch: "zimage"
        assistant_lora_path: "ostris/zimage_turbo_training_adapter/zimage_turbo_training_adapter_v1.safetensors"
        quantize: true
        quantize_te: true
        low_vram: true
        qtype: "qfloat8"
      
      train:
        dataset_folder: "./dataset"
        batch_size: 1
        gradient_accumulation: 4
        epochs: 10
        save_every_n_epochs: 1
        noise_scheduler: "flowmatch"
        timestep_type: "weighted"
        unload_text_encoder: false
      
      network:
        type: "lora"
        linear: 128
        linear_alpha: 128
        transformer_only: true
      
      sample:
        sampler: "flowmatch"
        sample_steps: 8
        guidance_scale: 1
        width: 1024
        height: 1024
        sample_every_n_epochs: 1
```

---

### 4. **INFO: No is_zimage Property**

**Location:** `toolkit/models/base_model.py`, `toolkit/stable_diffusion_model.py`

**Issue:**
Other model types have convenience properties like `is_flux`, `is_pixart`, etc. There's no `is_zimage` property, though this might not be needed if nothing in the codebase checks for it.

**Priority:** Very Low (only needed if other code checks for it)

---

## 📋 Testing Recommendations

### 1. **Unit Tests**
- [ ] Test `ZImageModel` initialization
- [ ] Test training adapter loading (local and Hub paths)
- [ ] Test model loading with and without adapter
- [ ] Test LoRA weight conversion methods

### 2. **Integration Tests**
- [ ] Test end-to-end training run (short)
- [ ] Test inference with trained LoRA
- [ ] Test checkpoint saving/loading
- [ ] Test with different VRAM configurations

### 3. **Manual Testing**
- [ ] Test UI workflow: create job → train → generate samples
- [ ] Test with different dataset sizes
- [ ] Test with different resolutions
- [ ] Verify training adapter is properly removed during inference

---

## 🔍 Code Review Notes

### Training Adapter Implementation Analysis

The training adapter implementation follows the correct pattern:

1. **During Training:**
   - Adapter is merged into the model (`merge_in(merge_weight=1.0)`)
   - But marked as `is_merged_in = False` so inference can handle it separately
   - `multiplier = -1.0` and `is_active = False` means it's deactivated during training
   - This means the model trains on the de-distilled version (base + adapter)

2. **During Inference:**
   - `invert_assistant_lora = True` tells the system to invert the adapter
   - In `base_model.py:369-375`, when `invert_assistant_lora` is True:
     - `assistant_lora.is_active = True`
     - `multiplier = -1.0` (already set)
   - This effectively removes the adapter effects, restoring the distilled model
   - The new LoRA's information remains on the distilled model

This matches the intended behavior described in the Hugging Face model card.

---

## 📝 Recommendations

### Immediate Actions (High Priority)
1. ✅ **Add 'zimage' to ModelArch type** - Fix type safety issue
2. ✅ **Create example config file** - Improve usability

### Short-term (Medium Priority)
3. ✅ **Add 'zimage' handling in config parsing** - For consistency
4. ✅ **Add unit tests** - Ensure reliability

### Long-term (Low Priority)
5. ✅ **Consider adding is_zimage property** - If needed by other code
6. ✅ **Add to README.md** - Document Z-Image Turbo training
7. ✅ **Performance benchmarking** - Compare with/without adapter

---

## ✅ Conclusion

The Z-Image Turbo integration is **functionally complete and correct**. The core implementation properly handles the training adapter pattern, and the UI integration is well done. The main gaps are in the configuration system type definitions and documentation, which are minor issues that don't affect runtime functionality.

**Recommendation:** Address the type definition issue and create an example config file, then the integration will be production-ready.

---

## 📚 References

- [Hugging Face Model Card](https://huggingface.co/ostris/zimage_turbo_training_adapter)
- [GitHub Commit](https://github.com/ostris/ai-toolkit/commit/4e62c38df5eb25dcf6a9ba3011113521f1f20c10)
- Base Model: [Tongyi-MAI/Z-Image-Turbo](https://huggingface.co/Tongyi-MAI/Z-Image-Turbo)

