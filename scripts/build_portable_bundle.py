"""Builds a zero-block, self-contained portable bundle using official signed Python."""

import os
import sys
import shutil
import zipfile
import urllib.request
import subprocess
from pathlib import Path

PYTHON_EMBED_URL = "https://www.python.org/ftp/python/3.11.9/python-3.11.9-embed-amd64.zip"
PYTHON_VERSION_TAG = "3.11"
PYTHON_PTH_NAME = "python311._pth"

def build_portable_bundle() -> None:
    project_root = Path(__file__).resolve().parent.parent
    bundle_dir = project_root / "dist" / "portable_bundle"
    sf_dir = bundle_dir / "SecureFolder"
    python_dir = sf_dir / "python"
    site_packages = python_dir / "Lib" / "site-packages"

    print("========================================================")
    print("Building Zero-Block Portable Bundle (Signed Python)")
    print("========================================================")

    # 1. Clean and prepare target folders
    if bundle_dir.exists():
        shutil.rmtree(bundle_dir)
    site_packages.mkdir(parents=True, exist_ok=True)

    # 2. Download Python Embeddable package
    cache_dir = project_root / "build" / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    zip_path = cache_dir / "python-3.11.9-embed-amd64.zip"

    if not zip_path.exists():
        print(f"Downloading official signed Python runtime from:\n{PYTHON_EMBED_URL}...")
        urllib.request.urlretrieve(PYTHON_EMBED_URL, zip_path)
        print("Download complete.")
    else:
        print(f"Using cached Python runtime: {zip_path}")

    # 3. Extract Python runtime
    print(f"Extracting signed Python to: {python_dir}")
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(python_dir)

    # 4. Configure ._pth file to enable site-packages and src imports
    pth_file = python_dir / PYTHON_PTH_NAME
    if pth_file.exists():
        pth_content = (
            "python311.zip\n"
            ".\n"
            "Lib/site-packages\n"
            "../src\n"
            "import site\n"
        )
        pth_file.write_text(pth_content, encoding="utf-8")
        print(f"Configured {PYTHON_PTH_NAME} with site-packages support.")

    # 5. Download and install cryptography binary wheel for win_amd64
    print("Installing cryptography into portable site-packages...")
    pip_cmd = [
        sys.executable,
        "-m",
        "pip",
        "install",
        "--target",
        str(site_packages),
        "--platform",
        "win_amd64",
        "--python-version",
        PYTHON_VERSION_TAG,
        "--only-binary=:all:",
        "cryptography",
    ]
    subprocess.check_call(pip_cmd)
    print("Cryptography successfully installed into portable bundle.")

    # 6. Copy SecureFolder source files
    src_dest = sf_dir / "src"
    print(f"Copying SecureFolder source code -> {src_dest}")
    shutil.copytree(project_root / "src", src_dest)

    # 7. Copy standalone emergency recovery script and documentation
    for item in ["emergency_recover.py", "USER_MANUAL.md", "README.md"]:
        src_file = project_root / item
        if src_file.exists():
            shutil.copy2(src_file, bundle_dir / item)
            print(f"Copied {item} -> {bundle_dir / item}")

    # 8. Create zero-click batch launchers on bundle root
    # Unlock Launcher
    (bundle_dir / "Unlock_Vault.bat").write_text(
        "@echo off\n"
        "title SecureFolder - Unlock Vault\n"
        "cd /d \"%~dp0\"\n"
        "set \"PYTHONPATH=%~dp0SecureFolder\\src\"\n"
        "\"%~dp0SecureFolder\\python\\python.exe\" -m secure_folder.main unlock my_vault\n"
        "pause\n",
        encoding="utf-8"
    )

    # Lock Launcher
    (bundle_dir / "Lock_Vault.bat").write_text(
        "@echo off\n"
        "title SecureFolder - Lock Vault\n"
        "cd /d \"%~dp0\"\n"
        "set \"PYTHONPATH=%~dp0SecureFolder\\src\"\n"
        "\"%~dp0SecureFolder\\python\\python.exe\" -m secure_folder.main lock my_vault\n"
        "pause\n",
        encoding="utf-8"
    )

    # Status Launcher
    (bundle_dir / "Status_Vault.bat").write_text(
        "@echo off\n"
        "title SecureFolder - Status\n"
        "cd /d \"%~dp0\"\n"
        "set \"PYTHONPATH=%~dp0SecureFolder\\src\"\n"
        "\"%~dp0SecureFolder\\python\\python.exe\" -m secure_folder.main status my_vault\n"
        "pause\n",
        encoding="utf-8"
    )

    # Verify Launcher
    (bundle_dir / "Verify_Vault.bat").write_text(
        "@echo off\n"
        "title SecureFolder - Verify Integrity\n"
        "cd /d \"%~dp0\"\n"
        "set \"PYTHONPATH=%~dp0SecureFolder\\src\"\n"
        "\"%~dp0SecureFolder\\python\\python.exe\" -m secure_folder.main verify my_vault\n"
        "pause\n",
        encoding="utf-8"
    )

    print("\n========================================================")
    print("SUCCESS: Zero-Block Portable Bundle created!")
    print(f"Bundle directory: {bundle_dir}")
    print("========================================================")

if __name__ == "__main__":
    build_portable_bundle()
