"""File operations, streaming hash calculation, and atomic writes."""

import os
import shutil
import hashlib
from pathlib import Path
from typing import Optional

def compute_sha256(path: Path, chunk_size: int = 1024 * 1024) -> str:
    """Computes SHA-256 hash of a file by streaming in chunks to bound memory usage."""
    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            hasher.update(chunk)
    return hasher.hexdigest()

def copy_file_safe(src: Path, dst: Path) -> None:
    """Copies a file safely using a temporary file and atomic replace."""
    src = Path(src)
    dst = Path(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    temp_dst = dst.with_name(f"{dst.name}.tmp_{os.urandom(4).hex()}")
    try:
        shutil.copy2(src, temp_dst)
        os.replace(temp_dst, dst)
    except Exception:
        if temp_dst.exists():
            try:
                temp_dst.unlink()
            except OSError:
                pass
        raise
