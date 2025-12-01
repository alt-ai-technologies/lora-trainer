#!/usr/bin/env python3
"""Helper script to list files in Modal volume."""
import modal

app = modal.App("list-files")

volume = modal.Volume.from_name("zimage-generation-outputs")

@app.function(volumes={"/vol": volume})
def list_files():
    import os
    from pathlib import Path
    
    # Check common output locations
    paths_to_check = [
        "/root/modal_output",
        "/vol",
        "/root",
    ]
    
    print("Checking for generated images...")
    for path in paths_to_check:
        if os.path.exists(path):
            print(f"\n✓ Found: {path}")
            for root, dirs, files in os.walk(path):
                level = root.replace(path, '').count(os.sep)
                indent = ' ' * 2 * level
                print(f'{indent}{os.path.basename(root)}/')
                subindent = ' ' * 2 * (level + 1)
                for file in files:
                    print(f'{subindent}{file}')
        else:
            print(f"\n✗ Not found: {path}")

if __name__ == "__main__":
    with app.run():
        list_files.remote()

