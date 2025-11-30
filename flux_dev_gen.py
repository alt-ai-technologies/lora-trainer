import os

import modal

if modal.is_local():
    from dotenv import load_dotenv
    load_dotenv()

app = modal.App("image-gen")

hf_secret = modal.Secret.from_dict({"HF_TOKEN": os.environ.get("HF_TOKEN", "")})
model_cache = modal.Volume.from_name("model-cache", create_if_missing=True)

CACHE_DIR = "/model-cache"
MODEL_ID = "black-forest-labs/FLUX.1-dev"

image = (
    modal.Image.debian_slim(python_version="3.12")
    .pip_install(
        "torch",
        "diffusers",
        "transformers",
        "accelerate",
        "sentencepiece",
        "huggingface_hub",
        "hf_transfer",
        index_url="https://download.pytorch.org/whl/cu121",
        extra_index_url="https://pypi.org/simple",
    )
    .env({
        "HF_HUB_ENABLE_HF_TRANSFER": "1",
        "HF_HOME": CACHE_DIR,
    })
)

with image.imports():
    import torch
    from diffusers import FluxPipeline


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

        torch.backends.cuda.matmul.allow_tf32 = True
        self.pipe = FluxPipeline.from_pretrained(
            MODEL_ID,
            torch_dtype=torch.bfloat16,
            cache_dir=CACHE_DIR,
        )
        self.pipe.to("cuda")

    @modal.method()
    def generate(
        self,
        prompt: str,
        height: int = 1024,
        width: int = 1024,
        guidance_scale: float = 3.5,
        num_inference_steps: int = 50,
        seed: int | None = None,
    ) -> bytes:
        generator = torch.Generator("cuda").manual_seed(seed) if seed is not None else None

        image = self.pipe(
            prompt,
            height=height,
            width=width,
            guidance_scale=guidance_scale,
            num_inference_steps=num_inference_steps,
            generator=generator,
        ).images[0]

        from io import BytesIO
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        return buffer.getvalue()


@app.local_entrypoint()
def main(
    prompt: str = "a photo of a cat wearing a tiny hat",
    output: str = None,
    seed: int = None,
):
    from utils import get_output_path

    print(f"Generating: {prompt}")
    generator = ImageGenerator()
    image_bytes = generator.generate.remote(prompt, seed=seed)

    output_path = get_output_path(prompt, output, prefix="flux")
    output_path.write_bytes(image_bytes)
    print(f"Saved to {output_path}")
