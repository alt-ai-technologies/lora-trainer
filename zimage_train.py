"""
Minimal Z-Image-Turbo LoRA training script with multi-GPU support.

Usage:
    # Single GPU
    python zimage_train.py --dataset ./my_images --output ./my_lora

    # Multi-GPU with accelerate
    accelerate launch zimage_train.py --dataset ./my_images --output ./my_lora
"""

import argparse
import math
import os
from pathlib import Path

import torch
from torch.utils.data import Dataset, DataLoader
from accelerate import Accelerator
from diffusers import ZImagePipeline, FlowMatchEulerDiscreteScheduler
from peft import LoraConfig, get_peft_model
from PIL import Image
from safetensors.torch import save_file
from tqdm import tqdm


# Common aspect ratio buckets for training
BUCKETS = [
    (512, 512),
    (576, 448), (448, 576),
    (640, 384), (384, 640),
    (768, 512), (512, 768),
    (896, 448), (448, 896),
    (1024, 512), (512, 1024),
    (1024, 768), (768, 1024),
    (1024, 1024),
]


def find_best_bucket(width: int, height: int) -> tuple[int, int]:
    """Find the bucket that best matches the image aspect ratio."""
    aspect = width / height
    best_bucket = min(BUCKETS, key=lambda b: abs(b[0]/b[1] - aspect))
    return best_bucket


class ImageCaptionDataset(Dataset):
    """Simple dataset that loads images and their caption files."""

    def __init__(self, folder: str, tokenizer, text_encoder, vae, device: str = "cuda"):
        self.folder = Path(folder)
        self.tokenizer = tokenizer
        self.text_encoder = text_encoder
        self.vae = vae
        self.device = device

        # Find all images with matching caption files
        self.samples = []
        for img_path in self.folder.glob("*"):
            if img_path.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp"]:
                caption_path = img_path.with_suffix(".txt")
                if caption_path.exists():
                    self.samples.append((img_path, caption_path))

        if not self.samples:
            raise ValueError(f"No image/caption pairs found in {folder}")

        print(f"Found {len(self.samples)} training samples")

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        img_path, caption_path = self.samples[idx]

        # Load and preprocess image
        image = Image.open(img_path).convert("RGB")
        bucket_w, bucket_h = find_best_bucket(image.width, image.height)
        image = image.resize((bucket_w, bucket_h), Image.LANCZOS)

        # Convert to tensor and normalize to [-1, 1]
        img_tensor = torch.tensor(list(image.getdata()), dtype=torch.float32)
        img_tensor = img_tensor.view(bucket_h, bucket_w, 3).permute(2, 0, 1) / 127.5 - 1.0

        # Load caption
        caption = caption_path.read_text().strip()

        return {
            "image": img_tensor,
            "caption": caption,
            "bucket": (bucket_w, bucket_h),
        }


def collate_fn(batch):
    """Collate function that groups by bucket size."""
    # For simplicity, just use the first item's bucket
    # A more sophisticated version would batch by bucket
    return {
        "images": torch.stack([item["image"] for item in batch]),
        "captions": [item["caption"] for item in batch],
        "bucket": batch[0]["bucket"],
    }


def encode_prompt(tokenizer, text_encoder, prompt: str, device: str) -> torch.Tensor:
    """Encode a text prompt to embeddings."""
    inputs = tokenizer(
        prompt,
        padding="max_length",
        max_length=512,
        truncation=True,
        return_tensors="pt",
    )
    input_ids = inputs.input_ids.to(device)
    attention_mask = inputs.attention_mask.to(device)

    with torch.no_grad():
        outputs = text_encoder(input_ids, attention_mask=attention_mask)
        # Use the last hidden state
        prompt_embeds = outputs.last_hidden_state

    return prompt_embeds, attention_mask


def load_training_adapter(transformer, adapter_path: str, device: str, dtype: torch.dtype):
    """
    Load and merge the de-distillation training adapter.
    This "de-distills" the model for stable training.
    Returns state needed to remove the adapter later.
    """
    from safetensors.torch import load_file

    print(f"Loading training adapter from {adapter_path}")
    state_dict = load_file(adapter_path)

    # Get LoRA rank
    lora_rank = None
    for key, value in state_dict.items():
        if "lora_A" in key or "lora_down" in key:
            lora_rank = value.shape[0]
            break

    if lora_rank is None:
        raise ValueError("Could not determine adapter rank")

    # Group lora_A and lora_B pairs
    lora_pairs = {}
    for key, value in state_dict.items():
        base_key = key.replace("diffusion_model.", "")

        if ".lora_A." in base_key or ".lora_down." in base_key:
            if ".lora_A." in base_key:
                module_path = base_key.split(".lora_A.")[0]
            else:
                module_path = base_key.split(".lora_down.")[0]
            if module_path not in lora_pairs:
                lora_pairs[module_path] = {}
            lora_pairs[module_path]["A"] = value
        elif ".lora_B." in base_key or ".lora_up." in base_key:
            if ".lora_B." in base_key:
                module_path = base_key.split(".lora_B.")[0]
            else:
                module_path = base_key.split(".lora_up.")[0]
            if module_path not in lora_pairs:
                lora_pairs[module_path] = {}
            lora_pairs[module_path]["B"] = value

    # Merge adapter into weights: W' = W + (B @ A)
    # Track (module, delta) for removal later
    merged_count = 0
    adapter_state = []
    for module_path, pair in lora_pairs.items():
        if "A" not in pair or "B" not in pair:
            continue

        parts = module_path.split(".")
        module = transformer
        for part in parts:
            if part.isdigit():
                module = module[int(part)]
            else:
                module = getattr(module, part)

        if not hasattr(module, "weight"):
            continue

        lora_A = pair["A"].to(device, dtype=dtype)
        lora_B = pair["B"].to(device, dtype=dtype)
        delta = lora_B @ lora_A
        module.weight.data += delta
        adapter_state.append((module, delta))
        merged_count += 1

    print(f"Merged training adapter into {merged_count} layers")
    return adapter_state


