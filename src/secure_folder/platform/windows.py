"""Windows platform-specific helpers."""

import os
import ctypes
from pathlib import Path

def set_hidden(path: Path, hidden: bool = True) -> bool:
    """Sets or unsets the Windows hidden attribute (FILE_ATTRIBUTE_HIDDEN)."""
    FILE_ATTRIBUTE_HIDDEN = 0x02
    FILE_ATTRIBUTE_NORMAL = 0x80
    try:
        attrs = ctypes.windll.kernel32.GetFileAttributesW(str(path))
        if attrs == -1:
            return False
        if hidden:
            new_attrs = attrs | FILE_ATTRIBUTE_HIDDEN
        else:
            new_attrs = attrs & ~FILE_ATTRIBUTE_HIDDEN
            if new_attrs == 0:
                new_attrs = FILE_ATTRIBUTE_NORMAL
        return bool(ctypes.windll.kernel32.SetFileAttributesW(str(path), new_attrs))
    except Exception:
        return False
