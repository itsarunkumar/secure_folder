#!/usr/bin/env bash
set -e
DIR="$(cd "$(dirname "$0")/.." >/dev/null 2>&1 && pwd)"
cd "$DIR"

echo "========================================================"
echo "Building SecureFolder for macOS (Mach-O Binary)"
echo "========================================================"

# Build onefile macOS binary
python3 -m PyInstaller \
  --name "secure-folder-macos" \
  --onefile \
  --clean \
  --noconfirm \
  --paths "src" \
  --collect-all "cryptography" \
  --exclude-module "pytest" \
  "src/secure_folder/main.py"

echo ""
echo "Build SUCCESSFUL! Binary created at: dist/secure-folder-macos"
