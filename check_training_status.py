#!/usr/bin/env python3
"""Check training status and list saved files."""

import modal

app = modal.App("check-training-status")

image = modal.Image.debian_slim(python_version="3.11")

MOUNT_DIR = "/root/modal_output"
training_output_volume = modal.Volume.from_name("zimage-training-outputs", create_if_missing=True)

@app.function(
    volumes={MOUNT_DIR: training_output_volume},
    timeout=60,
)
def check_outputs():
    from pathlib import Path
    import os
    
    output_dir = Path(MOUNT_DIR)
    
    print("=" * 60)
    print("Training Output Status")
    print("=" * 60)
    print(f"Output directory: {output_dir}")
    print()
    
    if not output_dir.exists():
        print("Output directory does not exist yet.")
        return
    
    # Find all training folders
    training_folders = [d for d in output_dir.iterdir() if d.is_dir()]
    
    if not training_folders:
        print("No training folders found.")
        return
    
    for folder in training_folders:
        print(f"\nTraining: {folder.name}")
        print("-" * 60)
        
        # Check for LoRA files
        lora_files = list(folder.rglob("*.safetensors"))
        if lora_files:
            print(f"\nLoRA files ({len(lora_files)}):")
            for f in sorted(lora_files):
                size = f.stat().st_size / (1024 * 1024)  # MB
                print(f"  - {f.name} ({size:.2f} MB)")
        
        # Check for sample images
        sample_dirs = [d for d in folder.iterdir() if d.is_dir() and 'sample' in d.name.lower()]
        if sample_dirs:
            print(f"\nSample directories:")
            for sample_dir in sample_dirs:
                images = list(sample_dir.glob("*.png")) + list(sample_dir.glob("*.jpg"))
                print(f"  - {sample_dir.name}: {len(images)} images")
        
        # Check for checkpoints
        checkpoint_dirs = [d for d in folder.iterdir() if d.is_dir() and ('checkpoint' in d.name.lower() or 'step' in d.name.lower())]
        if checkpoint_dirs:
            print(f"\nCheckpoint directories:")
            for ckpt_dir in checkpoint_dirs:
                files = list(ckpt_dir.rglob("*"))
                print(f"  - {ckpt_dir.name}: {len(files)} files")
        
        # List all files
        all_files = list(folder.rglob("*"))
        files_only = [f for f in all_files if f.is_file()]
        if files_only:
            print(f"\nAll files ({len(files_only)}):")
            for f in sorted(files_only)[:20]:  # Show first 20
                rel_path = f.relative_to(folder)
                size = f.stat().st_size / 1024  # KB
                print(f"  - {rel_path} ({size:.1f} KB)")
            if len(files_only) > 20:
                print(f"  ... and {len(files_only) - 20} more files")

@app.local_entrypoint()
def main():
    check_outputs.remote()

if __name__ == "__main__":
    main()

