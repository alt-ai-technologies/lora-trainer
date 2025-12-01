#!/usr/bin/env python3
"""
Modal deployment script for Z-Image Turbo LoRA training.

Usage:
    modal run modal_train_deploy.py config/my_training.yaml
    modal run modal_train_deploy.py config/training1.yaml config/training2.yaml --recover
    modal run modal_train_deploy.py config/my_training.yaml --name custom_name
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
)

# Create persistent volumes
# HF model cache - speeds up subsequent runs significantly
HF_CACHE_DIR = "/root/.cache/huggingface"
hf_cache_volume = modal.Volume.from_name("hf-model-cache", create_if_missing=True)

# Training outputs - stores LoRAs, samples, checkpoints
MOUNT_DIR = "/root/modal_output"
training_output_volume = modal.Volume.from_name("zimage-training-outputs", create_if_missing=True)

# Optional: Dataset volume for reusable datasets
DATASET_DIR = "/root/datasets"
dataset_volume = modal.Volume.from_name("zimage-datasets", create_if_missing=True)

# Create the Modal app
app = modal.App(
    name="zimage-turbo-training",
    image=image
)


@app.function(
    # Request a GPU with sufficient VRAM for Z-Image Turbo
    gpu="A100",  # 40GB VRAM - recommended for Z-Image Turbo with quantization
    timeout=7200,  # 2 hours - adjust based on training steps
    secrets=[
        modal.Secret.from_name("huggingface"),  # HF token for model access
    ],
    volumes={
        HF_CACHE_DIR: hf_cache_volume,
        MOUNT_DIR: training_output_volume,
        DATASET_DIR: dataset_volume,  # Optional - comment out if not using
    }
)
def main(config_file_list_str: str, recover: bool = False, name: str = None):
    """
    Run Z-Image Turbo LoRA training on Modal.
    
    Args:
        config_file_list_str: Comma-separated list of config file paths
        recover: Continue running additional jobs even if one fails
        name: Optional name to replace [name] tag in config
    """
    import sys
    from pathlib import Path
    
    # Set up Hugging Face cache directory
    Path(HF_CACHE_DIR).mkdir(parents=True, exist_ok=True)
    os.environ["HF_HOME"] = HF_CACHE_DIR
    os.environ["HUGGINGFACE_HUB_CACHE"] = str(Path(HF_CACHE_DIR) / "hub")
    
    # Add ai-toolkit to Python path
    ai_toolkit_path = Path("/root/ai-toolkit-z_image_turbo")
    if ai_toolkit_path.exists():
        sys.path.insert(0, str(ai_toolkit_path))
    
    # Change to the ai-toolkit directory
    os.chdir(str(ai_toolkit_path))
    
    # Import after path setup
    from toolkit.job import get_job
    
    # Convert config file list from string to list
    config_file_list = config_file_list_str.split(",")
    
    jobs_completed = 0
    jobs_failed = 0
    
    print("=" * 80)
    print("Z-Image Turbo LoRA Training on Modal")
    print("=" * 80)
    print(f"Running {len(config_file_list)} job{'s' if len(config_file_list) > 1 else ''}")
    print(f"Training outputs will be saved to: {MOUNT_DIR}")
    print(f"HF cache directory: {HF_CACHE_DIR}")
    print("=" * 80)
    print()
    
    for config_file in config_file_list:
        config_file = config_file.strip()
        try:
            print(f"Loading config: {config_file}")
            
            # Handle both absolute and relative paths
            if not Path(config_file).is_absolute():
                # Try relative to ai-toolkit config directory
                config_path = ai_toolkit_path / "config" / config_file
                if not config_path.exists():
                    # Try as direct path in ai-toolkit
                    config_path = ai_toolkit_path / config_file
            else:
                config_path = Path(config_file)
            
            if not config_path.exists():
                raise FileNotFoundError(f"Config file not found: {config_file} (tried: {config_path})")
            
            print(f"Using config file: {config_path}")
            
            # Get the job
            job = get_job(str(config_path), name)
            
            # Ensure training folder is set to Modal output directory
            if 'process' in job.config and len(job.config['process']) > 0:
                job.config['process'][0]['training_folder'] = MOUNT_DIR
            
            os.makedirs(MOUNT_DIR, exist_ok=True)
            print(f"Training outputs will be saved to: {MOUNT_DIR}")
            print()
            
            # Run the job
            job.run()
            
            # Commit volumes after training
            print()
            print("Committing volumes...")
            hf_cache_volume.commit()
            training_output_volume.commit()
            dataset_volume.commit()
            print("✓ Volumes committed")
            
            # Cleanup
            job.cleanup()
            jobs_completed += 1
            
            print()
            print(f"✓ Job '{job.name}' completed successfully")
            print()
            
        except Exception as e:
            import traceback
            print()
            print(f"❌ Error running job '{config_file}': {e}")
            print()
            traceback.print_exc()
            jobs_failed += 1
            
            # Still commit volumes even on failure to save any progress
            try:
                hf_cache_volume.commit()
                training_output_volume.commit()
            except:
                pass
            
            if not recover:
                print()
                print("=" * 80)
                print(f"Result: {jobs_completed} completed, {jobs_failed} failed")
                print("=" * 80)
                raise e
    
    print()
    print("=" * 80)
    print(f"Result: {jobs_completed} completed, {jobs_failed} failed")
    print("=" * 80)
    
    if jobs_failed > 0:
        sys.exit(1)


def print_end_message(jobs_completed, jobs_failed):
    """Print summary message."""
    failure_string = f"{jobs_failed} failure{'' if jobs_failed == 1 else 's'}" if jobs_failed > 0 else ""
    completed_string = f"{jobs_completed} completed job{'' if jobs_completed == 1 else 's'}"
    
    print("")
    print("=" * 80)
    print("Result:")
    if len(completed_string) > 0:
        print(f" - {completed_string}")
    if len(failure_string) > 0:
        print(f" - {failure_string}")
    print("=" * 80)


@app.local_entrypoint()
def local_main(*args):
    """
    Local entrypoint to run training on Modal.

    Usage:
        modal run modal_train_deploy.py config/my_training.yaml
        modal run modal_train_deploy.py config/training1.yaml config/training2.yaml --recover
        modal run modal_train_deploy.py config/my_training.yaml --name custom_name
    """
    import argparse

    parser = argparse.ArgumentParser(description="Z-Image Turbo LoRA Training on Modal")
    parser.add_argument("config_files", nargs="+", help="Config file(s) to run")
    parser.add_argument("--recover", action="store_true", help="Continue running jobs even if one fails")
    parser.add_argument("--name", type=str, default=None, help="Optional name to replace [name] tag in config")

    parsed = parser.parse_args(args=args)

    # Convert list to comma-separated string
    config_file_list_str = ",".join(parsed.config_files)

    result = main.remote(
        config_file_list_str=config_file_list_str,
        recover=parsed.recover,
        name=parsed.name
    )

    print(f"\nTraining execution completed")
    return result

