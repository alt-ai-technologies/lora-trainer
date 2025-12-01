#!/usr/bin/env python3
"""
Modal deployment script for running Z-Image Turbo Hub Models tests.

Usage:
    modal run modal_test_deploy.py
    modal run modal_test_deploy.py --test-file tests/test_zimage_turbo_hub_models.py
"""

import os
import sys
import modal
from pathlib import Path

# Enable Hugging Face transfer for faster downloads
os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "1"
os.environ['DISABLE_TELEMETRY'] = 'YES'

# Get the project root directory
PROJECT_ROOT = Path(__file__).parent
AI_TOOLKIT_PATH = PROJECT_ROOT / "ai-toolkit-z_image_turbo"

# Define the Modal image with all dependencies
image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install(
        "libgl1",
        "libglib2.0-0",
        "git",
        "wget",
        "curl"
    )
    # Install PyTorch with CUDA support first
    .run_commands(
        "pip install --no-cache-dir torch==2.7.0 torchvision==0.22.0 torchaudio==2.7.0 --index-url https://download.pytorch.org/whl/cu126"
    )
    .pip_install(
        # Core dependencies
        "torchao==0.10.0",
        "safetensors",
        "transformers==4.57.3",
        "git+https://github.com/huggingface/diffusers@6bf668c4d217ebc96065e673d8a257fd79950d34",
        # LoRA and training
        "lycoris-lora==1.8.3",
        "peft",
        # Data processing
        "flatten_json",
        "pyyaml",
        "oyaml",
        "pydantic",
        "omegaconf",
        "toml",
        # Image processing
        "albumentations==1.4.15",
        "albucore==0.0.16",
        "opencv-python",
        "kornia",
        "invisible-watermark",
        "einops",
        "pytorch-wavelets==1.3.0",
        # Training and optimization
        "accelerate",
        "bitsandbytes",
        "prodigyopt",
        "k-diffusion",
        "optimum-quanto==0.2.4",
        # Model components
        "open_clip_torch",
        "timm",
        "controlnet_aux==0.0.10",
        "sentencepiece",
        # Utilities
        "python-dotenv",
        "hf_transfer",
        "huggingface_hub",
        "lpips",
        "pytorch_fid",
        "matplotlib==3.10.1",
        "tensorboard",
        # Testing
        "pytest",
        # Other utilities
        "python-slugify",
        "setuptools==69.5.1",
        # Git dependencies
        "git+https://github.com/jaretburkett/easy_dwpose.git",
    )
    .env({
        "HF_HUB_ENABLE_HF_TRANSFER": "1",
        "DISABLE_TELEMETRY": "YES",
    })
)

# Add local directories to the image
image = image.add_local_dir(
    str(AI_TOOLKIT_PATH),
    remote_path="/root/ai-toolkit-z_image_turbo"
).add_local_dir(
    str(PROJECT_ROOT / "tests"),
    remote_path="/root/tests"
)

# Create a persistent volume for Hugging Face model cache
# This will cache downloaded models between runs, significantly speeding up subsequent deployments
HF_CACHE_DIR = "/root/.cache/huggingface"
hf_cache_volume = modal.Volume.from_name("hf-model-cache", create_if_missing=True)

# Create the Modal app
app = modal.App(
    name="zimage-turbo-tests",
    image=image
)


