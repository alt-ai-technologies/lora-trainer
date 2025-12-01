#!/usr/bin/env python3
"""
Book Cover Generator CLI

Generate book covers using the trained LoRA model based on user inputs.

Usage:
    python book_cover_generator.py --title "My Book" --author "John Doe" --genre thriller
    python book_cover_generator.py --interactive
    python book_cover_generator.py --title "Sci-Fi Novel" --genre "science fiction" --color-scheme "vibrant neon" --mood "futuristic"
"""

import argparse
import sys
import os
from pathlib import Path
import yaml
import tempfile
from datetime import datetime

# Add parent directory to path to access ai-toolkit
sys.path.insert(0, str(Path(__file__).parent.parent / "ai-toolkit-z_image_turbo"))

def build_prompt(title, author, genre, color_scheme, mood, style, typography, elements):
    """Build a book cover prompt from user inputs."""
    prompt_parts = ["book cover"]
    
    if genre:
        prompt_parts.append(f"{genre.lower()} novel")
    
    if style:
        prompt_parts.append(f"{style.lower()} style")
    else:
        prompt_parts.append("modern design")
    
    if color_scheme:
        prompt_parts.append(f"{color_scheme.lower()} colors")
    
    if mood:
        prompt_parts.append(f"{mood.lower()} atmosphere")
    
    if typography:
        prompt_parts.append(f"{typography.lower()} typography")
    else:
        prompt_parts.append("professional typography")
    
    if elements:
        prompt_parts.append(elements.lower())
    
    if title:
        # Add title context (first few words)
        title_words = title.split()[:3]
        if len(title_words) < len(title.split()):
            prompt_parts.append(f"titled '{' '.join(title_words)}...'")
        else:
            prompt_parts.append(f"titled '{title}'")
    
    if author:
        prompt_parts.append(f"by {author}")
    
    return ", ".join([p for p in prompt_parts if p])

def create_generation_config(prompt, output_dir, lora_path, width=768, height=1024, steps=8, seed=-1):
    """Create a generation config YAML file."""
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
                    "assistant_lora_path": "ostris/zimage_turbo_training_adapter/zimage_turbo_training_adapter_v1.safetensors",
                    "inference_lora_path": lora_path
                }
            }]
        }
    }
    return config

def interactive_mode():
    """Interactive mode to collect user inputs."""
    print("=" * 60)
    print("Book Cover Generator - Interactive Mode")
    print("=" * 60)
    print()
    
    title = input("Book Title: ").strip()
    author = input("Author Name (optional): ").strip() or None
    genre = input("Genre (e.g., thriller, romance, sci-fi, fantasy): ").strip() or None
    
    print("\nDesign Options:")
    color_scheme = input("Color Scheme (e.g., dark, vibrant, pastel, monochrome): ").strip() or None
    mood = input("Mood/Atmosphere (e.g., mysterious, inspiring, dramatic, playful): ").strip() or None
    style = input("Style (e.g., minimalist, bold, elegant, vintage): ").strip() or None
    typography = input("Typography Style (e.g., bold, elegant, modern, classic): ").strip() or None
    elements = input("Additional Elements (e.g., geometric patterns, floral, illustrations): ").strip() or None
    
    return {
        "title": title,
        "author": author,
        "genre": genre,
        "color_scheme": color_scheme,
        "mood": mood,
        "style": style,
        "typography": typography,
        "elements": elements
    }

def find_lora_path(default_path=None):
    """Find the LoRA checkpoint path."""
    # Try Modal volume path first (only if we have permission)
    modal_path = "/root/modal_output/zimage_turbo_book_covers_lora_v1/zimage_turbo_book_covers_lora_v1_000000500.safetensors"
    
    # Try local paths
    local_paths = [
        Path.home() / "modal_output" / "zimage_turbo_book_covers_lora_v1" / "zimage_turbo_book_covers_lora_v1_000000500.safetensors",
        Path(".") / "modal_output" / "zimage_turbo_book_covers_lora_v1" / "zimage_turbo_book_covers_lora_v1_000000500.safetensors",
        Path(__file__).parent.parent / "modal_output" / "zimage_turbo_book_covers_lora_v1" / "zimage_turbo_book_covers_lora_v1_000000500.safetensors",
        Path(".") / "lora_checkpoints" / "zimage_turbo_book_covers_lora_v1_000000500.safetensors",
        Path(__file__).parent / "lora_checkpoints" / "zimage_turbo_book_covers_lora_v1_000000500.safetensors",
    ]
    
    if default_path:
        default_path_obj = Path(default_path)
        if default_path_obj.exists():
            return str(default_path_obj.absolute())
    
    # Check if we're on Modal (path exists and we have permission)
    try:
        if Path(modal_path).exists():
            return modal_path
    except (PermissionError, OSError):
        # Not on Modal or no permission, skip
        pass
    
    # Check local paths
    for path in local_paths:
        if path.exists():
            return str(path.absolute())
    
    # If not found, check if we might be on Modal
    # (but don't try to access /root if we don't have permission)
    try:
        import os
        # Try to check if we're on Modal without causing permission errors
        if os.path.exists("/root") and os.access("/root", os.R_OK):
            # We're on Modal and have access, return Modal path
            return modal_path
    except (PermissionError, OSError):
        pass
    
    # Running locally but LoRA not found
    print()
    print("⚠️  Warning: LoRA checkpoint not found locally!")
    print("   Download it with: python download_lora.py")
    print("   Or specify path with: --lora-path /path/to/lora.safetensors")
    print()
    print("   Attempting to use Modal path (will fail if not on Modal)...")
    return modal_path