def remove_training_adapter(adapter_state):
    """Remove the training adapter by subtracting the deltas."""
    for module, delta in adapter_state:
        module.weight.data -= delta
    print(f"Removed training adapter from {len(adapter_state)} layers")


def save_lora_weights(model, output_path: str):
    """Save trained LoRA weights in diffusers-compatible format."""
    lora_state_dict = {}

    # Extract LoRA weights from PEFT model
    for name, param in model.named_parameters():
        if "lora_" in name:
            # Convert to diffusers format: transformer.* -> diffusion_model.*
            save_name = name.replace("base_model.model.", "").replace("transformer.", "diffusion_model.")
            lora_state_dict[save_name] = param.detach().cpu()

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    save_file(lora_state_dict, output_path)
    print(f"Saved LoRA weights to {output_path}")


def train(
    dataset_path: str,
    output_path: str,
    model_id: str = "Tongyi-MAI/Z-Image-Turbo",
    adapter_path: str = None,
    steps: int = 2000,
    batch_size: int = 1,
    lr: float = 1e-4,
    lora_rank: int = 32,
    cache_dir: str = None,
):
    """Main training function with accelerate for multi-GPU support."""

    # Initialize accelerator for distributed training
    accelerator = Accelerator(
        gradient_accumulation_steps=1,
        mixed_precision="bf16",
    )

    device = accelerator.device
    dtype = torch.bfloat16

    # Only print on main process
    if accelerator.is_main_process:
        print(f"Training Z-Image-Turbo LoRA")
        print(f"  Dataset: {dataset_path}")
        print(f"  Output: {output_path}")
        print(f"  Steps: {steps}")
        print(f"  Batch size: {batch_size}")
        print(f"  Learning rate: {lr}")
        print(f"  LoRA rank: {lora_rank}")
        print(f"  Devices: {accelerator.num_processes}")

    # Load the pipeline
    if accelerator.is_main_process:
        print("Loading Z-Image-Turbo pipeline...")

    pipe = ZImagePipeline.from_pretrained(
        model_id,
        torch_dtype=dtype,
        cache_dir=cache_dir,
    )

    transformer = pipe.transformer
    vae = pipe.vae
    text_encoder = pipe.text_encoder
    tokenizer = pipe.tokenizer
    scheduler = pipe.scheduler

    # Move components to device
    vae.to(device, dtype=dtype)
    text_encoder.to(device, dtype=dtype)
    transformer.to(device, dtype=dtype)

    # Freeze VAE and text encoder
    vae.requires_grad_(False)
    text_encoder.requires_grad_(False)


    # Load training adapter if provided (de-distills the model)
    adapter_state = None
    if adapter_path:
        adapter_state = load_training_adapter(transformer, adapter_path, device, dtype)

    # Add LoRA to transformer
    if accelerator.is_main_process:
        print("Adding LoRA layers...")

    lora_config = LoraConfig(
        r=lora_rank,
        lora_alpha=lora_rank,  # alpha = rank is common convention
        target_modules=["to_q", "to_k", "to_v", "to_out.0"],
        lora_dropout=0.0,
    )
    transformer = get_peft_model(transformer, lora_config)

    if accelerator.is_main_process:
        transformer.print_trainable_parameters()

    # Create dataset
    dataset = ImageCaptionDataset(
        dataset_path,
        tokenizer=tokenizer,
        text_encoder=text_encoder,
        vae=vae,
        device=device,
    )

    # Pre-compute and cache all latents and text embeddings
    if accelerator.is_main_process:
        print("Caching latents and text embeddings...")

    cached_samples = []
    with torch.no_grad():
        for idx in tqdm(range(len(dataset)), desc="Caching", disable=not accelerator.is_main_process):
            sample = dataset[idx]
            img_tensor = sample["image"].unsqueeze(0).to(device, dtype=dtype)

            # Encode image to latent
            latent = vae.encode(img_tensor).latent_dist.sample()
            latent = latent.squeeze(0) * vae.config.scaling_factor

            # Encode text
            prompt_embeds, attention_mask = encode_prompt(
                tokenizer, text_encoder, sample["caption"], device
            )

            cached_samples.append({
                "latent": latent,
                "prompt_embeds": prompt_embeds.squeeze(0),
                "attention_mask": attention_mask.squeeze(0),
            })

    if accelerator.is_main_process:
        print(f"Cached {len(cached_samples)} samples")

    # Simple cached dataloader
    def get_batch(batch_indices):
        latents = torch.stack([cached_samples[i]["latent"] for i in batch_indices])
        prompt_embeds = torch.stack([cached_samples[i]["prompt_embeds"] for i in batch_indices])
        return latents, prompt_embeds

    dataloader = DataLoader(
        list(range(len(cached_samples))),
        batch_size=batch_size,
        shuffle=True,
        num_workers=0,
    )

    # Optimizer
    optimizer = torch.optim.AdamW(
        transformer.parameters(),
        lr=lr,
        weight_decay=0.01,
    )

    # Prepare for distributed training
    transformer, optimizer = accelerator.prepare(transformer, optimizer)

    # Training loop - step-based
    global_step = 0
    transformer.train()

    progress_bar = tqdm(
        total=steps,
        desc="Training",
        disable=not accelerator.is_main_process,
    )

    while global_step < steps:
        for batch_indices in dataloader:
            if global_step >= steps:
                break

            with accelerator.accumulate(transformer):
                # Get cached latents and embeddings
                latents, prompt_embeds = get_batch(batch_indices.tolist())
                latents = latents.to(device, dtype=dtype)
                prompt_embeds = prompt_embeds.to(device, dtype=dtype)

                # Sample noise and timesteps for flow matching
                noise = torch.randn_like(latents)
                # Sample timesteps in [0, 1000] range, then convert for model
                timesteps = torch.randint(0, 1000, (latents.shape[0],), device=device)

                # Flow matching forward: x_t = (1 - t) * x_0 + t * noise
                t_normalized = timesteps.float() / 1000.0
                t_expanded = t_normalized.view(-1, 1, 1, 1)
                noisy_latents = (1 - t_expanded) * latents + t_expanded * noise

                # Z-Image expects [B, C, F, H, W] with frames dimension
                noisy_latents = noisy_latents.unsqueeze(2)  # Add frames dim
                # Convert to list of tensors (one per batch item)
                latent_list = list(noisy_latents.unbind(dim=0))

                # Timestep format for Z-Image: (1000 - t) / 1000
                timestep_model_input = (1000 - timesteps.float()) / 1000.0

                # Predict velocity using Z-Image API
                model_out_list = transformer(
                    latent_list,
                    timestep_model_input,
                    prompt_embeds,
                )[0]

                # Process output: stack, squeeze frames dim, negate
                model_pred = torch.stack([t.float() for t in model_out_list], dim=0)
                model_pred = model_pred.squeeze(2)  # Remove frames dim
                model_pred = -model_pred  # Z-Image outputs need negation

                # Flow matching target: velocity = noise - x_0
                target = (noise - latents).float()
                loss = torch.nn.functional.mse_loss(model_pred, target)

                accelerator.backward(loss)
                optimizer.step()
                optimizer.zero_grad()

                global_step += 1
                progress_bar.update(1)
                progress_bar.set_postfix(loss=loss.detach().item())

    progress_bar.close()

    # Save the trained LoRA
    if accelerator.is_main_process:
        # Unwrap the model if distributed
        unwrapped_model = accelerator.unwrap_model(transformer)

        # Remove training adapter before saving so the LoRA works with the original model
        if adapter_state:
            remove_training_adapter(adapter_state)

        save_lora_weights(unwrapped_model, output_path)

    accelerator.wait_for_everyone()
    if accelerator.is_main_process:
        print("Training complete!")


def main():
    parser = argparse.ArgumentParser(description="Train Z-Image-Turbo LoRA")
    parser.add_argument("--dataset", required=True, help="Path to dataset folder")
    parser.add_argument("--output", required=True, help="Output path for LoRA weights")
    parser.add_argument("--model", default="Tongyi-MAI/Z-Image-Turbo", help="Model ID")
    parser.add_argument("--adapter", default=None, help="Training adapter path")
    parser.add_argument("--steps", type=int, default=2000, help="Training steps")
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--lr", type=float, default=1e-4)
    parser.add_argument("--lora-rank", type=int, default=32)
    parser.add_argument("--cache-dir", default=None, help="HuggingFace cache directory")

    args = parser.parse_args()

    train(
        dataset_path=args.dataset,
        output_path=args.output,
        model_id=args.model,
        adapter_path=args.adapter,
        steps=args.steps,
        batch_size=args.batch_size,
        lr=args.lr,
        lora_rank=args.lora_rank,
        cache_dir=args.cache_dir,
    )


if __name__ == "__main__":
    main()
