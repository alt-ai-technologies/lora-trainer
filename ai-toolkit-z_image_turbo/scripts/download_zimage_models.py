#!/usr/bin/env python3
"""
Download Z-Image Turbo models to model vault.

Usage:
    python scripts/download_zimage_models.py

Requires:
    - huggingface_hub installed
    - Hugging Face token (set HF_TOKEN env var or run huggingface-cli login)
"""

import os
import sys
from pathlib import Path
from huggingface_hub import snapshot_download, hf_hub_download

# Model vault location
MODEL_VAULT = Path("/home/nfmil/model_vault")

# Models to download
MODELS = {
    "base": {
        "repo_id": "Tongyi-MAI/Z-Image-Turbo",
        "local_dir": MODEL_VAULT / "Tongyi-MAI" / "Z-Image-Turbo",
        "description": "Z-Image Turbo base model"
    },
    "adapter": {
        "repo_id": "ostris/zimage_turbo_training_adapter",
        "local_dir": MODEL_VAULT / "ostris" / "zimage_turbo_training_adapter",
        "description": "Z-Image Turbo training adapter"
    }
}


def download_model(repo_id: str, local_dir: Path, description: str):
    """Download a model from Hugging Face Hub."""
    print(f"\n{'='*60}")
    print(f"Downloading: {description}")
    print(f"Repository: {repo_id}")
    print(f"Destination: {local_dir}")
    print(f"{'='*60}\n")
    
    # Create parent directory
    local_dir.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        # Download entire repository
        snapshot_download(
            repo_id=repo_id,
            local_dir=str(local_dir),
            local_dir_use_symlinks=False,
            resume_download=True
        )
        print(f"✅ Successfully downloaded {description}")
        print(f"   Location: {local_dir}\n")
        return True
    except Exception as e:
        print(f"❌ Error downloading {description}: {e}\n")
        return False


def main():
    """Main download function."""
    print("Z-Image Turbo Model Downloader")
    print("=" * 60)
    
    # Check if model vault exists
    MODEL_VAULT.mkdir(parents=True, exist_ok=True)
    print(f"Model vault: {MODEL_VAULT}\n")
    
    # Check for Hugging Face token
    hf_token = os.environ.get("HF_TOKEN") or os.environ.get("HUGGING_FACE_HUB_TOKEN")
    if not hf_token:
        print("⚠️  Warning: No HF_TOKEN found in environment.")
        print("   If the model is gated, you may need to:")
        print("   1. Set HF_TOKEN environment variable, or")
        print("   2. Run: huggingface-cli login")
        print("   3. Accept the model license on Hugging Face\n")
    
    # Download models
    results = {}
    for key, model_info in MODELS.items():
        results[key] = download_model(
            repo_id=model_info["repo_id"],
            local_dir=model_info["local_dir"],
            description=model_info["description"]
        )
    
    # Summary
    print("\n" + "=" * 60)
    print("Download Summary")
    print("=" * 60)
    for key, model_info in MODELS.items():
        status = "✅ Success" if results[key] else "❌ Failed"
        print(f"{status}: {model_info['description']}")
        print(f"   Location: {model_info['local_dir']}")
    
    # Check if all succeeded
    if all(results.values()):
        print("\n✅ All models downloaded successfully!")
        print("\nYou can now use local paths in your config:")
        print(f"  name_or_path: \"{MODELS['base']['local_dir']}\"")
        print(f"  assistant_lora_path: \"{MODELS['adapter']['local_dir']}/zimage_turbo_training_adapter_v1.safetensors\"")
        return 0
    else:
        print("\n⚠️  Some downloads failed. Please check the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

