"""Helper utility to stage SecureFolder portable files onto an external hard drive."""

import os
import shutil
import argparse
from pathlib import Path

def stage_external_drive(target_dir: Path) -> None:
    target_dir = Path(target_dir).resolve()
    if not target_dir.exists():
        print(f"Error: Target directory does not exist: {target_dir}")
        return

    print(f"==================================================")
    print(f"Staging SecureFolder to External Drive: {target_dir}")
    print(f"==================================================")

    project_root = Path(__file__).resolve().parent.parent
    dist_dir = project_root / "dist"
    win_exe = dist_dir / "secure-folder-windows.exe"

    # 1. Copy Windows Executable to Drive Root
    if win_exe.exists():
        dest_exe = target_dir / "secure-folder.exe"
        print(f"Copying {win_exe.name} -> {dest_exe}")
        shutil.copy2(win_exe, dest_exe)
    else:
        print(f"Warning: {win_exe} not found. Run scripts/build_windows.bat first.")

    # 2. Copy User Manual and Readme
    for doc in ["USER_MANUAL.md", "README.md"]:
        doc_src = project_root / doc
        if doc_src.exists():
            print(f"Copying {doc} -> {target_dir / doc}")
            shutil.copy2(doc_src, target_dir / doc)

    # 3. Create Convenience Windows Launchers on Drive Root
    unlock_bat = target_dir / "Unlock_Vault.bat"
    unlock_bat.write_text(
        "@echo off\n"
        "cd /d \"%~dp0\"\n"
        "if exist secure-folder.exe (\n"
        "    secure-folder.exe unlock my_vault\n"
        ") else (\n"
        "    echo secure-folder.exe not found!\n"
        ")\n"
        "pause\n",
        encoding="utf-8"
    )
    print(f"Created convenience launcher: {unlock_bat}")

    lock_bat = target_dir / "Lock_Vault.bat"
    lock_bat.write_text(
        "@echo off\n"
        "cd /d \"%~dp0\"\n"
        "if exist secure-folder.exe (\n"
        "    secure-folder.exe lock my_vault\n"
        ") else (\n"
        "    echo secure-folder.exe not found!\n"
        ")\n"
        "pause\n",
        encoding="utf-8"
    )
    print(f"Created convenience launcher: {lock_bat}")

    print("\nExternal hard drive staging COMPLETE!")
    print("Files ready on external drive:")
    for item in target_dir.iterdir():
        print(f" - {item.name}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Stage SecureFolder to an external drive.")
    parser.add_argument("target", type=Path, help="Target drive letter or directory (e.g. E:\\ or D:\\)")
    args = parser.parse_args()
    stage_external_drive(args.target)
