# FLUX.2 Development Plan - Phased Approach

## Overview

This document outlines a phased development plan to fully integrate FLUX.2 support into the ai-toolkit. The plan is divided into 5 phases, each building upon the previous phase.

## Phase 1: Foundation & Configuration (Priority: Critical)

**Goal**: Enable basic FLUX.2 model loading and configuration

### Tasks

1. **Update Config System** (`toolkit/config_modules.py`)
   - [ ] Add `"flux2"` to `ModelArch` type definition (line 556)
   - [ ] Add `is_flux2: bool` property to `ModelConfig.__init__` (line 570)
   - [ ] Add handling for `arch == "flux2"` in config parsing (after line 696)
   - [ ] Set `is_flux2 = True` when `arch == "flux2"` (after line 719)
   - [ ] Ensure `arch` defaults to `"flux2"` when `is_flux2=True` (after line 727)

2. **Update Base Model Classes**
   - [ ] Add `is_flux2()` property to `toolkit/models/base_model.py` (after line 249)
   - [ ] Add `is_flux2` property to `toolkit/stable_diffusion_model.py` (after line 262)
   - [ ] Update flow matching check to include `is_flux2` (line 199)

3. **Verify Model Registration**
   - [ ] Verify `Flux2Model` is properly exported in `extensions_built_in/diffusion_models/__init__.py`
   - [ ] Test `get_model_class()` returns `Flux2Model` for `arch="flux2"`

4. **Create Example Configs**
   - [ ] Create `config/examples/train_lora_flux2_24gb.yaml`
   - [ ] Create `config/examples/train_lora_flux2_48gb.yaml` (for higher VRAM)
   - [ ] Base configs on FLUX.1 examples but update:
     - `arch: "flux2"`
     - `name_or_path: "black-forest-labs/FLUX.2-dev"` (or correct path)
     - Model-specific settings

**Estimated Time**: 4-6 hours  
**Dependencies**: None  
**Risk Level**: Low  
**Testing**: Verify config loads and model class is selected correctly

---

## Phase 2: Model Loading & Verification (Priority: Critical)

**Goal**: Ensure FLUX.2 model loads correctly with all components

### Tasks

1. **Review and Fix Flux2Model Implementation**
   - [ ] Verify text encoder path is correct (`Mistral-Small-3.2-24B-Instruct-2506` per FLUX.2 docs)
   - [ ] Update hardcoded paths to be configurable
   - [ ] Add proper error handling for missing model files
   - [ ] Verify model file names match official FLUX.2 release
   - [ ] Test model loading on clean environment

2. **Memory Management**
   - [ ] Review quantization settings for FLUX.2 (32B parameters)
   - [ ] Test with `quantize: true` option
   - [ ] Test with `low_vram: true` option
   - [ ] Verify layer offloading works if needed
   - [ ] Document VRAM requirements

3. **Text Encoder Integration**
   - [ ] Verify Mistral model loads correctly
   - [ ] Test prompt encoding
   - [ ] Verify chat template format works
   - [ ] Test with various prompt lengths

4. **VAE Integration**
   - [ ] Verify VAE loads correctly
   - [ ] Test image encoding/decoding
   - [ ] Verify VAE scale factor (should be 16)

5. **Pipeline Integration**
   - [ ] Verify `Flux2Pipeline` works for inference
   - [ ] Test basic text-to-image generation
   - [ ] Verify sampling parameters

**Estimated Time**: 8-12 hours  
**Dependencies**: Phase 1  
**Risk Level**: Medium  
**Testing**: 
- Load model successfully
- Generate test image
- Verify all components work

---

## Phase 3: Training Pipeline Integration (Priority: High)

**Goal**: Enable LoRA training for FLUX.2

### Tasks

1. **Training Process Integration**
   - [ ] Verify `BaseSDTrainProcess` works with `Flux2Model`
   - [ ] Test basic training loop
   - [ ] Verify gradient checkpointing works
   - [ ] Test with different batch sizes
   - [ ] Verify gradient accumulation

2. **LoRA Integration**
   - [ ] Review `toolkit/lora_special.py` for FLUX.2 compatibility
   - [ ] Add `is_flux2` checks where `is_flux` is checked (lines 503, 579)
   - [ ] Verify target modules are correct for FLUX.2
   - [ ] Test LoRA training end-to-end
   - [ ] Verify LoRA saving/loading

3. **Noise Prediction & Loss**
   - [ ] Verify `get_noise_prediction()` works correctly
   - [ ] Test packed sequence handling
   - [ ] Verify loss calculation
   - [ ] Test with different timesteps

4. **Sampling During Training**
   - [ ] Verify sample generation during training works
   - [ ] Test with different resolutions
   - [ ] Verify prompt embedding generation
   - [ ] Test guidance scale

5. **Checkpoint Saving/Loading**
   - [ ] Verify checkpoint saving works
   - [ ] Test checkpoint resumption
   - [ ] Verify LoRA weights are saved correctly
   - [ ] Test model metadata

**Estimated Time**: 12-16 hours  
**Dependencies**: Phase 2  
**Risk Level**: Medium-High  
**Testing**: 
- Complete training run (short test)
- Verify checkpoints save/load
- Verify LoRA weights are correct

---

## Phase 4: Adapter & Extension Support (Priority: Medium)

**Goal**: Ensure compatibility with existing adapters and extensions

### Tasks

1. **Review Adapter Compatibility**
   - [ ] Review `toolkit/ip_adapter.py` - determine if FLUX.2 support needed
   - [ ] Review `toolkit/models/vd_adapter.py` - determine if FLUX.2 support needed
   - [ ] Review `toolkit/models/control_lora_adapter.py` - determine if FLUX.2 support needed
   - [ ] Review `toolkit/models/subpixel_adapter.py` - determine if FLUX.2 support needed
   - [ ] Review `toolkit/models/mean_flow_adapter.py` - determine if FLUX.2 support needed
   - [ ] Document which adapters work/don't work with FLUX.2

