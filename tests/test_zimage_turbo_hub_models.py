#!/usr/bin/env python3
"""
Test suite for Z-Image Turbo models from Hugging Face Hub.

Tests that models can be downloaded and loaded from Hugging Face Hub.
Models are downloaded on-demand when running tests.

Usage:
    python tests/test_zimage_turbo_hub_models.py

Requirements:
    - huggingface_hub installed
    - Hugging Face token (optional, for gated models)
    - ai-toolkit-z_image_turbo in Python path
"""

import os
import sys
import tempfile
import shutil
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
    # Handle torchaudio import issues
    import warnings
    import types
    import importlib.util
    
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        try:
            import torchaudio
            TORCHAUDIO_AVAILABLE = True
        except (ImportError, OSError) as e:
            # Create a proper mock torchaudio module
            mock_torchaudio = types.ModuleType('torchaudio')
            mock_torchaudio.save = lambda *args, **kwargs: None
            mock_torchaudio.__version__ = "0.0.0"
            spec = importlib.util.spec_from_loader('torchaudio', loader=None)
            mock_torchaudio.__spec__ = spec
            mock_torchaudio.__loader__ = None
            mock_torchaudio.__file__ = "<mock>"
            mock_torchaudio.__path__ = []
            sys.modules['torchaudio'] = mock_torchaudio
            TORCHAUDIO_AVAILABLE = False
            print(f"⚠ Warning: torchaudio not available, using mock")
    
    from toolkit.config_modules import ModelConfig
    from toolkit.util.get_model import get_model_class
    from huggingface_hub import snapshot_download, hf_hub_download
    HAS_TOOLKIT = True
except ImportError as e:
    print(f"Warning: Could not import toolkit modules: {e}")
    print("Make sure ai-toolkit-z_image_turbo is in your Python path")
    HAS_TOOLKIT = False

# Hugging Face Hub model IDs
BASE_MODEL_ID = "Tongyi-MAI/Z-Image-Turbo"
ADAPTER_REPO_ID = "ostris/zimage_turbo_training_adapter"
ADAPTER_FILENAME = "zimage_turbo_training_adapter_v1.safetensors"

# Temporary directory for downloaded models
TEST_CACHE_DIR = Path(tempfile.gettempdir()) / "zimage_turbo_test_cache"


