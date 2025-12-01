#!/usr/bin/env python3
"""Check what's actually in the Modal volume."""
import modal

app = modal.App("check-output")

volume = modal.Volume.from_name("zimage-generation-outputs")

@app.function(volumes={"/root/modal_output": volume})
def check_output():
    import os
    from pathlib import Path
    
    output_dir = "/root/modal_output"
    
    print(f"Checking: {output_dir}")
    print(f"Exists: {os.path.exists(output_dir)}")
    
    if os.path.exists(output_dir):
        print(f"\nContents of {output_dir}:")
        items = list(Path(output_dir).iterdir())
        if not items:
            print("  (empty)")
        else:
            for item in sorted(items):
                if item.is_dir():
                    print(f"  📁 {item.name}/")
                    # List contents of subdirectory
                    for subitem in sorted(item.iterdir()):
                        size = subitem.stat().st_size if subitem.is_file() else 0
                        print(f"    - {subitem.name} ({size:,} bytes)" if subitem.is_file() else f"    📁 {subitem.name}/")
                else:
                    size = item.stat().st_size
                    print(f"  📄 {item.name} ({size:,} bytes)")
    
    # Also check root
    print(f"\n\nChecking /root:")
    root_items = [p for p in Path("/root").iterdir() if p.name != "modal_output"]
    for item in sorted(root_items)[:10]:
        print(f"  {item.name}")

if __name__ == "__main__":
    with app.run():
        check_output.remote()

