#!/usr/bin/env python3
"""
Modal deployment script for Z-Image Turbo image generation.

Usage:
    modal run modal_generate_deploy.py config/generate_zimage_simple.yaml
    modal run modal_generate_deploy.py config/generate_zimage.yaml
    modal run modal_generate_deploy.py config/gen1.yaml config/gen2.yaml --recover
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

# Generation outputs - stores generated images
OUTPUT_DIR = "/root/modal_output"
generation_output_volume = modal.Volume.from_name("zimage-generation-outputs", create_if_missing=True)

# Create the Modal app
app = modal.App(
    name="zimage-turbo-generation",
    image=image
)


@app.function(
    # Request a GPU with sufficient VRAM for Z-Image Turbo
    gpu="A100",  # 40GB VRAM - recommended for Z-Image Turbo with quantization
    timeout=3600,  # 1 hour - should be enough for generation
    secrets=[
        modal.Secret.from_name("huggingface"),  # HF token for model access
    ],
    volumes={
        HF_CACHE_DIR: hf_cache_volume,
        OUTPUT_DIR: generation_output_volume,
    }
)
def main(config_file_list_str: str, recover: bool = False, name: str = None):
    """
    Run Z-Image Turbo image generation on Modal.
    
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
    print("Z-Image Turbo Image Generation on Modal")
    print("=" * 80)
    print(f"Running {len(config_file_list)} job{'s' if len(config_file_list) > 1 else ''}")
    print(f"Generated images will be saved to: {OUTPUT_DIR}")
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
            
            # Modify config before creating job to set output folder
            import yaml
            with open(config_path, 'r') as f:
                config_data = yaml.safe_load(f)
            
            # Override output_folder for generation jobs
            if 'config' in config_data and 'process' in config_data['config']:
                for process in config_data['config']['process']:
                    if process.get('type') == 'to_folder' and 'output_folder' in process:
                        process['output_folder'] = OUTPUT_DIR
                    elif 'training_folder' in process:
                        process['training_folder'] = OUTPUT_DIR
            
            # Save modified config temporarily
            temp_config_path = config_path.parent / f".modal_temp_{config_path.name}"
            with open(temp_config_path, 'w') as f:
                yaml.dump(config_data, f)
            
            # Get the job with modified config
            job = get_job(str(temp_config_path), name)
            
            # Clean up temp config
            temp_config_path.unlink()
            
            os.makedirs(OUTPUT_DIR, exist_ok=True)
            print(f"Outputs will be saved to: {OUTPUT_DIR}")
            print()
            
            # Run the job
            job.run()
            
            # Commit volumes after generation
            print()
            print("Committing volumes...")
            hf_cache_volume.commit()
            generation_output_volume.commit()
            print("✓ Volumes committed")
            
            # Cleanup
            job.cleanup()
            jobs_completed += 1
            
            print()
            print(f"✓ Job '{job.name}' completed successfully")
            print(f"  Generated images saved to: {OUTPUT_DIR}")
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
                generation_output_volume.commit()
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
    print(f"Generated images are available in the volume: zimage-generation-outputs")
    print("=" * 80)
    
    if jobs_failed > 0:
        sys.exit(1)


@app.local_entrypoint()
def local_main(config_file_list: str, recover: bool = False, name: str = None):
    """
    Local entrypoint to run image generation on Modal.
    
    Usage:
        modal run modal_generate_deploy.py config/generate_zimage_simple.yaml
        modal run modal_generate_deploy.py config/generate_zimage.yaml
        modal run modal_generate_deploy.py --config-file-list "config/gen1.yaml,config/gen2.yaml" --recover
    """
    # If it's a single file (no commas), use as-is, otherwise split
    if "," in config_file_list:
        config_file_list_str = config_file_list
    else:
        config_file_list_str = config_file_list
    
    result = main.remote(
        config_file_list_str=config_file_list_str,
        recover=recover,
        name=name
    )
    
    print(f"\nImage generation completed")
    print(f"\nTo download generated images, use Modal CLI:")
    print(f"  modal volume download zimage-generation-outputs <local_path>")
    return result

