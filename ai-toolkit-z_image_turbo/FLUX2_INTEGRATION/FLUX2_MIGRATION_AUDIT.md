# FLUX.2 Migration Audit & Development Plan

## Executive Summary

This document provides a comprehensive audit of the ai-toolkit codebase and a phased development plan to fully support FLUX.2 model training. The codebase already contains a partial FLUX.2 implementation in `extensions_built_in/diffusion_models/flux2/`, but it requires integration and updates throughout the codebase.

## Current State Analysis

### ✅ What Already Exists

1. **FLUX.2 Model Implementation** (`extensions_built_in/diffusion_models/flux2/`)
   - `Flux2Model` class extending `BaseModel` with `arch = "flux2"`
   - Custom `Flux2` transformer model implementation
   - Custom `Flux2Pipeline` for inference
   - Custom `AutoEncoder` for FLUX.2 VAE
   - Sampling utilities for packed sequences
   - Model registered in `extensions_built_in/diffusion_models/__init__.py`

2. **Model Registration System**
   - Extension system in `toolkit/extension.py`
   - Model discovery via `toolkit/util/get_model.py`
   - `get_model_class()` function matches `config.arch` to `ModelClass.arch`

### ❌ What's Missing or Incomplete

1. **Config System Integration**
   - `ModelArch` type in `config_modules.py` doesn't include `"flux2"`
   - `ModelConfig` class doesn't handle `arch == "flux2"` properly
   - No `is_flux2` property or flag
   - Config examples don't include FLUX.2 training configs

2. **Model Selection Logic**
   - Many places check `is_flux` which only matches `arch == 'flux'` (FLUX.1)
   - `StableDiffusion` class has `is_flux` property but no `is_flux2`
   - `BaseModel` class has `is_flux` but no `is_flux2`

3. **Training Pipeline Integration**
   - `BaseSDTrainProcess` may need FLUX.2 specific handling
   - LoRA training may need adjustments for FLUX.2 architecture
   - Sampling/generation code may need FLUX.2 support

4. **UI Integration**
   - `flux_train_ui.py` only supports FLUX.1
   - UI options may need FLUX.2 support
   - Config generation for FLUX.2

5. **Documentation**
   - README doesn't mention FLUX.2 training
   - No example configs for FLUX.2
   - No migration guide

6. **Compatibility Checks**
   - Many adapters (IP-Adapter, ControlNet, etc.) check `is_flux` but not `is_flux2`
   - Memory management may need FLUX.2 specific handling
   - Quantization may need FLUX.2 specific settings

## Detailed File Audit

### Core Model Files

#### ✅ `extensions_built_in/diffusion_models/flux2/flux2_model.py`
- **Status**: Partially complete
- **Issues**:
  - Uses `Mistral3ForConditionalGeneration` (should verify version)
  - Text encoder path hardcoded: `"mistralai/Mistral-Small-3.1-24B-Instruct-2503"`
  - Model filename hardcoded: `"flux2-dev.safetensors"`
  - VAE filename hardcoded: `"ae.safetensors"`
  - Missing integration with training process
  - Missing proper error handling for model loading

#### ✅ `extensions_built_in/diffusion_models/flux2/src/model.py`
- **Status**: Complete
- **Notes**: Custom Flux2 transformer implementation

#### ✅ `extensions_built_in/diffusion_models/flux2/src/pipeline.py`
- **Status**: Complete
- **Notes**: Custom pipeline for FLUX.2 inference

#### ✅ `extensions_built_in/diffusion_models/flux2/src/autoencoder.py`
- **Status**: Complete
- **Notes**: Custom VAE implementation

### Configuration System

#### ❌ `toolkit/config_modules.py`
- **Line 556**: `ModelArch` type doesn't include `"flux2"`
- **Line 570**: No `is_flux2` flag in `ModelConfig`
- **Line 696-697**: Only handles `arch == 'flux'` (FLUX.1)
- **Line 719-720**: Only sets `is_flux` for FLUX.1
- **Action Required**: Add `"flux2"` to `ModelArch`, add `is_flux2` property, handle `arch == "flux2"`

