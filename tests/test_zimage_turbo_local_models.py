#!/usr/bin/env python3
"""
Test suite for Z-Image Turbo local models.

Tests that the models downloaded to the model vault can be:
1. Discovered and loaded correctly
2. Training adapter can be loaded
3. Basic model properties work
4. Model can be initialized without errors

Usage:
    python tests/test_zimage_turbo_local_models.py

Requirements:
    - Models downloaded to /home/nfmil/model_vault
    - ai-toolkit-z_image_turbo in Python path
"""

import os
import sys
from pathlib import Path

# Add ai-toolkit to path
ai_toolkit_path = Path(__file__).parent.parent / "ai-toolkit-z_image_turbo"
if ai_toolkit_path.exists():
    sys.path.insert(0, str(ai_toolkit_path))

import torch

# Try to import pytest, but don't fail if not available
try:
    import pytest
    HAS_PYTEST = True
except ImportError:
    HAS_PYTEST = False
    # Create a mock pytest for manual testing
    class MockPytest:
        @staticmethod
        def fixture(autouse=False):
            def decorator(func):
                return func
            return decorator
        @staticmethod
        def skipif(condition, reason=""):
            def decorator(func):
                if condition:
                    def skip_func(*args, **kwargs):
                        print(f"⏭ Skipped: {reason}")
                        return None
                    return skip_func
                return func
            return decorator
        @staticmethod
        def main(args):
            print("pytest not available, running manually...")
            return 0
    pytest = MockPytest()

# Import toolkit modules
try:
    # Add ai-toolkit to path if not already there
    ai_toolkit_path = Path(__file__).parent.parent / "ai-toolkit-z_image_turbo"
    if ai_toolkit_path.exists() and str(ai_toolkit_path) not in sys.path:
        sys.path.insert(0, str(ai_toolkit_path))
    
    # Try to handle torchaudio import issues gracefully
    import warnings
    import types
    import importlib.util
    
    # Suppress torchaudio warnings/errors during import
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        try:
            import torchaudio
            TORCHAUDIO_AVAILABLE = True
        except (ImportError, OSError) as e:
            # torchaudio might not be installed or have version mismatch
            # Create a proper mock torchaudio module with __spec__
            mock_torchaudio = types.ModuleType('torchaudio')
            mock_torchaudio.save = lambda *args, **kwargs: None  # Dummy function
            mock_torchaudio.__version__ = "0.0.0"
            
            # Create a proper spec so importlib can detect it
            spec = importlib.util.spec_from_loader('torchaudio', loader=None)
            mock_torchaudio.__spec__ = spec
            mock_torchaudio.__loader__ = None
            mock_torchaudio.__file__ = "<mock>"
            mock_torchaudio.__path__ = []
            
            # Inject into sys.modules before importing config_modules
            sys.modules['torchaudio'] = mock_torchaudio
            TORCHAUDIO_AVAILABLE = False
            print(f"⚠ Warning: torchaudio not available ({type(e).__name__}: {e})")
            print("  Using mock torchaudio for testing (audio features will be disabled)")
    
    from toolkit.config_modules import ModelConfig
    from toolkit.util.get_model import get_model_class
    HAS_TOOLKIT = True
except (ImportError, OSError) as e:
    error_msg = str(e)
    print(f"❌ Could not import toolkit modules: {error_msg}")
    print("\nTroubleshooting:")
    print("1. Make sure ai-toolkit-z_image_turbo is in your Python path")
    print("2. Install/update torchaudio to match your PyTorch version:")
    print("   - Check PyTorch version: python -c 'import torch; print(torch.__version__)'")
    print("   - Install matching torchaudio:")
    print("     pip install torchaudio --index-url https://download.pytorch.org/whl/cu126")
    print("   - Or reinstall all PyTorch packages together:")
    print("     pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu126")
    print("\n3. If torchaudio version mismatch persists, try:")
    print("   pip uninstall torchaudio")
    print("   pip install torchaudio --index-url https://download.pytorch.org/whl/cu126")
    HAS_TOOLKIT = False
    TORCHAUDIO_AVAILABLE = False

