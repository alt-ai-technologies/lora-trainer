#!/usr/bin/env python3
"""
Generate book cover on Modal (for GPU access).

Usage:
    python generate_on_modal.py --title "My Book" --genre thriller
    python generate_on_modal.py --interactive
"""

import argparse
import sys
import os
from pathlib import Path
import yaml
import tempfile

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from book_cover_cli.book_cover_generator import build_prompt, interactive_mode

def create_modal_config(prompt, output_dir, lora_path, width=768, height=1024, steps=8, seed=-1):
    """Create a Modal generation config."""
    config = {
        "job": "generate",
        "config": {
            "name": "book_cover_generation",
            "process": [{
                "type": "to_folder",
                "output_folder": str(output_dir),
                "device": "cuda:0",
                "generate": {
                    "sampler": "ddpm",
                    "width": width,
                    "height": height,
                    "neg": "",
                    "seed": seed,
                    "guidance_scale": 1,
                    "sample_steps": steps,
                    "ext": ".png",
                    "prompt_file": True,
                    "prompts": [prompt]
                },
                "model": {
                    "name_or_path": "Tongyi-MAI/Z-Image-Turbo",
                    "arch": "zimage",
                    "quantize": True,
                    "quantize_te": True,
                    "dtype": "bf16",
                    "inference_lora_path": lora_path
                }
            }]
        }
    }
    return config

def main():
    parser = argparse.ArgumentParser(description="Generate book cover on Modal")
    
    # Same arguments as local CLI
    parser.add_argument("--interactive", "-i", action="store_true")
    parser.add_argument("--title", type=str)
    parser.add_argument("--author", type=str)
    parser.add_argument("--genre", type=str)
    parser.add_argument("--color-scheme", type=str)
    parser.add_argument("--mood", type=str)
    parser.add_argument("--style", type=str)
    parser.add_argument("--typography", type=str)
    parser.add_argument("--elements", type=str)
    parser.add_argument("--width", type=int, default=768)
    parser.add_argument("--height", type=int, default=1024)
    parser.add_argument("--steps", type=int, default=8)
    parser.add_argument("--seed", type=int, default=-1)
    
    args = parser.parse_args()
    
    # Collect inputs
    if args.interactive:
        inputs = interactive_mode()
    else:
        if not args.title:
            print("Error: --title is required (or use --interactive)")
            sys.exit(1)
        inputs = {
            "title": args.title,
            "author": args.author,
            "genre": args.genre,
            "color_scheme": getattr(args, "color_scheme"),
            "mood": args.mood,
            "style": args.style,
            "typography": args.typography,
            "elements": args.elements
        }
    
    # Build prompt
    prompt = build_prompt(
        inputs["title"], inputs["author"], inputs["genre"],
        inputs["color_scheme"], inputs["mood"], inputs["style"],
        inputs["typography"], inputs["elements"]
    )
    
    # Modal paths
    lora_path = "/root/modal_output/zimage_turbo_book_covers_lora_v1/zimage_turbo_book_covers_lora_v1_000000500.safetensors"
    output_dir = "/root/modal_output/book_covers"
    
    print(f"\nPrompt: {prompt}\n")
    print(f"Generating on Modal...")
    print(f"LoRA: {lora_path}")
    print()
    
    # Create config
    config = create_modal_config(prompt, output_dir, lora_path, args.width, args.height, args.steps, args.seed)
    
    # Save to temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)
        config_path = f.name
    
    try:
        # Run on Modal
        import subprocess
        cmd = [
            "modal", "run",
            str(Path(__file__).parent.parent / "modal_generate_deploy.py"),
            "--config-file-list", config_path
        ]
        
        subprocess.run(cmd, check=True)
        
        print("\n✓ Generation complete!")
        print(f"✓ Download images with:")
        print(f"  modal volume get zimage-generation-outputs book_covers ./downloaded_covers")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
    finally:
        if os.path.exists(config_path):
            os.unlink(config_path)

if __name__ == "__main__":
    main()

