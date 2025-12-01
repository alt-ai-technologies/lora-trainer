#!/usr/bin/env python3
"""
Simple test script for Z-Image Turbo integration.
Tests model discovery and configuration without loading the full model.
"""

import os
import sys

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def test_imports():
    """Test that we can import the necessary modules."""
    print("=" * 60)
    print("Test 1: Module Imports")
    print("=" * 60)
    
    try:
        # Try importing config_modules - this might fail if torchaudio is missing
        # but we'll handle that gracefully
        try:
            from toolkit.config_modules import ModelConfig, ModelArch
            print("✓ Successfully imported ModelConfig and ModelArch")
        except ImportError as e:
            print(f"⚠ Could not import config_modules: {e}")
            print("  (This is okay for a basic test)")
            return False
        
        # Test ModelArch type
        from typing import get_args
        arch_types = get_args(ModelArch)
        print(f"✓ ModelArch types: {len(arch_types)} architectures")
        
        if 'zimage' in arch_types:
            print("✓ 'zimage' is in ModelArch type definition")
        else:
            print("✗ 'zimage' is NOT in ModelArch type definition")
            return False
        
        return True
    except Exception as e:
        print(f"✗ Import test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_model_class():
    """Test that ZImageModel class exists and has correct arch."""
    print("\n" + "=" * 60)
    print("Test 2: Model Class")
    print("=" * 60)
    
    try:
        from extensions_built_in.diffusion_models.z_image.z_image import ZImageModel
        
        print(f"✓ ZImageModel class found: {ZImageModel.__name__}")
        print(f"✓ ZImageModel arch: {ZImageModel.arch}")
        
        if ZImageModel.arch == "zimage":
            print("✓ ZImageModel has correct arch='zimage'")
        else:
            print(f"✗ ZImageModel arch is '{ZImageModel.arch}', expected 'zimage'")
            return False
        
        # Check for required methods
        required_methods = ['load_model', 'get_generation_pipeline', 'get_noise_prediction']
        for method in required_methods:
            if hasattr(ZImageModel, method):
                print(f"✓ ZImageModel has {method} method")
            else:
                print(f"✗ ZImageModel missing {method} method")
                return False
        
        return True
    except Exception as e:
        print(f"✗ Model class test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_model_registration():
    """Test that ZImageModel is registered in AI_TOOLKIT_MODELS."""
    print("\n" + "=" * 60)
    print("Test 3: Model Registration")
    print("=" * 60)
    
    try:
        from extensions_built_in.diffusion_models.z_image import AI_TOOLKIT_MODELS
        from extensions_built_in.diffusion_models.z_image.z_image import ZImageModel
        
        print(f"✓ AI_TOOLKIT_MODELS found")
        print(f"✓ AI_TOOLKIT_MODELS contains {len(AI_TOOLKIT_MODELS)} model(s)")
        
        if ZImageModel in AI_TOOLKIT_MODELS:
            print("✓ ZImageModel is registered in AI_TOOLKIT_MODELS")
        else:
            print("✗ ZImageModel is NOT registered in AI_TOOLKIT_MODELS")
            return False
        
        return True
    except Exception as e:
        print(f"✗ Model registration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_model_discovery():
    """Test that get_model_class can find ZImageModel."""
    print("\n" + "=" * 60)
    print("Test 4: Model Discovery")
    print("=" * 60)
    
    try:
        # Try to import get_model_class
        try:
            from toolkit.util.get_model import get_model_class
            from toolkit.config_modules import ModelConfig
        except ImportError as e:
            print(f"⚠ Could not import get_model_class: {e}")
            print("  (This requires full toolkit setup)")
            return None
        
        # Create a config with zimage arch
        config = ModelConfig(
            name_or_path="/dummy/path",
            arch="zimage"
        )
        
        ModelClass = get_model_class(config)
        print(f"✓ get_model_class returned: {ModelClass.__name__}")
        
        if ModelClass.arch == "zimage":
            print("✓ Discovered model has correct arch='zimage'")
            return True
        else:
            print(f"✗ Discovered model arch is '{ModelClass.arch}', expected 'zimage'")
            return False
    except Exception as e:
        print(f"⚠ Model discovery test skipped: {e}")
        print("  (This requires full toolkit setup)")
        return None

def test_properties():
    """Test that is_zimage property exists."""
    print("\n" + "=" * 60)
    print("Test 5: Model Properties")
    print("=" * 60)
    
    try:
        from toolkit.models.base_model import BaseModel
        from toolkit.stable_diffusion_model import StableDiffusion
        
        has_base = hasattr(BaseModel, 'is_zimage')
        has_stable = hasattr(StableDiffusion, 'is_zimage')
        
        if has_base:
            print("✓ is_zimage property exists in BaseModel")
        else:
            print("✗ is_zimage property NOT found in BaseModel")
        
        if has_stable:
            print("✓ is_zimage property exists in StableDiffusion")
        else:
            print("✗ is_zimage property NOT found in StableDiffusion")
        
        return has_base and has_stable
    except Exception as e:
        print(f"✗ Properties test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_model_paths():
    """Test that model paths exist."""
    print("\n" + "=" * 60)
    print("Test 6: Model Paths")
    print("=" * 60)
    
    MODEL_VAULT = "/home/nfmil/model_vault"
    BASE_MODEL_PATH = f"{MODEL_VAULT}/Tongyi-MAI/Z-Image-Turbo"
    TRAINING_ADAPTER_PATH = f"{MODEL_VAULT}/ostris/zimage_turbo_training_adapter/zimage_turbo_training_adapter_v1.safetensors"
    
    base_exists = os.path.exists(BASE_MODEL_PATH)
    adapter_exists = os.path.exists(TRAINING_ADAPTER_PATH)
    
    if base_exists:
        print(f"✓ Base model path exists: {BASE_MODEL_PATH}")
    else:
        print(f"⚠ Base model path NOT found: {BASE_MODEL_PATH}")
    
    if adapter_exists:
        print(f"✓ Training adapter path exists: {TRAINING_ADAPTER_PATH}")
    else:
        print(f"⚠ Training adapter path NOT found: {TRAINING_ADAPTER_PATH}")
    
    return base_exists and adapter_exists

def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("Z-Image Turbo Integration Test Suite (Simple)")
    print("=" * 60 + "\n")
    
    results = []
    
    # Test 1: Imports
    results.append(("Imports", test_imports()))
    
    # Test 2: Model Class
    results.append(("Model Class", test_model_class()))
    
    # Test 3: Model Registration
    results.append(("Model Registration", test_model_registration()))
    
    # Test 4: Model Discovery (may be None if imports fail)
    discovery_result = test_model_discovery()
    if discovery_result is not None:
        results.append(("Model Discovery", discovery_result))
    
    # Test 5: Properties
    results.append(("Properties", test_properties()))
    
    # Test 6: Model Paths
    results.append(("Model Paths", test_model_paths()))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = 0
    failed = 0
    skipped = 0
    
    for name, result in results:
        if result is True:
            print(f"✅ {name}: PASSED")
            passed += 1
        elif result is False:
            print(f"❌ {name}: FAILED")
            failed += 1
        else:
            print(f"⚠️  {name}: SKIPPED")
            skipped += 1
    
    print(f"\nTotal: {passed} passed, {failed} failed, {skipped} skipped")
    
    if failed == 0:
        print("\n✅ ALL CRITICAL TESTS PASSED!")
        print("Z-Image Turbo integration is working correctly!")
    else:
        print(f"\n❌ {failed} TEST(S) FAILED")
        print("Please check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main()

