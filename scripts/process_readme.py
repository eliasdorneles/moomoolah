#!/usr/bin/env python3
"""Process README.md to convert local image URLs to GitHub URLs for PyPI."""

import re
import sys
from pathlib import Path


def process_readme(tag_version: str) -> None:
    """Convert local image URLs to GitHub URLs in README.md.

    Args:
        tag_version: The git tag version (e.g., "0.2.0")
    """
    readme_path = Path("README.md")

    if not readme_path.exists():
        print(f"Error: {readme_path} not found", file=sys.stderr)
        sys.exit(1)

    content = readme_path.read_text()

    # GitHub repository base URL for raw files at specific tag
    github_base = (
        f"https://raw.githubusercontent.com/eliasdorneles/moomoolah/v{tag_version}"
    )

    # Replace linked images: [![alt](./path)](./path)
    content = re.sub(
        r"\[\!\[([^\]]*)\]\(\./([^)]+)\)\]\(\./([^)]+)\)",
        rf"[!\[\1]({github_base}/\2)]({github_base}/\3)",
        content,
    )

    # Replace simple images: ![alt](./path)
    content = re.sub(
        r"\!\[([^\]]*)\]\(\./([^)]+)\)", rf"![\1]({github_base}/\2)", content
    )

    # Write the processed content back
    readme_path.write_text(content)
    print(f"Processed README.md with GitHub URLs for tag v{tag_version}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: process_readme.py <tag_version>", file=sys.stderr)
        print("Example: process_readme.py 0.2.0", file=sys.stderr)
        sys.exit(1)

    tag_version = sys.argv[1]
    process_readme(tag_version)