2. **Update Adapter Checks**
   - [ ] Add `is_flux2` checks where appropriate
   - [ ] Update adapter initialization if needed
   - [ ] Test each adapter with FLUX.2 (if applicable)

3. **Memory Management Extensions**
   - [ ] Review GPU splitting for FLUX.2 (if needed)
   - [ ] Test multi-GPU setups
   - [ ] Verify memory management utilities work

4. **Other Extensions**
   - [ ] Review Kontext support (if applicable to FLUX.2)
   - [ ] Review other model-specific extensions
   - [ ] Document compatibility

**Estimated Time**: 8-12 hours  
**Dependencies**: Phase 3  
**Risk Level**: Medium  
**Testing**: Test each adapter/extension individually

---

## Phase 5: UI, Documentation & Polish (Priority: Medium)

**Goal**: Complete user-facing features and documentation

### Tasks

1. **UI Updates**
   - [ ] Update `flux_train_ui.py` to support FLUX.2
   - [ ] Add FLUX.2 option to model selection
   - [ ] Update UI to show FLUX.2-specific settings
   - [ ] Test UI workflow end-to-end

2. **Web UI Integration**
   - [ ] Verify `ui/src/app/jobs/new/options.ts` properly handles FLUX.2
   - [ ] Update any hardcoded model lists
   - [ ] Test config generation from UI

3. **Documentation**
   - [ ] Add FLUX.2 section to `README.md`
   - [ ] Document setup requirements
   - [ ] Document VRAM requirements
   - [ ] Create migration guide from FLUX.1
   - [ ] Document known limitations
   - [ ] Add troubleshooting section

4. **Example Configs & Scripts**
   - [ ] Create additional example configs if needed
   - [ ] Update `run_modal.py` for FLUX.2 (if applicable)
   - [ ] Create example training scripts

5. **Testing & Validation**
   - [ ] End-to-end training test
   - [ ] Test on different hardware configurations
   - [ ] Performance benchmarking
   - [ ] Memory usage profiling

6. **Error Handling & Validation**
   - [ ] Add helpful error messages
   - [ ] Validate configs
   - [ ] Add warnings for common issues

**Estimated Time**: 10-14 hours  
**Dependencies**: Phase 4  
**Risk Level**: Low  
**Testing**: Full user workflow testing

---

## Implementation Order Summary

```
Phase 1 (Foundation) → Phase 2 (Loading) → Phase 3 (Training) → Phase 4 (Adapters) → Phase 5 (Polish)
```

## Critical Path Items

These items must be completed in order:

1. **Config system updates** (Phase 1) - Blocks everything
2. **Model loading** (Phase 2) - Blocks training
3. **Basic training** (Phase 3) - Core functionality
4. **Documentation** (Phase 5) - User enablement

## Parallel Work Items

These can be worked on in parallel after Phase 2:

- Adapter compatibility review (Phase 4)
- UI updates (Phase 5)
- Documentation writing (Phase 5)

## Testing Strategy

### Unit Tests
- Config parsing with `arch="flux2"`
- Model class selection
- Model loading

### Integration Tests
- End-to-end training run
- Checkpoint save/load
- LoRA training

### Manual Tests
- UI workflow
- Different hardware configs
- Various training scenarios

## Success Criteria

### Phase 1 Success
- ✅ Config with `arch: "flux2"` loads without errors
- ✅ `Flux2Model` is selected correctly
- ✅ Example configs exist

### Phase 2 Success
- ✅ Model loads all components successfully
- ✅ Can generate test image
- ✅ Memory usage is acceptable

### Phase 3 Success
- ✅ Training loop runs without errors
- ✅ LoRA weights are saved correctly
- ✅ Can resume from checkpoint

### Phase 4 Success
- ✅ Adapter compatibility documented
- ✅ Critical adapters work (if applicable)

### Phase 5 Success
- ✅ UI supports FLUX.2
- ✅ Documentation is complete
- ✅ Users can train FLUX.2 LoRAs successfully

## Risk Mitigation

### High Memory Usage
- **Risk**: FLUX.2 is 32B parameters, may not fit in 24GB
- **Mitigation**: 
  - Aggressive quantization
  - Layer offloading
  - Document minimum requirements
  - Provide multiple configs for different VRAM levels

### Training Instability
- **Risk**: New architecture may have different training characteristics
- **Mitigation**:
  - Start with conservative learning rates
  - Test with small datasets first
  - Document recommended settings

### Compatibility Issues
- **Risk**: Some adapters may not work
- **Mitigation**:
  - Document which adapters work
  - Provide workarounds where possible
  - Prioritize critical adapters

## Estimated Total Time

- **Phase 1**: 4-6 hours
- **Phase 2**: 8-12 hours
- **Phase 3**: 12-16 hours
- **Phase 4**: 8-12 hours
- **Phase 5**: 10-14 hours

**Total**: 42-60 hours (5-7.5 working days)

## Next Steps

1. Review and approve this plan
2. Set up development environment
3. Begin Phase 1 implementation
4. Create feature branch: `feature/flux2-support`
5. Regular checkpoints after each phase

## Notes

- FLUX.2 uses Mistral-3.2-24B-Instruct (verify exact model name)
- Model files: `flux2-dev.safetensors` and `ae.safetensors`
- VAE scale factor: 16 (8x + 2x pixel shuffle)
- Requires Hugging Face model access acceptance
- Non-commercial license (FLUX.2-dev)

