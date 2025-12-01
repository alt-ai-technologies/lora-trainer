# Z-Image Turbo Local Models Test Suite

## Overview

This test suite validates that Z-Image Turbo models downloaded to the local model vault can be loaded and used correctly with the AI Toolkit.

## Prerequisites

1. **Models Downloaded**: Models must be in `/home/nfmil/model_vault`
   - Base model: `/home/nfmil/model_vault/Tongyi-MAI/Z-Image-Turbo`
   - Training adapter: `/home/nfmil/model_vault/ostris/zimage_turbo_training_adapter/zimage_turbo_training_adapter_v1.safetensors`

2. **Dependencies**: Install AI Toolkit dependencies
   ```bash
   cd /home/nfmil/projects/image_gen/ai-toolkit-z_image_turbo
   pip install -r requirements.txt
   ```

3. **PyTorch Packages**: Install matching PyTorch, torchvision, and torchaudio
   ```bash
   pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu126
   ```

## Running Tests

### Option 1: From project root (recommended)

```bash
cd /home/nfmil/projects/image_gen

# Activate virtual environment if using one
source .venv/bin/activate  # or your venv path

# Run tests
pytest tests/test_zimage_turbo_local_models.py -v

# Or run manually
python3 tests/test_zimage_turbo_local_models.py
```

### Option 2: From ai-toolkit directory

```bash
cd /home/nfmil/projects/image_gen/ai-toolkit-z_image_turbo

# Add parent directory to path
export PYTHONPATH=/home/nfmil/projects/image_gen:$PYTHONPATH

# Run tests
pytest ../tests/test_zimage_turbo_local_models.py -v
```

## Test Coverage

The test suite includes:

- ✅ Model path validation
- ✅ Model discovery and registration  
- ✅ Configuration with local paths
- ✅ Model initialization
- ✅ Full model loading (with and without adapter)
- ✅ Component existence checks
- ✅ Training adapter loading and configuration
- ✅ Adapter inversion logic
- ✅ LoRA weight conversion
- ✅ Model properties and methods

## Troubleshooting

### torchaudio Import Error

If you see `OSError: Could not load this library: .../libtorchaudio.so`:

1. **Check PyTorch version**:
   ```bash
   python -c "import torch; print(torch.__version__)"
   ```

2. **Reinstall matching torchaudio**:
   ```bash
   pip uninstall torchaudio
   pip install torchaudio --index-url https://download.pytorch.org/whl/cu126
   ```

3. **Or reinstall all PyTorch packages together**:
   ```bash
   pip uninstall torch torchvision torchaudio
   pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu126
   ```

The test will automatically use a mock torchaudio if the real one can't be loaded (audio features will be disabled).

### Missing Dependencies

If you see `ModuleNotFoundError: No module named 'diffusers'`:

```bash
cd /home/nfmil/projects/image_gen/ai-toolkit-z_image_turbo
pip install -r requirements.txt
```

### CUDA Not Available

Tests that require CUDA will automatically skip if CUDA is not available. You'll see:
```
⚠ CUDA not available, skipping GPU-dependent tests
```

## Expected Output

When tests pass, you should see:

```
============================================================
Z-Image Turbo Local Models Test Suite
============================================================

Running: Model Paths Exist...
✓ Model Paths Exist passed

Running: Model Discovery...
✓ Model Discovery passed

...

============================================================
Results: X passed, 0 failed, Y skipped
============================================================
```

## Notes

- Tests automatically handle torchaudio import issues
- CUDA-only tests are skipped if CUDA is not available
- Tests work with both pytest and manual execution
- All tests use local model paths from `/home/nfmil/model_vault`

