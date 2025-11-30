import os

import modal

if modal.is_local():
    from dotenv import load_dotenv
    load_dotenv()

app = modal.App("zimage-turbo")

hf_secret = modal.Secret.from_dict({"HF_TOKEN": os.environ.get("HF_TOKEN", "")})
model_cache = modal.Volume.from_name("model-cache", create_if_missing=True)

CACHE_DIR = "/model-cache"
MODEL_ID = "Tongyi-MAI/Z-Image-Turbo"

image = (
    modal.Image.debian_slim(python_version="3.12")
    .apt_install("git")
    .pip_install(
        "torch",
        "transformers",
        "accelerate",
        "sentencepiece",
        "huggingface_hub",
        "hf_transfer",
        "peft",
        "safetensors",
        "git+https://github.com/huggingface/diffusers",
        index_url="https://download.pytorch.org/whl/cu121",
        extra_index_url="https://pypi.org/simple",
    )
    .env({
        "HF_HUB_ENABLE_HF_TRANSFER": "1",
        "HF_HOME": CACHE_DIR,
    })
    .add_local_file("zimage.py", "/root/zimage.py")
)

with image.imports():
    from zimage import ZImageModel, SafetyChecker


@app.cls(
    gpu="A100-80GB",
    image=image,
    timeout=300,
    secrets=[hf_secret],
    volumes={CACHE_DIR: model_cache},
)
class ImageGenerator:
    @modal.enter()
    def enter(self):
        from huggingface_hub import snapshot_download

        snapshot_download(MODEL_ID, cache_dir=CACHE_DIR, token=os.environ.get("HF_TOKEN"))
        model_cache.commit()

        self.model = ZImageModel(MODEL_ID, CACHE_DIR)
        self.safety_checker = SafetyChecker()

    @modal.method()
    def generate(
        self,
        prompt: str,
        height: int = 1024,
        width: int = 1024,
        num_inference_steps: int = 9,
        seed: int | None = None,
        lora_id: str | None = None,
        lora_weight_name: str | None = None,
        lora_scale: float = 1.0,
        safe: bool = False,
        nsfw_threshold: float = 0.9,
    ) -> dict:
        from huggingface_hub import hf_hub_download, list_repo_files

        lora_loaded = False
        if lora_id:
            if not lora_weight_name:
                # Auto-detect safetensors file if there's only one
                files = list_repo_files(lora_id, token=os.environ.get("HF_TOKEN"))
                safetensors_files = [f for f in files if f.endswith(".safetensors")]
                if len(safetensors_files) == 0:
                    raise ValueError(f"No .safetensors files found in {lora_id}")
                elif len(safetensors_files) == 1:
                    lora_weight_name = safetensors_files[0]
                else:
                    raise ValueError(
                        f"Multiple .safetensors files in {lora_id}: {safetensors_files}. "
                        "Use --lora-weight-name to specify which one."
                    )
            try:
                lora_path = hf_hub_download(
                    repo_id=lora_id,
                    filename=lora_weight_name,
                    cache_dir=CACHE_DIR,
                    token=os.environ.get("HF_TOKEN"),
                )
                model_cache.commit()
                self.model.load_lora(lora_path, scale=lora_scale)
                lora_loaded = True
            except Exception:
                if lora_loaded:
                    self.model.unload_lora()
                raise

        try:
            result = self.model.generate(
                prompt=prompt,
                height=height,
                width=width,
                num_inference_steps=num_inference_steps,
                seed=seed,
                safety_checker=self.safety_checker,
            )

            # Block NSFW content in safe mode
            if safe and result["safety_scores"]:
                nsfw_score = result["safety_scores"].get("nsfw", 0)
                if nsfw_score > nsfw_threshold:
                    result["blocked"] = True
                    result["image_bytes"] = None
                else:
                    result["blocked"] = False
            else:
                result["blocked"] = False

            return result
        finally:
            if lora_loaded:
                self.model.unload_lora()


@app.local_entrypoint()
def main(
    prompt: str = "a photo of a cat wearing a tiny hat",
    output: str = None,
    seed: int = None,
    lora: str = None,
    lora_weight_name: str = None,
    lora_scale: float = 1.0,
    safe: bool = False,
):
    from utils import get_output_path

    print(f"Generating: {prompt}")
    if lora:
        print(f"Using LoRA: {lora} (scale={lora_scale})")
    if safe:
        print("Safe mode: NSFW content will be blocked")
    generator = ImageGenerator()
    result = generator.generate.remote(
        prompt,
        seed=seed,
        lora_id=lora,
        lora_weight_name=lora_weight_name,
        lora_scale=lora_scale,
        safe=safe,
    )

    if result["safety_scores"]:
        nsfw_score = result["safety_scores"].get("nsfw", 0)
        print(f"Safety: nsfw={nsfw_score:.1%}")

    if result["blocked"]:
        print("Image blocked: NSFW content detected")
        return

    output_path = get_output_path(prompt, output, prefix="zimage")
    output_path.write_bytes(result["image_bytes"])
    print(f"Saved to {output_path}")
