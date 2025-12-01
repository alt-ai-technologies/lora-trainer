#!/usr/bin/env python3
"""Download the step 500 LoRA checkpoint locally for use with the CLI."""

import modal
import subprocess
from pathlib import Path

def download_lora_locally(output_dir="./lora_checkpoints"):
    """Download LoRA from Modal volume to local directory."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    lora_name = "zimage_turbo_book_covers_lora_v1_000000500.safetensors"
    volume_path = f"zimage_turbo_book_covers_lora_v1/{lora_name}"
    local_path = output_path / lora_name
    
    print("=" * 60)
    print("Downloading LoRA Checkpoint (Step 500)")
    print("=" * 60)
    print(f"From: Modal volume (zimage-training-outputs)")
    print(f"To: {local_path.absolute()}")
    print()
    
    try:
        # Use modal volume get command
        cmd = [
            "modal", "volume", "get",
            "zimage-training-outputs",
            volume_path,
            str(local_path)
        ]
        
        print(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        
        print()
        print("=" * 60)
        print("✓ Download complete!")
        print(f"✓ LoRA saved to: {local_path.absolute()}")
        print()
        print("You can now use it with:")
        print(f"  python book_cover_generator.py --lora-path {local_path.absolute()} --title 'My Book' --genre thriller")
        print("=" * 60)
        
        return str(local_path.absolute())
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error downloading: {e.stderr}")
        print()
        print("Make sure you have Modal CLI installed and authenticated:")
        print("  pip install modal")
        print("  modal token new")
        return None
    except FileNotFoundError:
        print("❌ Modal CLI not found. Install with: pip install modal")
        return None

if __name__ == "__main__":
    import sys
    output_dir = sys.argv[1] if len(sys.argv) > 1 else "./lora_checkpoints"
    download_lora_locally(output_dir)

