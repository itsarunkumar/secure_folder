"""Helper utility to stage SecureFolder portable bundle onto an external hard drive."""

import os
import shutil
import argparse
from pathlib import Path

def stage_external_drive(target_dir: Path) -> None:
    target_dir = Path(target_dir).resolve()
    if not target_dir.exists():
        print(f"Error: Target drive/directory does not exist: {target_dir}")
        return

    print("==================================================")
    print(f"Staging Zero-Block Portable Bundle to: {target_dir}")
    print("==================================================")

    project_root = Path(__file__).resolve().parent.parent
    bundle_src = project_root / "dist" / "portable_bundle"

    if not bundle_src.exists():
        print("Error: portable_bundle not found. Run scripts/build_portable_bundle.py first.")
        return

    for item in bundle_src.iterdir():
        dst = target_dir / item.name
        if item.is_dir():
            print(f"Copying directory: {item.name} -> {dst}")
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(item, dst)
        else:
            print(f"Copying file: {item.name} -> {dst}")
            shutil.copy2(item, dst)

    print("\n==================================================")
    print("[+] Drive staging COMPLETE! Zero-block portable bundle is ready.")
    print(f"Root of drive ({target_dir}) now contains:")
    for item in target_dir.iterdir():
        print(f" - {item.name}")
    print("==================================================")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Stage SecureFolder portable bundle to an external drive.")
    parser.add_argument("target", type=Path, help="Target drive letter or directory (e.g. E:\\ or D:\\)")
    args = parser.parse_args()
    stage_external_drive(args.target)
