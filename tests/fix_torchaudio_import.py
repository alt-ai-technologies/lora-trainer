#!/usr/bin/env python3
"""
Helper script to fix torchaudio import issues for testing.

This script patches torchaudio before importing toolkit modules,
allowing tests to run even if torchaudio has version mismatches.
"""

import sys
import types

def patch_torchaudio():
    """Create a mock torchaudio module if the real one can't be loaded."""
    try:
        import torchaudio
        # If we get here, torchaudio loaded successfully
        return True
    except (ImportError, OSError) as e:
        # Create a minimal mock torchaudio module
        mock_torchaudio = types.ModuleType('torchaudio')
        
        # Add a dummy save function (used by config_modules)
        def dummy_save(path, tensor, sample_rate=48000):
            """Dummy save function - does nothing."""
            pass
        
        mock_torchaudio.save = dummy_save
        mock_torchaudio.__version__ = "0.0.0"
        
        # Inject into sys.modules before any imports
        sys.modules['torchaudio'] = mock_torchaudio
        
        print(f"⚠ Warning: torchaudio not available ({e})")
        print("  Using mock torchaudio for testing (audio features will be disabled)")
        return False

if __name__ == "__main__":
    patch_torchaudio()
    print("Torchaudio patched. You can now import toolkit modules.")

