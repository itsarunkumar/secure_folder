"""macOS platform-specific helpers."""

import subprocess
from pathlib import Path

def set_hidden(path: Path, hidden: bool = True) -> bool:
    """Sets or unsets chflags hidden on macOS."""
    flag = "hidden" if hidden else "nohidden"
    try:
        res = subprocess.run(["chflags", flag, str(path)], capture_output=True, check=False)
        return res.returncode == 0
    except Exception:
        return False