#### ❌ `config/examples/`
- **Missing**: `train_lora_flux2_24gb.yaml` or similar
- **Missing**: `train_lora_flux2_schnell_24gb.yaml` if applicable
- **Action Required**: Create example configs for FLUX.2 training

### Model Selection & Loading

#### ⚠️ `toolkit/util/get_model.py`
- **Status**: Should work if `arch = "flux2"` is properly configured
- **Note**: Depends on config system updates

#### ❌ `toolkit/models/base_model.py`
- **Line 245**: Has `is_flux()` but no `is_flux2()`
- **Action Required**: Add `is_flux2()` property

#### ❌ `toolkit/stable_diffusion_model.py`
- **Line 257-258**: Has `is_flux` property but no `is_flux2`
- **Line 199**: Checks `is_flux` for flow matching
- **Action Required**: Add `is_flux2` property, update flow matching check

### Training Process

#### ⚠️ `jobs/process/BaseSDTrainProcess.py`
- **Line 1526**: Uses `get_model_class()` which should work
- **Potential Issues**: May need FLUX.2 specific training adjustments
- **Action Required**: Test and verify training works correctly

#### ⚠️ `toolkit/lora_special.py`
- **Line 503**: Checks `is_flux` for target modules
- **Line 579**: Checks `is_flux` for transformer models
- **Action Required**: May need to add `is_flux2` checks

### Adapters & Extensions

#### ⚠️ Multiple adapter files check `is_flux`:
- `toolkit/ip_adapter.py` - Lines 519, 536, 556, 629, 657, 671, 700, 743, 1128
- `toolkit/models/vd_adapter.py` - Lines 523, 546, 566, 581, 594, 601, 605, 653, 686
- `toolkit/models/control_lora_adapter.py` - Line 161
- `toolkit/models/subpixel_adapter.py` - Line 194
- `toolkit/models/mean_flow_adapter.py` - Lines 192, 222, 253
- **Action Required**: Review each adapter to determine if FLUX.2 support is needed

### UI & User Experience

#### ❌ `flux_train_ui.py`
- **Line 238**: Only sets `is_flux: true` (FLUX.1)
- **Action Required**: Add FLUX.2 option to UI

#### ⚠️ `ui/src/app/jobs/new/options.ts`
- **Line 470**: Has `name: 'flux2'` in options
- **Status**: May already have some UI support
- **Action Required**: Verify UI properly handles FLUX.2

### Documentation

#### ❌ `README.md`
- **Missing**: FLUX.2 training documentation
- **Missing**: FLUX.2 requirements and setup
- **Action Required**: Add FLUX.2 section to README

## Key Differences: FLUX.1 vs FLUX.2

1. **Text Encoder**: FLUX.1 uses T5, FLUX.2 uses Mistral-3.2-24B-Instruct
2. **Model Size**: FLUX.2 is 32B parameters vs FLUX.1's 12B
3. **Architecture**: Different transformer structure (double_blocks vs single_blocks)
4. **VAE**: FLUX.2 has improved autoencoder (Apache 2.0 licensed)
5. **Prompt Processing**: FLUX.2 uses chat template format
6. **Packed Sequences**: FLUX.2 uses packed sequence format for efficiency
7. **Model Files**: Different file naming (`flux2-dev.safetensors` vs `model.safetensors`)

## Critical Dependencies

1. **Hugging Face Access**: FLUX.2-dev requires model access acceptance
2. **Model Files**: Need `flux2-dev.safetensors` and `ae.safetensors`
3. **Text Encoder**: `mistralai/Mistral-Small-3.1-24B-Instruct-2503` (verify latest version)
4. **VRAM Requirements**: Likely higher than FLUX.1 (32B vs 12B parameters)

## Risk Assessment

### High Risk Areas
1. **Memory Management**: FLUX.2 is 2.67x larger than FLUX.1
2. **Quantization**: May need different quantization strategies
3. **Training Stability**: New architecture may have different training characteristics
4. **Compatibility**: Many adapters may not work without updates

### Medium Risk Areas
1. **Config Migration**: Users need to update configs
2. **UI Updates**: Need to ensure UI properly supports FLUX.2
3. **Documentation**: Users need clear guidance

### Low Risk Areas
1. **Model Loading**: Core loading logic should work
2. **Basic Training**: Core training loop should work with proper model class

