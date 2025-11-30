import torch
from diffusers import ZImagePipeline
from safetensors.torch import load_file
from transformers import pipeline as hf_pipeline


class SafetyChecker:
    def __init__(self, device: str = "cuda"):
        self.classifier = hf_pipeline(
            "image-classification",
            model="Falconsai/nsfw_image_detection",
            device=device,
        )

    def check(self, image) -> dict:
        """Return NSFW scores for an image."""
        results = self.classifier(image)
        # Convert list of {label, score} to dict
        return {r["label"]: r["score"] for r in results}


class ZImageModel:
    def __init__(self, model_id: str, cache_dir: str, device: str = "cuda"):
        torch.backends.cuda.matmul.allow_tf32 = True
        self.pipe = ZImagePipeline.from_pretrained(
            model_id,
            torch_dtype=torch.bfloat16,
            cache_dir=cache_dir,
        )
        self.pipe.to(device)
        self._lora_state = None

    def load_lora(self, lora_path: str, scale: float = 1.0):
        """Load LoRA weights by directly merging into model weights."""
        state_dict = load_file(lora_path)

        # Get LoRA rank and alpha from the weights
        lora_rank = None
        for key, value in state_dict.items():
            if "lora_A" in key or "lora_down" in key:
                lora_rank = value.shape[0]
                break

        if lora_rank is None:
            raise ValueError("Could not determine LoRA rank from weights")

        # Default alpha to rank (common convention)
        lora_alpha = lora_rank

        # Compute the scaling factor
        lora_scale = scale * (lora_alpha / lora_rank)

        # Group lora_A and lora_B pairs
        lora_pairs = {}
        for key, value in state_dict.items():
            # Normalize key - remove diffusion_model. prefix if present
            base_key = key.replace("diffusion_model.", "")

            if ".lora_A." in base_key or ".lora_down." in base_key:
                # Extract the module path (everything before .lora_A or .lora_down)
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

        # Apply LoRA weights by merging: W' = W + scale * (B @ A)
        # Track applied deltas for rollback on error
        transformer = self.pipe.transformer
        applied = []  # [(module, delta), ...] for rollback
        try:
            for module_path, pair in lora_pairs.items():
                if "A" not in pair or "B" not in pair:
                    continue

                # Navigate to the target module
                parts = module_path.split(".")
                module = transformer
                for part in parts:
                    if part.isdigit():
                        module = module[int(part)]
                    else:
                        module = getattr(module, part)

                # Check module has weights
                if not hasattr(module, "weight"):
                    raise ValueError(f"Module {module_path} has no weight attribute")

                # Compute delta: B @ A, scaled
                lora_A = pair["A"].to(module.weight.device, dtype=module.weight.dtype)
                lora_B = pair["B"].to(module.weight.device, dtype=module.weight.dtype)
                delta = (lora_B @ lora_A) * lora_scale

                # Merge into weights
                module.weight.data += delta
                applied.append((module, delta))

        except Exception:
            # Rollback any applied deltas
            for module, delta in applied:
                module.weight.data -= delta
            raise

        # Store the pairs for potential unloading
        self._lora_state = {"pairs": lora_pairs, "scale": lora_scale}

    def unload_lora(self):
        """Remove LoRA weights from the model by reversing the merge."""
        if self._lora_state is None:
            return

        lora_pairs = self._lora_state["pairs"]
        lora_scale = self._lora_state["scale"]
        transformer = self.pipe.transformer

        for module_path, pair in lora_pairs.items():
            if "A" not in pair or "B" not in pair:
                continue

            # Navigate to the target module
            parts = module_path.split(".")
            module = transformer
            for part in parts:
                if part.isdigit():
                    module = module[int(part)]
                else:
                    module = getattr(module, part)

            # Compute delta and subtract it
            lora_A = pair["A"].to(module.weight.device, dtype=module.weight.dtype)
            lora_B = pair["B"].to(module.weight.device, dtype=module.weight.dtype)
            delta = (lora_B @ lora_A) * lora_scale
            module.weight.data -= delta

        self._lora_state = None

    def generate(
        self,
        prompt: str,
        height: int = 1024,
        width: int = 1024,
        num_inference_steps: int = 9,
        seed: int | None = None,
        safety_checker: SafetyChecker | None = None,
    ) -> dict:
        generator = torch.Generator("cuda").manual_seed(seed) if seed is not None else None

        image = self.pipe(
            prompt=prompt,
            height=height,
            width=width,
            num_inference_steps=num_inference_steps,
            guidance_scale=0.0,
            generator=generator,
        ).images[0]

        # Run safety check if provided
        safety_scores = None
        if safety_checker:
            safety_scores = safety_checker.check(image)

        from io import BytesIO
        buffer = BytesIO()
        image.save(buffer, format="PNG")

        return {
            "image_bytes": buffer.getvalue(),
            "safety_scores": safety_scores,
        }
