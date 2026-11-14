"""Linux platform-specific helpers."""

from pathlib import Path

def set_hidden(path: Path, hidden: bool = True) -> bool:
    """Linux uses dot prefix for hidden files by convention."""
    return True
