"""Create a smaller image subset from a large example folder."""

from __future__ import annotations

import argparse
from pathlib import Path
import shutil

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tif", ".tiff"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a subset image folder for fast smoke tests.")
    parser.add_argument("--source", type=Path, required=True, help="Source image directory.")
    parser.add_argument("--target", type=Path, required=True, help="Target subset directory.")
    parser.add_argument("--count", type=int, default=20, help="Number of pages to copy.")
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Delete target directory before copying.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source: Path = args.source
    target: Path = args.target
    count: int = args.count

    if not source.exists() or not source.is_dir():
        raise SystemExit(f"Source directory not found: {source}")
    if count <= 0:
        raise SystemExit("--count must be greater than 0")

    files = sorted(
        [
            path
            for path in source.iterdir()
            if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS
        ],
        key=lambda path: path.name,
    )
    if not files:
        raise SystemExit(f"No supported image files found in {source}")

    selected = files[:count]
    if args.clean and target.exists():
        shutil.rmtree(target)

    target.mkdir(parents=True, exist_ok=True)
    for image_path in selected:
        shutil.copy2(image_path, target / image_path.name)

    print(f"Copied {len(selected)} files -> {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

