#!/usr/bin/env bash
set -e
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." >/dev/null 2>&1 && pwd)"
cd "$DIR"

echo "========================================================"
echo "Building SecureFolder for Linux (Standalone ELF Binary)"
echo "========================================================"

# Build onefile Linux binary
python3 -m PyInstaller \
  --name "secure-folder-linux" \
  --onefile \
  --clean \
  --noconfirm \
  --paths "src" \
  --collect-all "cryptography" \
  --exclude-module "pytest" \
  "src/secure_folder/main.py"

echo ""
echo "Build SUCCESSFUL! Binary created at: dist/secure-folder-linux"
