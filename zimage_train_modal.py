"""
Modal wrapper for Z-Image-Turbo LoRA training.

Usage:
    uv run modal run zimage_train_modal.py --dataset ./my_images --output my_lora
"""

import os
import modal
from pathlib import Path

app = modal.App("zimage-turbo-train")

# Persistent volumes
hf_cache = modal.Volume.from_name("model-cache", create_if_missing=True)
training_output = modal.Volume.from_name("training-output", create_if_missing=True)

CACHE_DIR = "/model-cache"
OUTPUT_DIR = "/training-output"

image = (
    modal.Image.debian_slim(python_version="3.12")
    .apt_install("git")
    .pip_install(
        "torch",
        "transformers",
        "accelerate",
        "peft",
        "safetensors",
        "pillow",
        "tqdm",
        "huggingface_hub",
        "hf_transfer",
        "git+https://github.com/huggingface/diffusers",
        index_url="https://download.pytorch.org/whl/cu121",
        extra_index_url="https://pypi.org/simple",
    )
    .env({
        "HF_HUB_ENABLE_HF_TRANSFER": "1",
        "HF_HOME": CACHE_DIR,
    })
    .add_local_file("zimage_train.py", "/root/zimage_train.py")
)


@app.function(
    gpu="H100:2",
    image=image,
    timeout=7200,  # 2 hours
    volumes={
        CACHE_DIR: hf_cache,
        OUTPUT_DIR: training_output,
    },
)
def train(
    dataset_files: dict[str, bytes],
    output_name: str,
    steps: int = 2000,
    batch_size: int = 2,  # 4 OOMs on H100
    lr: float = 1e-4,
    lora_rank: int = 32,
):
    """Run training on Modal with uploaded dataset."""
    import subprocess
    from huggingface_hub import hf_hub_download

    # Write dataset files to temp directory
    dataset_dir = Path("/tmp/dataset")
    dataset_dir.mkdir(parents=True, exist_ok=True)

    for filename, content in dataset_files.items():
        filepath = dataset_dir / filename
        filepath.write_bytes(content)

    print(f"Loaded {len(dataset_files)} files to {dataset_dir}")

    # Download training adapter
    adapter_path = hf_hub_download(
        repo_id="ostris/zimage_turbo_training_adapter",
        filename="zimage_turbo_training_adapter_v1.safetensors",
        cache_dir=CACHE_DIR,
    )
    hf_cache.commit()

    # Output path
    output_path = f"{OUTPUT_DIR}/{output_name}.safetensors"

    # Run training with accelerate for multi-GPU
    cmd = [
        "accelerate", "launch",
        "--multi_gpu",
        "--num_processes", "2",
        "/root/zimage_train.py",
        "--dataset", str(dataset_dir),
        "--output", output_path,
        "--adapter", adapter_path,
        "--steps", str(steps),
        "--batch-size", str(batch_size),
        "--lr", str(lr),
        "--lora-rank", str(lora_rank),
        "--cache-dir", CACHE_DIR,
    ]

    result = subprocess.run(cmd, check=True)

    # Commit output volume
    training_output.commit()
    hf_cache.commit()

    print(f"Training complete! Output saved to volume: {output_path}")
    return output_path


@app.local_entrypoint()
def main(*args):
    import argparse

    parser = argparse.ArgumentParser(description="Train Z-Image-Turbo LoRA on Modal")
    parser.add_argument("--dataset", required=True, help="Path to local dataset folder")
    parser.add_argument("--output", required=True, help="Output name for LoRA (saved to Modal volume)")
    parser.add_argument("--steps", type=int, default=2000)
    parser.add_argument("--batch-size", type=int, default=2)
    parser.add_argument("--lr", type=float, default=1e-4)
    parser.add_argument("--lora-rank", type=int, default=32)

    parsed = parser.parse_args(args)

    # Load dataset files
    dataset_path = Path(parsed.dataset)
    if not dataset_path.exists():
        raise ValueError(f"Dataset folder not found: {dataset_path}")

    dataset_files = {}
    for filepath in dataset_path.iterdir():
        if filepath.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp", ".txt"]:
            dataset_files[filepath.name] = filepath.read_bytes()

    if not dataset_files:
        raise ValueError(f"No image/caption files found in {dataset_path}")

    print(f"Uploading {len(dataset_files)} files from {dataset_path}")
    print(f"Using 2x H100")

    # Generate output name with hyperparams and timestamp
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    lr_str = f"{parsed.lr:.0e}".replace("-", "")  # 1e-4 -> 1e04
    output_name = f"{parsed.output}_{parsed.steps}steps_r{parsed.lora_rank}_lr{lr_str}_{timestamp}"
    print(f"Output name: {output_name}")

    # Run training
    output_path = train.remote(
        dataset_files=dataset_files,
        output_name=output_name,
        steps=parsed.steps,
        batch_size=parsed.batch_size,
        lr=parsed.lr,
        lora_rank=parsed.lora_rank,
    )

    print(f"\nTraining complete!")
    print(f"Output saved to Modal volume 'training-output' at: {output_path}")
    print(f"\nTo generate with this LoRA:")
    print(f"  uv run modal run zimage_turbo_gen.py --prompt \"your prompt\" --lora {output_name}")
    print(f"\nTo download:")
    print(f"  modal volume get training-output {output_path} ./{output_name}.safetensors")