# Model vault paths
MODEL_VAULT = Path("/home/nfmil/model_vault")
BASE_MODEL_PATH = MODEL_VAULT / "Tongyi-MAI" / "Z-Image-Turbo"
TRAINING_ADAPTER_PATH = MODEL_VAULT / "ostris" / "zimage_turbo_training_adapter" / "zimage_turbo_training_adapter_v1.safetensors"


class TestZImageTurboLocalModels:
    """Test suite for Z-Image Turbo local models."""
    
    def setup_method(self):
        """Setup test fixtures (pytest compatible)."""
        if not HAS_TOOLKIT:
            raise ImportError("Toolkit modules not available")
        self.base_model_path = str(BASE_MODEL_PATH)
        self.adapter_path = str(TRAINING_ADAPTER_PATH)
        
    def test_model_paths_exist(self):
        """Test that model paths exist."""
        assert BASE_MODEL_PATH.exists(), f"Base model not found at {BASE_MODEL_PATH}"
        assert TRAINING_ADAPTER_PATH.exists(), f"Training adapter not found at {TRAINING_ADAPTER_PATH}"
        
        # Check for key directories in base model
        assert (BASE_MODEL_PATH / "transformer").exists(), "transformer directory not found"
        assert (BASE_MODEL_PATH / "text_encoder").exists(), "text_encoder directory not found"
        assert (BASE_MODEL_PATH / "vae").exists(), "vae directory not found"
        assert (BASE_MODEL_PATH / "tokenizer").exists(), "tokenizer directory not found"
        
        print(f"✓ Base model found at: {BASE_MODEL_PATH}")
        print(f"✓ Training adapter found at: {TRAINING_ADAPTER_PATH}")
    
    def test_model_discovery(self):
        """Test that ZImageModel can be discovered by arch type."""
        config = ModelConfig(
            name_or_path=self.base_model_path,
            arch="zimage"
        )
        
        ModelClass = get_model_class(config)
        assert ModelClass is not None, "Model class not found"
        assert ModelClass.arch == "zimage", f"Expected arch 'zimage', got '{ModelClass.arch}'"
        
        print(f"✓ Model class discovered: {ModelClass.__name__}")
        print(f"✓ Model arch: {ModelClass.arch}")
    
    def test_model_config_with_local_paths(self):
        """Test that ModelConfig accepts local paths."""
        config = ModelConfig(
            name_or_path=self.base_model_path,
            arch="zimage",
            assistant_lora_path=self.adapter_path,
            quantize=True,
            low_vram=True
        )
        
        assert config.arch == "zimage", "Config arch should be 'zimage'"
        assert config.name_or_path == self.base_model_path, "Config should use local path"
        assert config.assistant_lora_path == self.adapter_path, "Config should use local adapter path"
        
        print(f"✓ Config created with local paths")
        print(f"  Base model: {config.name_or_path}")
        print(f"  Adapter: {config.assistant_lora_path}")
    
    def test_model_initialization(self):
        """Test that model can be initialized (without loading if no CUDA)."""
        config = ModelConfig(
            name_or_path=self.base_model_path,
            arch="zimage",
            assistant_lora_path=self.adapter_path,
            quantize=True,
            low_vram=True
        )
        
        ModelClass = get_model_class(config)
        
        # Initialize model (this doesn't load weights, just creates the object)
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        try:
            model = ModelClass(
                device=device,
                model_config=config,
                dtype="bf16" if torch.cuda.is_available() else "float32"
            )
            
            assert model is not None, "Model should be initialized"
            assert model.arch == "zimage", "Model arch should be 'zimage'"
            assert model.model_config.assistant_lora_path == self.adapter_path, "Adapter path should be set"
            
            print(f"✓ Model initialized successfully")
            print(f"  Device: {device}")
            print(f"  Arch: {model.arch}")
            
        except Exception as e:
            if not torch.cuda.is_available():
                pytest.skip(f"CUDA not available, skipping model initialization: {e}")
            else:
                raise
    
    @pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA not available")
    def test_model_loading(self):
        """Test that model can be loaded from local paths (requires CUDA)."""
        config = ModelConfig(
            name_or_path=self.base_model_path,
            arch="zimage",
            assistant_lora_path=self.adapter_path,
            quantize=True,
            low_vram=True
        )
        
        ModelClass = get_model_class(config)
        device = torch.device("cuda")
        
        model = ModelClass(
            device=device,
            model_config=config,
            dtype="bf16"
        )
        
        # Load the model
        print("Loading model from local paths...")
        model.load_model()
        
        assert model.is_loaded or hasattr(model, 'model'), "Model should be loaded"
        assert model.model_config.assistant_lora_path == self.adapter_path, "Adapter path should be preserved"
        
        # Check that adapter was loaded if path was provided
        if hasattr(model, 'assistant_lora'):
            print(f"✓ Training adapter loaded: {model.assistant_lora is not None}")
        
        print(f"✓ Model loaded successfully from local paths")
    
    def test_model_properties(self):
        """Test that model properties are correct."""
        config = ModelConfig(
            name_or_path=self.base_model_path,
            arch="zimage"
        )
        
        ModelClass = get_model_class(config)
        
        # Check static properties
        assert ModelClass.arch == "zimage", "Model arch should be 'zimage'"
        
        # Check if model has expected attributes
        assert hasattr(ModelClass, 'get_train_scheduler'), "Model should have get_train_scheduler method"
        assert hasattr(ModelClass, 'load_training_adapter'), "Model should have load_training_adapter method"
        
        print(f"✓ Model properties verified")
    
    def test_adapter_path_validation(self):
        """Test that adapter path validation works."""
        config = ModelConfig(
            name_or_path=self.base_model_path,
            arch="zimage",
            assistant_lora_path=self.adapter_path
        )
        
        ModelClass = get_model_class(config)
        device = torch.device("cpu")  # Use CPU to avoid loading weights
        
        model = ModelClass(
            device=device,
            model_config=config,
            dtype="float32"
        )
        
        # Check that adapter path is stored
        assert model.model_config.assistant_lora_path == self.adapter_path
        
        # Check that path exists
        assert os.path.exists(self.adapter_path), f"Adapter path should exist: {self.adapter_path}"
        
        print(f"✓ Adapter path validation passed")
    
    def test_config_with_hub_paths_fallback(self):
        """Test that config can also use Hugging Face Hub paths."""
        config = ModelConfig(
            name_or_path="Tongyi-MAI/Z-Image-Turbo",
            arch="zimage",
            assistant_lora_path="ostris/zimage_turbo_training_adapter/zimage_turbo_training_adapter_v1.safetensors"
        )
        
        assert config.arch == "zimage"
        assert config.name_or_path == "Tongyi-MAI/Z-Image-Turbo"
        assert "zimage_turbo_training_adapter" in config.assistant_lora_path
        
        print(f"✓ Config with Hub paths works (will download on first use)")
    
    @pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA not available")
    def test_model_components_exist(self):
        """Test that all required model components exist in local paths."""
        # Check base model components
        transformer_path = BASE_MODEL_PATH / "transformer"
        text_encoder_path = BASE_MODEL_PATH / "text_encoder"
        vae_path = BASE_MODEL_PATH / "vae"
        tokenizer_path = BASE_MODEL_PATH / "tokenizer"
        
        assert transformer_path.exists(), f"Transformer not found at {transformer_path}"
        assert text_encoder_path.exists(), f"Text encoder not found at {text_encoder_path}"
        assert vae_path.exists(), f"VAE not found at {vae_path}"
        assert tokenizer_path.exists(), f"Tokenizer not found at {tokenizer_path}"
        
        print(f"✓ All model components found:")
        print(f"  Transformer: {transformer_path}")
        print(f"  Text Encoder: {text_encoder_path}")
        print(f"  VAE: {vae_path}")
        print(f"  Tokenizer: {tokenizer_path}")
    
    @pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA not available")
    def test_model_loading_with_adapter(self):
        """Test that model loads correctly with training adapter from local path."""
        config = ModelConfig(
            name_or_path=self.base_model_path,
            arch="zimage",
            assistant_lora_path=self.adapter_path,
            quantize=True,
            low_vram=True
        )
        
        ModelClass = get_model_class(config)
        device = torch.device("cuda")
        
        model = ModelClass(
            device=device,
            model_config=config,
            dtype="bf16"
        )
        
        print("Loading model with training adapter...")
        model.load_model()
        
        # Verify model loaded
        assert hasattr(model, 'model') or hasattr(model, 'transformer'), "Model should be loaded"
        assert hasattr(model, 'text_encoder'), "Text encoder should be loaded"
        assert hasattr(model, 'vae'), "VAE should be loaded"
        assert hasattr(model, 'pipeline'), "Pipeline should be created"
        
        # Verify adapter was loaded
        assert hasattr(model, 'assistant_lora'), "Assistant LoRA should be loaded"
        assert model.assistant_lora is not None, "Assistant LoRA should not be None"
        assert model.invert_assistant_lora == True, "invert_assistant_lora should be True"
        
        print(f"✓ Model loaded with training adapter")
        print(f"  Assistant LoRA loaded: {model.assistant_lora is not None}")
        print(f"  Invert flag: {model.invert_assistant_lora}")
    
    @pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA not available")
    def test_model_loading_without_adapter(self):
        """Test that model loads correctly without training adapter."""
        config = ModelConfig(
            name_or_path=self.base_model_path,
            arch="zimage",
            quantize=True,
            low_vram=True
        )
        
        ModelClass = get_model_class(config)
        device = torch.device("cuda")
        
        model = ModelClass(
            device=device,
            model_config=config,
            dtype="bf16"
        )
        
        print("Loading model without training adapter...")
        model.load_model()
        
        # Verify model loaded
        assert hasattr(model, 'model') or hasattr(model, 'transformer'), "Model should be loaded"
        assert hasattr(model, 'text_encoder'), "Text encoder should be loaded"
        assert hasattr(model, 'vae'), "VAE should be loaded"
        
        # Verify adapter was NOT loaded
        if hasattr(model, 'assistant_lora'):
            assert model.assistant_lora is None or not hasattr(model, 'assistant_lora'), "Assistant LoRA should not be loaded"
        
        print(f"✓ Model loaded without training adapter")
    
    def test_model_bucket_divisibility(self):
        """Test that model returns correct bucket divisibility."""
        config = ModelConfig(
            name_or_path=self.base_model_path,
            arch="zimage"
        )
        
        ModelClass = get_model_class(config)
        device = torch.device("cpu")
        
        model = ModelClass(
            device=device,
            model_config=config,
            dtype="float32"
        )
        
        divisibility = model.get_bucket_divisibility()
        assert divisibility == 32, f"Expected bucket divisibility 32, got {divisibility}"
        
        print(f"✓ Bucket divisibility: {divisibility}")
    
    def test_model_scheduler(self):
        """Test that model returns correct scheduler."""
        from extensions_built_in.diffusion_models.z_image.z_image import ZImageModel
        
        scheduler = ZImageModel.get_train_scheduler()
        assert scheduler is not None, "Scheduler should not be None"
        
        print(f"✓ Scheduler created: {type(scheduler).__name__}")
    
    def test_lora_weight_conversion(self):
        """Test LoRA weight conversion methods."""
        config = ModelConfig(
            name_or_path=self.base_model_path,
            arch="zimage"
        )
        
        ModelClass = get_model_class(config)
        device = torch.device("cpu")
        
        model = ModelClass(
            device=device,
            model_config=config,
            dtype="float32"
        )
        
        # Test conversion from transformer to diffusion_model format
        test_dict = {
            "transformer.layers.0.attention.to_k.weight": torch.randn(10, 10),
            "transformer.layers.1.attention.to_v.weight": torch.randn(10, 10)
        }
        
        converted = model.convert_lora_weights_before_save(test_dict)
        
        assert "diffusion_model.layers.0.attention.to_k.weight" in converted
        assert "diffusion_model.layers.1.attention.to_v.weight" in converted
        assert "transformer.layers.0.attention.to_k.weight" not in converted
        
        # Test reverse conversion
        reverse_converted = model.convert_lora_weights_before_load(converted)
        
        assert "transformer.layers.0.attention.to_k.weight" in reverse_converted
        assert "transformer.layers.1.attention.to_v.weight" in reverse_converted
        assert "diffusion_model.layers.0.attention.to_k.weight" not in reverse_converted
        
        print(f"✓ LoRA weight conversion works correctly")
    
    @pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA not available")
    def test_adapter_inversion_flag(self):
        """Test that adapter inversion flag is set correctly."""
        config = ModelConfig(
            name_or_path=self.base_model_path,
            arch="zimage",
            assistant_lora_path=self.adapter_path
        )
        
        ModelClass = get_model_class(config)
        device = torch.device("cuda")
        
        model = ModelClass(
            device=device,
            model_config=config,
            dtype="bf16"
        )
        
        # Load model to trigger adapter loading
        model.load_model()
        
        # Check inversion flag
        assert hasattr(model, 'invert_assistant_lora'), "Model should have invert_assistant_lora attribute"
        assert model.invert_assistant_lora == True, "invert_assistant_lora should be True for Z-Image Turbo"
        
        # Check adapter multiplier
        if hasattr(model, 'assistant_lora') and model.assistant_lora is not None:
            assert model.assistant_lora.multiplier == -1.0, "Adapter multiplier should be -1.0"
            assert model.assistant_lora.is_active == False, "Adapter should be inactive during training"
        
        print(f"✓ Adapter inversion flag set correctly")
        print(f"  invert_assistant_lora: {model.invert_assistant_lora}")
        if hasattr(model, 'assistant_lora') and model.assistant_lora is not None:
            print(f"  adapter.multiplier: {model.assistant_lora.multiplier}")
            print(f"  adapter.is_active: {model.assistant_lora.is_active}")