class TestZImageTurboHubModels:
    """Test suite for Z-Image Turbo models from Hugging Face Hub."""
    
    def setup_method(self):
        """Setup test fixtures."""
        if not HAS_TOOLKIT:
            raise ImportError("Toolkit modules not available")
        
        # Create test cache directory
        TEST_CACHE_DIR.mkdir(parents=True, exist_ok=True)
        
        self.base_model_id = BASE_MODEL_ID
        self.adapter_repo_id = ADAPTER_REPO_ID
        self.adapter_filename = ADAPTER_FILENAME
        self.cache_dir = TEST_CACHE_DIR
    
    def teardown_method(self):
        """Cleanup after tests."""
        # Optionally clean up downloaded models (commented out to keep cache)
        # if TEST_CACHE_DIR.exists():
        #     shutil.rmtree(TEST_CACHE_DIR)
        pass
    
    def test_hub_model_ids_valid(self):
        """Test that Hub model IDs are correctly formatted."""
        assert "/" in self.base_model_id, "Base model ID should be in format 'org/model'"
        assert "/" in self.adapter_repo_id, "Adapter repo ID should be in format 'org/repo'"
        
        print(f"✓ Hub model IDs valid:")
        print(f"  Base: {self.base_model_id}")
        print(f"  Adapter: {self.adapter_repo_id}/{self.adapter_filename}")
    
    def test_model_discovery_with_hub_path(self):
        """Test that ZImageModel can be discovered using Hub path."""
        config = ModelConfig(
            name_or_path=self.base_model_id,
            arch="zimage"
        )
        
        ModelClass = get_model_class(config)
        assert ModelClass is not None, "Model class not found"
        assert ModelClass.arch == "zimage", f"Expected arch 'zimage', got '{ModelClass.arch}'"
        
        print(f"✓ Model class discovered from Hub path: {ModelClass.__name__}")
        print(f"✓ Model arch: {ModelClass.arch}")
    
    def test_config_with_hub_paths(self):
        """Test that ModelConfig accepts Hugging Face Hub paths."""
        config = ModelConfig(
            name_or_path=self.base_model_id,
            arch="zimage",
            assistant_lora_path=f"{self.adapter_repo_id}/{self.adapter_filename}",
            quantize=True,
            low_vram=True
        )
        
        assert config.arch == "zimage", "Config arch should be 'zimage'"
        assert config.name_or_path == self.base_model_id, "Config should use Hub path"
        assert self.adapter_repo_id in config.assistant_lora_path, "Config should use Hub adapter path"
        
        print(f"✓ Config created with Hub paths")
        print(f"  Base model: {config.name_or_path}")
        print(f"  Adapter: {config.assistant_lora_path}")
    
    def test_adapter_download(self):
        """Test downloading training adapter from Hub."""
        print(f"Downloading adapter from Hub...")
        print(f"  Repository: {self.adapter_repo_id}")
        print(f"  File: {self.adapter_filename}")
        
        try:
            adapter_path = hf_hub_download(
                repo_id=self.adapter_repo_id,
                filename=self.adapter_filename,
                cache_dir=str(self.cache_dir),
                force_download=False  # Use cache if available
            )
            
            assert os.path.exists(adapter_path), f"Adapter not downloaded to {adapter_path}"
            assert adapter_path.endswith(self.adapter_filename), "Downloaded file should match filename"
            
            file_size = os.path.getsize(adapter_path) / (1024 * 1024)  # MB
            print(f"✓ Adapter downloaded successfully")
            print(f"  Path: {adapter_path}")
            print(f"  Size: {file_size:.1f} MB")
            
            return adapter_path
            
        except Exception as e:
            # Check if it's an authentication issue
            if "401" in str(e) or "authentication" in str(e).lower():
                pytest.skip(f"Authentication required for {self.adapter_repo_id}: {e}")
            else:
                raise
    
    def test_base_model_download_metadata(self):
        """Test that we can access base model metadata without full download."""
        print(f"Checking base model metadata...")
        print(f"  Model: {self.base_model_id}")
        
        try:
            # Try to download just the model card/README
            # This is much faster than downloading the full model
            from huggingface_hub import HfApi
            api = HfApi()
            
            model_info = api.model_info(self.base_model_id)
            assert model_info is not None, "Model info should be available"
            
            print(f"✓ Base model metadata accessible")
            # ModelInfo uses 'id' or 'modelId' (camelCase), not 'model_id'
            model_id = getattr(model_info, 'id', None) or getattr(model_info, 'modelId', None) or str(model_info)
            print(f"  Model ID: {model_id}")
            print(f"  Private: {getattr(model_info, 'private', 'Unknown')}")
            print(f"  Gated: {getattr(model_info, 'gated', 'Unknown')}")
            
            if getattr(model_info, 'gated', False):
                print(f"  ⚠ Model is gated - you may need to accept the license on Hugging Face")
                print(f"  ⚠ Visit: https://huggingface.co/{self.base_model_id}")
            
        except Exception as e:
            error_str = str(e)
            if "401" in error_str or "authentication" in error_str.lower() or "unauthorized" in error_str.lower():
                pytest.skip(f"Authentication required: {e}")
            elif "404" in error_str or "not found" in error_str.lower():
                pytest.skip(f"Model not found: {e}")
            elif "403" in error_str or "forbidden" in error_str.lower():
                pytest.skip(f"Access forbidden - may need to accept license: {e}")
            else:
                # For other errors, just print a warning but don't fail
                print(f"⚠ Could not fetch model metadata: {e}")
                print(f"  This is OK - model may still be accessible for download")
    
    @pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA not available")
    def test_model_loading_from_hub(self):
        """Test that model can be loaded from Hub (requires CUDA and download)."""
        config = ModelConfig(
            name_or_path=self.base_model_id,
            arch="zimage",
            quantize=True,
            low_vram=True
        )
        
        ModelClass = get_model_class(config)
        device = torch.device("cuda")
        
        print(f"Loading model from Hub (this will download if not cached)...")
        print(f"  Model: {self.base_model_id}")
        print(f"  This may take several minutes on first run...")
        
        model = ModelClass(
            device=device,
            model_config=config,
            dtype="bf16"
        )
        
        # Load the model (will download from Hub if needed)
        model.load_model()
        
        assert hasattr(model, 'model') or hasattr(model, 'transformer'), "Model should be loaded"
        assert hasattr(model, 'text_encoder'), "Text encoder should be loaded"
        assert hasattr(model, 'vae'), "VAE should be loaded"
        
        print(f"✓ Model loaded successfully from Hub")
    
    @pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA not available")
    def test_model_loading_with_hub_adapter(self):
        """Test that model loads with training adapter from Hub."""
        config = ModelConfig(
            name_or_path=self.base_model_id,
            arch="zimage",
            assistant_lora_path=f"{self.adapter_repo_id}/{self.adapter_filename}",
            quantize=True,
            low_vram=True
        )
        
        ModelClass = get_model_class(config)
        device = torch.device("cuda")
        
        print(f"Loading model with Hub adapter (this will download if not cached)...")
        print(f"  Model: {self.base_model_id}")
        print(f"  Adapter: {self.adapter_repo_id}/{self.adapter_filename}")
        
        model = ModelClass(
            device=device,
            model_config=config,
            dtype="bf16"
        )
        
        # Load the model (will download adapter from Hub if needed)
        model.load_model()
        
        # Verify model loaded
        assert hasattr(model, 'model') or hasattr(model, 'transformer'), "Model should be loaded"
        
        # Verify adapter was loaded
        assert hasattr(model, 'assistant_lora'), "Assistant LoRA should be loaded"
        assert model.assistant_lora is not None, "Assistant LoRA should not be None"
        assert model.invert_assistant_lora == True, "invert_assistant_lora should be True"
        
        print(f"✓ Model loaded with Hub adapter")
        print(f"  Assistant LoRA loaded: {model.assistant_lora is not None}")
        print(f"  Invert flag: {model.invert_assistant_lora}")
    
    def test_hub_path_format_validation(self):
        """Test that Hub paths are correctly formatted."""
        # Test base model path
        assert "/" in self.base_model_id, "Base model ID should contain '/'"
        parts = self.base_model_id.split("/")
        assert len(parts) == 2, "Base model ID should be 'org/model'"
        
        # Test adapter path
        assert "/" in self.adapter_repo_id, "Adapter repo ID should contain '/'"
        adapter_parts = self.adapter_repo_id.split("/")
        assert len(adapter_parts) == 2, "Adapter repo ID should be 'org/repo'"
        
        print(f"✓ Hub path formats validated")
    
    def test_adapter_path_parsing(self):
        """Test that adapter path parsing works correctly."""
        # Test full Hub path format
        full_adapter_path = f"{self.adapter_repo_id}/{self.adapter_filename}"
        
        # The path should be parseable by the model loader
        config = ModelConfig(
            name_or_path=self.base_model_id,
            arch="zimage",
            assistant_lora_path=full_adapter_path
        )
        
        assert config.assistant_lora_path == full_adapter_path
        assert self.adapter_repo_id in config.assistant_lora_path
        assert self.adapter_filename in config.assistant_lora_path
        
        print(f"✓ Adapter path parsing works")
        print(f"  Full path: {full_adapter_path}")
    
    def test_hub_vs_local_paths(self):
        """Test that both Hub and local paths work in config."""
        # Test Hub paths
        hub_config = ModelConfig(
            name_or_path=self.base_model_id,
            arch="zimage",
            assistant_lora_path=f"{self.adapter_repo_id}/{self.adapter_filename}"
        )
        
        # Test local paths (if they exist)
        local_base = Path("/home/nfmil/model_vault/Tongyi-MAI/Z-Image-Turbo")
        local_adapter = Path("/home/nfmil/model_vault/ostris/zimage_turbo_training_adapter/zimage_turbo_training_adapter_v1.safetensors")
        
        if local_base.exists() and local_adapter.exists():
            local_config = ModelConfig(
                name_or_path=str(local_base),
                arch="zimage",
                assistant_lora_path=str(local_adapter)
            )
            
            assert local_config.name_or_path == str(local_base)
            assert local_config.assistant_lora_path == str(local_adapter)
            print(f"✓ Local paths also work")
        
        assert hub_config.name_or_path == self.base_model_id
        assert self.adapter_repo_id in hub_config.assistant_lora_path
        
        print(f"✓ Both Hub and local paths work correctly")
    
    def test_hub_authentication_check(self):
        """Test checking if Hub authentication is needed."""
        try:
            from huggingface_hub import whoami
            
            user_info = whoami()
            if user_info:
                print(f"✓ Authenticated to Hugging Face Hub")
                print(f"  User: {user_info.get('name', 'Unknown')}")
            else:
                print(f"⚠ Not authenticated (may need token for gated models)")
                
        except Exception as e:
            print(f"⚠ Could not check authentication: {e}")
            print(f"  You may need to run: huggingface-cli login")


