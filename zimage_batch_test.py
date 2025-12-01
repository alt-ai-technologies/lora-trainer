"""
Batch testing script for LoRA comparison.
Loads the model ONCE, then tests multiple LoRAs/scales/prompts.

Usage:
    uv run modal run zimage_batch_test.py
"""

import os
import modal
from pathlib import Path

if modal.is_local():
    from dotenv import load_dotenv
    load_dotenv()

app = modal.App("zimage-batch-test")

hf_secret = modal.Secret.from_dict({"HF_TOKEN": os.environ.get("HF_TOKEN", "")})
model_cache = modal.Volume.from_name("model-cache", create_if_missing=True)
training_output = modal.Volume.from_name("training-output", create_if_missing=True)

CACHE_DIR = "/model-cache"
LORA_DIR = "/training-output"
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
    #gpu="A100-80GB",
    gpu="h100",
    image=image,
    timeout=1800,  # 30 min for batch
    secrets=[hf_secret],
    volumes={CACHE_DIR: model_cache, LORA_DIR: training_output},
)
class BatchTester:
    @modal.enter()
    def enter(self):
        from huggingface_hub import snapshot_download

        snapshot_download(MODEL_ID, cache_dir=CACHE_DIR, token=os.environ.get("HF_TOKEN"))
        model_cache.commit()

        self.model = ZImageModel(MODEL_ID, CACHE_DIR)
        print("Model loaded and ready for batch testing")

    @modal.method()
    def run_tests(self, tests: list[dict]) -> list[dict]:
        """
        Run multiple tests on the same loaded model.

        Each test dict: {
            "lora": str or None,
            "scale": float,
            "prompt": str,
            "seed": int,
        }

        Returns list of results with image bytes.
        """
        results = []
        current_lora = None

        for i, test in enumerate(tests):
            lora = test.get("lora")
            scale = test.get("scale", 1.0)
            prompt = test["prompt"]
            seed = test.get("seed", 42)

            print(f"\n[{i+1}/{len(tests)}] Testing: lora={lora}, scale={scale}")
            print(f"  Prompt: {prompt[:50]}...")

            # Load/unload LoRA only if changed
            if lora != current_lora:
                if current_lora is not None:
                    self.model.unload_lora()

                if lora is not None:
                    lora_path = f"{LORA_DIR}/{lora}.safetensors"
                    if os.path.exists(lora_path):
                        self.model.load_lora(lora_path, scale=scale)
                    else:
                        print(f"  WARNING: LoRA not found: {lora_path}")
                        results.append({"error": f"LoRA not found: {lora}"})
                        continue

                current_lora = lora
            elif lora is not None and scale != test.get("_prev_scale"):
                # Same LoRA but different scale - reload with new scale
                self.model.unload_lora()
                lora_path = f"{LORA_DIR}/{lora}.safetensors"
                self.model.load_lora(lora_path, scale=scale)

            test["_prev_scale"] = scale

            # Generate
            result = self.model.generate(
                prompt=prompt,
                seed=seed,
            )

            results.append({
                "lora": lora,
                "scale": scale,
                "prompt": prompt,
                "seed": seed,
                "image_bytes": result["image_bytes"],
            })

            print(f"  Done!")

        # Cleanup
        if current_lora is not None:
            self.model.unload_lora()

        return results


