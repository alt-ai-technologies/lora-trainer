# Installation Guide

This guide covers installing AI Toolkit with all dependencies, including using `uv` for faster package management.

## Quick Start

### Using the Automated Script (Recommended)

```bash
chmod +x install_with_uv.sh
./install_with_uv.sh
```

### Manual Installation

#### 1. Install uv (Optional but Recommended)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"
```

#### 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

Or with uv:
```bash
uv venv
source venv/bin/activate
```

#### 3. Install PyTorch (Required First)

**For CUDA 12.6:**
```bash
pip install --no-cache-dir torch==2.7.0 torchvision==0.22.0 torchaudio==2.7.0 --index-url https://download.pytorch.org/whl/cu126
```

**For CUDA 12.8 (nightly):**
```bash
pip install --pre --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/nightly/cu128
```

**With uv:**
```bash
uv pip install --no-cache-dir torch==2.7.0 torchvision==0.22.0 torchaudio==2.7.0 --index-url https://download.pytorch.org/whl/cu126
```

#### 4. Install Project Dependencies

**With pip:**
```bash
pip install -r requirements.txt
```

**With uv (faster):**
```bash
uv pip install -r requirements.txt
```

## Verification

After installation, verify everything works:

```bash
python3 test_zimage_simple.py
```

Or run the full test:
```bash
python3 test_zimage_turbo.py
```

## Troubleshooting

### torchaudio not found

If you get `ModuleNotFoundError: No module named 'torchaudio'`, install it explicitly:

```bash
pip install torchaudio --index-url https://download.pytorch.org/whl/cu126
```

### diffusers not found

The diffusers package is installed from a git repository. If it fails, try:

```bash
pip install git+https://github.com/huggingface/diffusers@6bf668c4d217ebc96065e673d8a257fd79950d34
```

### CUDA version mismatch

Check your CUDA version:
```bash
nvcc --version
```

Then install the matching PyTorch version as shown in step 3.

## Using uv

See [UV_SETUP.md](./UV_SETUP.md) for detailed information about using `uv` for package management.

## Files

- `requirements.txt` - Main dependencies (PyTorch not included, install separately)
- `requirements-comprehensive.txt` - All dependencies including PyTorch (reference)
- `requirements-dev.txt` - Development dependencies
- `pyproject.toml` - Modern Python project configuration
- `install_with_uv.sh` - Automated installation script