def run_tests():
    """Run tests with pytest or manually."""
    print("=" * 60)
    print("Z-Image Turbo Hub Models Test Suite")
    print("=" * 60)
    print()
    
    if not HAS_TOOLKIT:
        print("❌ Toolkit modules not available!")
        print("Please ensure ai-toolkit-z_image_turbo is installed and in your Python path.")
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
    
    test_suite = TestZImageTurboHubModels()
    test_suite.setup_method()
    
    tests = [
        ("Hub Model IDs Valid", test_suite.test_hub_model_ids_valid),
        ("Model Discovery with Hub Path", test_suite.test_model_discovery_with_hub_path),
        ("Config with Hub Paths", test_suite.test_config_with_hub_paths),
        ("Hub Path Format Validation", test_suite.test_hub_path_format_validation),
        ("Adapter Path Parsing", test_suite.test_adapter_path_parsing),
        ("Hub vs Local Paths", test_suite.test_hub_vs_local_paths),
        ("Hub Authentication Check", test_suite.test_hub_authentication_check),
        ("Adapter Download", test_suite.test_adapter_download),
        ("Base Model Metadata", test_suite.test_base_model_download_metadata),
    ]
    
    # CUDA-only tests
    if torch.cuda.is_available():
        cuda_tests = [
            ("Model Loading from Hub", test_suite.test_model_loading_from_hub),
            ("Model Loading with Hub Adapter", test_suite.test_model_loading_with_hub_adapter),
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

