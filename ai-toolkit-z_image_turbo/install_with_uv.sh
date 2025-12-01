#!/bin/bash
# Installation script using uv for AI Toolkit
# This script installs all dependencies using uv

set -e

echo "=========================================="
echo "AI Toolkit Installation with uv"
echo "=========================================="

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "uv is not installed. Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
fi

echo "Using uv version: $(uv --version)"

# Check if we're in a virtual environment
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo ""
    echo "No virtual environment detected."
    
    # Check if venv exists in current directory
    if [ -d "venv" ]; then
        echo "Found venv directory. Activating it..."
        source venv/bin/activate
    else
        echo "Creating new virtual environment..."
        python3 -m venv venv
        source venv/bin/activate
    fi
else
    echo "Using existing virtual environment: $VIRTUAL_ENV"
fi

# Detect CUDA version
CUDA_VERSION=$(nvcc --version 2>/dev/null | grep "release" | sed 's/.*release \([0-9]\+\.[0-9]\+\).*/\1/' || echo "12.6")

echo "Detected CUDA version: $CUDA_VERSION"

# Install PyTorch first
echo ""
echo "=========================================="
echo "Installing PyTorch packages..."
echo "=========================================="

if [[ "$CUDA_VERSION" == "12.8" ]] || [[ "$CUDA_VERSION" == "12.9" ]]; then
    echo "Installing PyTorch with CUDA 12.8 (nightly)..."
    uv pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/nightly/cu128
else
    echo "Installing PyTorch with CUDA 12.6..."
    uv pip install --no-cache-dir torch==2.7.0 torchvision==0.22.0 torchaudio==2.7.0 --index-url https://download.pytorch.org/whl/cu126
fi

echo ""
echo "=========================================="
echo "Installing AI Toolkit dependencies..."
echo "=========================================="

# Install from requirements.txt using uv
uv pip install -r requirements.txt

echo ""
echo "=========================================="
echo "Installation complete!"
echo "=========================================="
echo ""
echo "Virtual environment: $VIRTUAL_ENV"
echo ""
echo "To verify installation, run:"
echo "  source venv/bin/activate  # if not already activated"
echo "  python3 test_zimage_simple.py"
echo ""
echo "To activate this environment in the future:"
echo "  source venv/bin/activate"
echo ""

