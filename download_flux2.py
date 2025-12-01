#!/usr/bin/env python3
"""Download FLUX.2 model to specified directory"""
import os
from pathlib import Path
from huggingface_hub import snapshot_download
from dotenv import load_dotenv

load_dotenv()

MODEL_ID = "black-forest-labs/FLUX.2-dev"
OUTPUT_DIR = Path("/home/nfmil/model_vault/flux2")
HF_TOKEN = os.environ.get("HF_TOKEN", "")

print(f"Downloading {MODEL_ID} to {OUTPUT_DIR}")
print(f"HF_TOKEN available: {bool(HF_TOKEN)}")

# Create output directory
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

try:
    snapshot_download(
        repo_id=MODEL_ID,
        local_dir=str(OUTPUT_DIR),
        token=HF_TOKEN if HF_TOKEN else None,
        local_dir_use_symlinks=False,
    )
    print(f"\n✓ Successfully downloaded FLUX.2 model to {OUTPUT_DIR}")
    print(f"Model size: {sum(f.stat().st_size for f in OUTPUT_DIR.rglob('*') if f.is_file()) / (1024**3):.2f} GB")
except Exception as e:
    print(f"\n✗ Error downloading model: {e}")
    print("\nNote: FLUX.2-dev might not be available on HuggingFace yet.")
    print("FLUX.2 may require installation from the GitHub repository:")
    print("  https://github.com/black-forest-labs/flux2")
    raise