@app.local_entrypoint()
def main():
    from datetime import datetime

    # === CONFIGURE YOUR TESTS HERE ===

    loras = [
        "zach_1500steps_r16_lr1e04_20251130_175816",
        "zach_1500steps_r32_lr2e04_20251130_175927",
        "zach_2000steps_r32_lr1e04_20251130_172202",
        "zach_1500steps_r32_lr1e04_20251130_172219",
        "zach_1500steps_r32_lr1e04_20251130_184159",
        "zach_1000steps_r32_lr2e04_20251130_184153",
    ]

    scales = [0.6, 0.8, 1.0, 1.2]

    prompts = [
        "TOK, wide shot, distant shot, full body shot, long shot, a man with a beard, wearing glasses, in the tone of 'A relaxed male figure sits at a rustic wooden table in a cozy coffee shop, bathed in warm, golden lighting filtering through large windows. He's casually dressed in a flannel shirt or hoodie, hands wrapped around a ceramic mug of steaming coffee, steam curling upward in the ambient light. The background features exposed brick walls, vintage Edison bulbs, and the soft hum of espresso machines, creating an atmosphere of comfortable solitude and urban warmth. The color palette is rich with warm browns, deep amber tones, and the soft glow of afternoon sunlight.', a man with realistic facial proportions and features, natural body type and proportions, fully visible face, highly expressive face with clear emotions, emotionally engaging expression, dynamic but natural body language",
        "TOK, wide shot, distant shot, full body shot, long shot, a man with a beard, wearing glasses, in the tone of 'A male astronaut in a bulky white spacesuit stands on the stark, gray lunar surface, holding the string of a colorful kite that floats eerily in the airless void. The scene is bathed in harsh, unfiltered sunlight casting deep black shadows across the cratered moonscape, while Earth hangs as a brilliant blue marble in the star-filled black sky. The kite defies physics, suspended in the vacuum of space, creating a surreal juxtaposition between childhood wonder and the alien desolation of the Moon's surface.', a man with realistic facial proportions and features, natural body type and proportions, fully visible face, highly expressive face with clear emotions, emotionally engaging expression, dynamic but natural body language",
        "TOK, wide shot, distant shot, full body shot, long shot, a man with a beard wearing glasses, in the tone of 'A muscular male warrior locked in fierce combat with a massive Tyrannosaurus Rex, sweat and dirt streaking his face as he grips a primitive weapon. The scene is bathed in harsh, dramatic lighting with deep shadows and golden highlights, capturing the raw intensity of primal survival. Dust and debris fill the air around them, while the T-Rex's massive jaws snap inches from the fighter's determined expression. The atmosphere is electric with danger, adrenaline, and the brutal clash between man and prehistoric beast.', a man with realistic facial proportions and features, natural body type and proportions, fully visible face, highly expressive face with clear emotions, emotionally engaging expression, dynamic but natural body language",
        "TOK, wide shot, distant shot, full body shot, long shot, a man with a beard, wearing glasses, in the tone of 'A triumphant male figure stands at the peak of victory, arms raised in celebration, bathed in golden stadium lights and confetti falling like rain. His face radiates pure elation and exhaustion, sweat glistening as he holds a championship trophy or medal high above his head. The atmosphere is electric with energy—roaring crowds blur into streaks of color in the background, while spotlights create dramatic shadows and highlights across his athletic form. The scene captures the raw emotion of ultimate achievement, where years of dedication culminate in a single, perfect moment of glory.', a man with realistic facial proportions and features, natural body type and proportions, fully visible face, highly expressive face with clear emotions, emotionally engaging expression, dynamic but natural body language",
    ]

    seed = 42  # Fixed seed for fair comparison

    # === BUILD TEST MATRIX ===

    tests = []

    # Test with no LoRA (baseline)
    for prompt in prompts:
        tests.append({
            "lora": None,
            "scale": 1.0,
            "prompt": prompt,
            "seed": seed,
        })

    # Test each LoRA at each scale
    for lora in loras:
        for scale in scales:
            for prompt in prompts:
                tests.append({
                    "lora": lora,
                    "scale": scale,
                    "prompt": prompt,
                    "seed": seed,
                })

    print(f"Running {len(tests)} tests...")
    print(f"  {len(loras)} LoRAs × {len(scales)} scales × {len(prompts)} prompts + {len(prompts)} baseline")

    # Run batch
    tester = BatchTester()
    results = tester.run_tests.remote(tests)

    # Save results
    output_dir = Path("output/batch_test_" + datetime.now().strftime("%Y%m%d_%H%M%S"))
    output_dir.mkdir(parents=True, exist_ok=True)

    for i, r in enumerate(results):
        if "error" in r:
            print(f"Error: {r['error']}")
            continue

        lora_name = r["lora"] or "nolora"
        scale = r["scale"]
        # Use index + key words from prompt to make unique filename
        prompt = r["prompt"].lower()
        if "coffee" in prompt:
            scene = "coffee"
        elif "astronaut" in prompt or "lunar" in prompt or "moon" in prompt:
            scene = "moon"
        elif "t-rex" in prompt or "dinosaur" in prompt or "warrior" in prompt:
            scene = "trex"
        elif "victory" in prompt or "trophy" in prompt or "champion" in prompt:
            scene = "victory"
        else:
            scene = f"prompt{i}"

        filename = f"{lora_name}_s{scale}_{scene}.png"
        filepath = output_dir / filename
        filepath.write_bytes(r["image_bytes"])

    print(f"\nSaved {len(results)} images to {output_dir}/")
    print("Open the folder and compare!")
