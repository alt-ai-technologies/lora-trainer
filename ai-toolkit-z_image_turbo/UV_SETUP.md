# UV Package Manager Setup

This project now uses [uv](https://github.com/astral-sh/uv) for fast Python package management.

## What is uv?

`uv` is an extremely fast Python package installer and resolver written in Rust. It's a drop-in replacement for `pip` and `pip-tools` that's 10-100x faster.

## Installation

### Install uv

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Or on Windows:
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

The installer adds `uv` to your PATH. You may need to restart your terminal or run:
```bash
export PATH="$HOME/.local/bin:$PATH"
```

### Verify Installation

```bash
uv --version
```

## Usage

### Quick Install (Recommended)

Use the provided installation script:

```bash
chmod +x install_with_uv.sh
./install_with_uv.sh
```

### Manual Installation

#### 1. Install PyTorch (Required First)

For CUDA 12.6:
```bash
uv pip install --system --no-cache-dir torch==2.7.0 torchvision==0.22.0 torchaudio==2.7.0 --index-url https://download.pytorch.org/whl/cu126
```

For CUDA 12.8 (nightly):
```bash
uv pip install --system --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/nightly/cu128
```

#### 2. Install Project Dependencies

```bash
uv pip install --system -r requirements.txt
```

### Using uv in Virtual Environment

If you prefer to use a virtual environment:

```bash
# Create virtual environment with uv
uv venv

# Activate it
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Install dependencies
uv pip install -r requirements.txt
```

### Installing Development Dependencies

```bash
uv pip install --system -r requirements-dev.txt
```

Or with uv's project management:

```bash
uv pip install --system -e ".[dev]"
```

## Benefits of uv

1. **Speed**: 10-100x faster than pip
2. **Reliability**: Better dependency resolution
3. **Compatibility**: Drop-in replacement for pip
4. **Cross-platform**: Works on Linux, macOS, and Windows

## Common Commands

```bash
# Install a package
uv pip install package-name

# Install from requirements file
uv pip install -r requirements.txt

# Install in development mode
uv pip install -e .

# List installed packages
uv pip list

# Show package info
uv pip show package-name

# Uninstall a package
uv pip uninstall package-name

# Update a package
uv pip install --upgrade package-name
```

## Project Structure

- `requirements.txt` - Main project dependencies
- `requirements-dev.txt` - Development dependencies
- `requirements-comprehensive.txt` - All dependencies including PyTorch (reference)
- `pyproject.toml` - Modern Python project configuration (for uv and other tools)
- `install_with_uv.sh` - Automated installation script

## Troubleshooting

### uv command not found

Make sure uv is in your PATH:
```bash
export PATH="$HOME/.local/bin:$PATH"
```

Or add to your `~/.bashrc` or `~/.zshrc`:
```bash
export PATH="$HOME/.local/bin:$PATH"
```

### Permission errors

If you get permission errors, use `--system` flag (installs to system Python) or use a virtual environment.

### CUDA version issues

Check your CUDA version:
```bash
nvcc --version
```

Then install the appropriate PyTorch version as shown in the manual installation section.

## Migration from pip

If you're currently using `pip`, you can replace all `pip` commands with `uv pip`:

```bash
# Old way
pip install -r requirements.txt

# New way (same command, just faster!)
uv pip install -r requirements.txt
```

## Additional Resources

- [uv Documentation](https://docs.astral.sh/uv/)
- [uv GitHub](https://github.com/astral-sh/uv)