@app.function(
    # Request a GPU with sufficient VRAM for model loading
    gpu="A100",  # Can also use "H100" or "A10G" depending on availability
    timeout=3600,  # 1 hour timeout (tests may take time to download models)
    secrets=[
        modal.Secret.from_name("huggingface"),  # HF token for gated models
    ],
    volumes={HF_CACHE_DIR: hf_cache_volume},  # Mount HF cache volume for persistent model storage
)
def run_tests(test_file: str = "tests/test_zimage_turbo_hub_models.py"):
    """
    Run the Z-Image Turbo Hub Models test suite on Modal.
    
    Args:
        test_file: Path to the test file to run (relative to project root)
    """
    import sys
    from pathlib import Path
    
    # Set up Hugging Face cache directory
    # The volume is already mounted, but we need to ensure the directory exists
    Path(HF_CACHE_DIR).mkdir(parents=True, exist_ok=True)
    os.environ["HF_HOME"] = HF_CACHE_DIR
    os.environ["HUGGINGFACE_HUB_CACHE"] = str(Path(HF_CACHE_DIR) / "hub")
    
    # Add ai-toolkit to Python path
    ai_toolkit_path = Path("/root/ai-toolkit-z_image_turbo")
    if ai_toolkit_path.exists():
        sys.path.insert(0, str(ai_toolkit_path))
    
    # Change to the project root directory
    os.chdir("/root")
    
    # Set up test file path
    test_path = Path("/root") / test_file
    
    print("=" * 80)
    print("Z-Image Turbo Hub Models Test Suite - Modal Deployment")
    print("=" * 80)
    print(f"Test file: {test_path}")
    print(f"AI Toolkit path: {ai_toolkit_path}")
    print(f"Python path: {sys.path}")
    print("=" * 80)
    print()
    
    # Check if test file exists
    if not test_path.exists():
        print(f"❌ Test file not found: {test_path}")
        return {"status": "error", "message": f"Test file not found: {test_path}"}
    
    # Check CUDA availability
    import torch
    print(f"CUDA available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"CUDA device: {torch.cuda.get_device_name(0)}")
        print(f"CUDA version: {torch.version.cuda}")
    print()
    
    # Run the test file
    try:
        # Try using pytest first if available
        try:
            import pytest
            print("Running tests with pytest...")
            exit_code = pytest.main([
                str(test_path),
                "-v",
                "--tb=short",
                "-s"  # Show print statements
            ])
            
            if exit_code == 0:
                print()
                print("=" * 80)
                print("✅ Tests passed!")
                print("=" * 80)
                return {"status": "success", "exit_code": exit_code}
            else:
                print()
                print("=" * 80)
                print(f"❌ Tests failed with exit code: {exit_code}")
                print("=" * 80)
                return {"status": "failure", "exit_code": exit_code}
                
        except ImportError:
            print("pytest not available, running test file directly...")
            # Fallback to direct execution
            sys.path.insert(0, str(test_path.parent))
            
            # Execute the test file
            with open(test_path, 'r') as f:
                test_code = f.read()
            
            # Create a namespace for execution
            namespace = {
                '__file__': str(test_path),
                '__name__': '__main__',
            }
            
            # Execute the test code
            exec(compile(test_code, str(test_path), 'exec'), namespace)
            
            print()
            print("=" * 80)
            print("✅ Tests completed successfully!")
            print("=" * 80)
            
            # Commit the volume to save any newly downloaded models
            hf_cache_volume.commit()
            return {
                "status": "success",
                "message": "Tests completed successfully"
            }
        
    except SystemExit as e:
        # pytest or test script may call sys.exit()
        exit_code = e.code if e.code is not None else 0
        if exit_code == 0:
            print()
            print("=" * 80)
            print("✅ Tests passed!")
            print("=" * 80)
            # Commit the volume to save any newly downloaded models
            hf_cache_volume.commit()
            return {"status": "success", "exit_code": exit_code}
        else:
            print()
            print("=" * 80)
            print(f"❌ Tests failed with exit code: {exit_code}")
            print("=" * 80)
            # Still commit the volume even on failure to save downloaded models
            hf_cache_volume.commit()
            return {"status": "failure", "exit_code": exit_code}
            
    except Exception as e:
        import traceback
        print()
        print("=" * 80)
        print(f"❌ Error running tests: {e}")
        print("=" * 80)
        traceback.print_exc()
        # Commit the volume even on error to save any partial downloads
        try:
            hf_cache_volume.commit()
        except:
            pass
        return {
            "status": "error",
            "message": str(e),
            "traceback": traceback.format_exc()
        }


@app.local_entrypoint()
def main(test_file: str = "tests/test_zimage_turbo_hub_models.py"):
    """
    Local entrypoint to run tests on Modal.
    
    Usage:
        modal run modal_test_deploy.py
        modal run modal_test_deploy.py --test-file tests/test_zimage_turbo_hub_models.py
    """
    result = run_tests.remote(test_file=test_file)
    print(f"\nTest execution result: {result}")
    return result