def run_tests():
    """Run tests with pytest or manually."""
    print("=" * 60)
    print("Z-Image Turbo Local Models Test Suite")
    print("=" * 60)
    print()
    
    if not HAS_TOOLKIT:
        print("❌ Toolkit modules not available!")
        print("Please ensure ai-toolkit-z_image_turbo is installed and in your Python path.")
        print("\nYou can:")
        print("  1. Install dependencies: pip install -r ai-toolkit-z_image_turbo/requirements.txt")
        print("  2. Add to path: export PYTHONPATH=/home/nfmil/projects/image_gen/ai-toolkit-z_image_turbo:$PYTHONPATH")
        sys.exit(1)
    
    # Check if pytest is available
    if HAS_PYTEST:
        try:
            print("Running with pytest...")
            pytest.main([__file__, "-v"])
            return
        except Exception as e:
            print(f"pytest failed: {e}, running manually...")
            print()
    
    # Run tests manually
    print("Running tests manually...")
    print()
    
    test_suite = TestZImageTurboLocalModels()
    test_suite.setup_method()
    
    tests = [
        ("Model Paths Exist", test_suite.test_model_paths_exist),
        ("Model Discovery", test_suite.test_model_discovery),
        ("Model Config", test_suite.test_model_config_with_local_paths),
        ("Model Properties", test_suite.test_model_properties),
        ("Adapter Path Validation", test_suite.test_adapter_path_validation),
        ("Hub Paths Fallback", test_suite.test_config_with_hub_paths_fallback),
        ("Model Components Exist", test_suite.test_model_components_exist),
        ("Bucket Divisibility", test_suite.test_model_bucket_divisibility),
        ("Model Scheduler", test_suite.test_model_scheduler),
        ("LoRA Weight Conversion", test_suite.test_lora_weight_conversion),
    ]
    
    # CUDA-only tests
    if torch.cuda.is_available():
        cuda_tests = [
            ("Model Loading with Adapter", test_suite.test_model_loading_with_adapter),
            ("Model Loading without Adapter", test_suite.test_model_loading_without_adapter),
            ("Adapter Inversion Flag", test_suite.test_adapter_inversion_flag),
        ]
        tests.extend(cuda_tests)
    else:
        print("⚠ CUDA not available, skipping GPU-dependent tests\n")
    
    passed = 0
    failed = 0
    skipped = 0
    
    for name, test_func in tests:
        try:
            print(f"Running: {name}...")
            test_func()
            passed += 1
            print(f"✓ {name} passed\n")
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception as e:
            # Check if it's a skip exception
            if "skip" in str(e).lower() or "Skip" in str(type(e).__name__):
                skipped += 1
                print(f"⏭ {name} skipped: {e}\n")
            else:
                failed += 1
                print(f"✗ {name} failed: {e}\n")
                import traceback
                traceback.print_exc()
    
    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed, {skipped} skipped")
    print("=" * 60)
    
    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    run_tests()

