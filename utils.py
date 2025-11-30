from datetime import datetime
from pathlib import Path
import re


def slugify(text: str, max_length: int = 50) -> str:
    slug = text.lower()
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'[\s_]+', '-', slug)
    slug = re.sub(r'-+', '-', slug).strip('-')
    return slug[:max_length]


def get_output_path(prompt: str, output: str | None, prefix: str = "") -> Path:
    if output is None:
        slug = slugify(prompt)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if prefix:
            output = f"output/{prefix}_{slug}_{timestamp}.png"
        else:
            output = f"output/{slug}_{timestamp}.png"

    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    return output_path