def main():
    parser = argparse.ArgumentParser(
        description="Generate book covers using trained LoRA model",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode
  python book_cover_generator.py --interactive
  
  # Command line mode
  python book_cover_generator.py --title "The Dark Forest" --author "Liu Cixin" --genre "science fiction" --color-scheme "dark cosmic" --mood "mysterious"
  
  # Minimal example
  python book_cover_generator.py --title "My Novel" --genre thriller
        """
    )
    
    # Input options
    parser.add_argument("--interactive", "-i", action="store_true",
                       help="Run in interactive mode")
    parser.add_argument("--title", type=str, help="Book title")
    parser.add_argument("--author", type=str, help="Author name")
    parser.add_argument("--genre", type=str, 
                       help="Genre (thriller, romance, sci-fi, fantasy, mystery, horror, etc.)")
    
    # Design options
    parser.add_argument("--color-scheme", type=str,
                       help="Color scheme (dark, vibrant, pastel, monochrome, neon, etc.)")
    parser.add_argument("--mood", type=str,
                       help="Mood/atmosphere (mysterious, inspiring, dramatic, playful, dark, etc.)")
    parser.add_argument("--style", type=str,
                       help="Design style (minimalist, bold, elegant, vintage, modern, etc.)")
    parser.add_argument("--typography", type=str,
                       help="Typography style (bold, elegant, modern, classic, sans-serif, etc.)")
    parser.add_argument("--elements", type=str,
                       help="Additional design elements (geometric patterns, floral, illustrations, etc.)")
    
    # Generation options
    parser.add_argument("--width", type=int, default=768,
                       help="Image width (default: 768)")
    parser.add_argument("--height", type=int, default=1024,
                       help="Image height (default: 1024)")
    parser.add_argument("--steps", type=int, default=8,
                       help="Number of inference steps (default: 8)")
    parser.add_argument("--seed", type=int, default=-1,
                       help="Random seed (-1 for random, default: -1)")
    parser.add_argument("--output-dir", type=str, default="./book_covers",
                       help="Output directory (default: ./book_covers)")
    
    # LoRA path
    parser.add_argument("--lora-path", type=str, default=None,
                       help="Path to LoRA checkpoint (default: auto-detect step 500 checkpoint)")
    
    args = parser.parse_args()
    
    # Collect inputs
    if args.interactive:
        inputs = interactive_mode()
    else:
        if not args.title:
            print("Error: --title is required (or use --interactive)")
            parser.print_help()
            sys.exit(1)
        
        inputs = {
            "title": args.title,
            "author": args.author,
            "genre": args.genre,
            "color_scheme": args.color_scheme,
            "mood": args.mood,
            "style": args.style,
            "typography": args.typography,
            "elements": args.elements
        }
    
    # Find LoRA path
    lora_path = find_lora_path(args.lora_path)
    
    # Build prompt
    prompt = build_prompt(
        inputs["title"],
        inputs["author"],
        inputs["genre"],
        inputs["color_scheme"],
        inputs["mood"],
        inputs["style"],
        inputs["typography"],
        inputs["elements"]
    )
    
    print()
    print("=" * 60)
    print("Generation Settings")
    print("=" * 60)
    print(f"Prompt: {prompt}")
    print(f"Size: {args.width}x{args.height}")
    print(f"Steps: {args.steps}")
    print(f"Seed: {args.seed if args.seed != -1 else 'random'}")
    print(f"LoRA: {lora_path}")
    print(f"Output: {args.output_dir}")
    print("=" * 60)
    print()
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Create temporary config file
    config = create_generation_config(
        prompt,
        str(output_dir.absolute()),
        lora_path,
        args.width,
        args.height,
        args.steps,
        args.seed
    )
    
    # Save config to temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)
        config_path = f.name
    
    try:
        # Import and run generation
        print("Loading generation system...")
        from toolkit.job import get_job
        
        job = get_job(config_path)
        print("Starting generation...")
        job.run()
        
        print()
        print("=" * 60)
        print("✓ Generation complete!")
        print(f"✓ Book cover saved to: {output_dir}")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error during generation: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        # Clean up temp config
        if os.path.exists(config_path):
            os.unlink(config_path)

if __name__ == "__main__":
    main()

