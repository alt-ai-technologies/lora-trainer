#!/usr/bin/env python3
"""
Quick test script to validate image generation setup.
Run this before attempting to generate images.
"""

import sys
import os
from pathlib import Path

def test_config_files():
    """Test that config files are valid YAML and have correct structure."""
    print("=" * 60)
    print("Testing Config Files")
    print("=" * 60)
    
    try:
        import yaml
    except ImportError:
        print("❌ yaml module not found. Install: pip install pyyaml")
        return False
    
    config_dir = Path(__file__).parent / "ai-toolkit-z_image_turbo" / "config"
    configs = [
        "generate_zimage_simple.yaml",
        "generate_zimage.yaml"
    ]
    
    all_valid = True
    for config_name in configs:
        config_path = config_dir / config_name
        if not config_path.exists():
            print(f"❌ {config_name}: File not found")
            all_valid = False
            continue
            
        try:
            with open(config_path) as f:
                config = yaml.safe_load(f)
            
            # Validate structure
            if "job" not in config:
                print(f"❌ {config_name}: Missing 'job' field")
                all_valid = False
                continue
                
            if config["job"] != "generate":
                print(f"❌ {config_name}: Job type should be 'generate', got '{config['job']}'")
                all_valid = False
                continue
                
            if "config" not in config:
                print(f"❌ {config_name}: Missing 'config' field")
                all_valid = False
                continue
                
            model_config = config["config"]["process"][0].get("model", {})
            if model_config.get("arch") != "zimage":
                print(f"❌ {config_name}: Model arch should be 'zimage'")
                all_valid = False
                continue
                
            print(f"✅ {config_name}: Valid")
            
        except yaml.YAMLError as e:
            print(f"❌ {config_name}: YAML syntax error: {e}")
            all_valid = False
        except Exception as e:
            print(f"❌ {config_name}: Error: {e}")
            all_valid = False
    
    return all_valid


def test_environment():
    """Test Python environment and dependencies."""
    print("\n" + "=" * 60)
    print("Testing Environment")
    print("=" * 60)
    
    # Test PyTorch
    try:
        import torch
        print(f"✅ PyTorch: {torch.__version__}")
        if torch.cuda.is_available():
            print(f"✅ CUDA: Available")
            print(f"✅ GPU: {torch.cuda.get_device_name(0)}")
        else:
            print("⚠️  CUDA: Not available (will use CPU - slow)")
    except ImportError:
        print("❌ PyTorch: Not installed")
        return False
    
    # Test AI Toolkit imports
    ai_toolkit_path = Path(__file__).parent / "ai-toolkit-z_image_turbo"
    if ai_toolkit_path.exists():
        sys.path.insert(0, str(ai_toolkit_path))
        try:
            from toolkit.job import get_job
            print("✅ AI Toolkit: Can import get_job")
        except ImportError as e:
            print(f"⚠️  AI Toolkit: Import error (dependencies may not be installed): {e}")
            print("   Install with: cd ai-toolkit-z_image_turbo && pip install -r requirements.txt")
    else:
        print("❌ AI Toolkit: Directory not found")
        return False
    
    return True


def test_paths():
    """Test that required paths exist."""
    print("\n" + "=" * 60)
    print("Testing Paths")
    print("=" * 60)
    
    # Model vault
    model_vault = Path("/home/nfmil/model_vault/Tongyi-MAI/Z-Image-Turbo")
    if model_vault.exists():
        print(f"✅ Model Vault: {model_vault}")
    else:
        print(f"⚠️  Model Vault: Not found at {model_vault}")
        print("   Will download from Hugging Face Hub if using Hub path")
    
    # Output directory
    output_dir = Path(__file__).parent / "ai-toolkit-z_image_turbo" / "output" / "gen"
    output_dir.mkdir(parents=True, exist_ok=True)
    if output_dir.exists():
        print(f"✅ Output Directory: {output_dir}")
    else:
        print(f"❌ Output Directory: Cannot create {output_dir}")
        return False
    
    # run.py
    run_py = Path(__file__).parent / "ai-toolkit-z_image_turbo" / "run.py"
    if run_py.exists():
        print(f"✅ run.py: {run_py}")
    else:
        print(f"❌ run.py: Not found")
        return False
    
    return True


def test_huggingface():
    """Test Hugging Face setup."""
    print("\n" + "=" * 60)
    print("Testing Hugging Face")
    print("=" * 60)
    
    import subprocess
    try:
        result = subprocess.run(
            ["huggingface-cli", "whoami"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            print(f"✅ Hugging Face: Logged in as {result.stdout.strip()}")
        else:
            print("⚠️  Hugging Face: Not logged in")
            print("   Login with: huggingface-cli login")
            print("   (Only needed if using Hub model path)")
    except FileNotFoundError:
        print("⚠️  Hugging Face CLI: Not found")
        print("   Install with: pip install huggingface_hub")
        print("   (Only needed if using Hub model path)")
    except Exception as e:
        print(f"⚠️  Hugging Face: {e}")
    
    return True  # Not critical


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("Image Generation Setup Test")
    print("=" * 60 + "\n")
    
    results = []
    results.append(("Config Files", test_config_files()))
    results.append(("Environment", test_environment()))
    results.append(("Paths", test_paths()))
    results.append(("Hugging Face", test_huggingface()))
    
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    
    all_passed = True
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{name}: {status}")
        if not passed and name != "Hugging Face":  # HF is optional
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ All critical tests passed! Ready to generate images.")
        print("\nTo generate images, run:")
        print("  cd ai-toolkit-z_image_turbo")
        print("  python run.py config/generate_zimage_simple.yaml")
    else:
        print("⚠️  Some tests failed. Please fix issues above.")
        print("\nCommon fixes:")
        print("  1. Install dependencies: cd ai-toolkit-z_image_turbo && pip install -r requirements.txt")
        print("  2. Activate virtual environment: source .venv/bin/activate")
        print("  3. Login to Hugging Face: huggingface-cli login (if using Hub path)")
    print("=" * 60 + "\n")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())

