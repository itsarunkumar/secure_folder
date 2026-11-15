#!/usr/bin/env python3
"""
launch_ui.py — Launch the SecureFolder desktop UI.

Usage:
    python launch_ui.py              # auto-detects my_vault next to this file
    python launch_ui.py path/to/vault
"""
import sys
from pathlib import Path

# Ensure the src package is importable
_root = Path(__file__).resolve().parent
_src  = _root / "src"
if str(_src) not in sys.path:
    sys.path.insert(0, str(_src))

from secure_folder.ui.app import launch

if __name__ == "__main__":
    vault = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    launch(vault)
