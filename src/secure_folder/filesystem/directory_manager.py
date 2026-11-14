"""Directory traversal and structure management."""

import os
from pathlib import Path
from typing import Dict, Any, List

from secure_folder.filesystem.file_manager import compute_sha256

class DirectoryManager:
    """Handles recursive directory scanning, path normalization, and folder reconstruction."""

    @staticmethod
    def scan_directory(base_dir: Path) -> Dict[str, Dict[str, Any]]:
        """Recursively scans base_dir and returns a map of relative_posix_path -> metadata.
        Directories and files are both captured to preserve empty folders.
        """
        base_dir = Path(base_dir).resolve()
        result: Dict[str, Dict[str, Any]] = {}

        if not base_dir.exists():
            return result

        for root, dirs, files in os.walk(base_dir):
            root_path = Path(root)
            rel_root = root_path.relative_to(base_dir)

            # Record directories (to preserve empty directory structure)
            for d in dirs:
                dir_path = root_path / d
                rel_path = (rel_root / d).as_posix()
                result[rel_path] = {
                    "type": "directory",
                    "mtime": dir_path.stat().st_mtime,
                }

            # Record files
            for f in files:
                file_path = root_path / f
                # Skip transient/lock/temp files
                if f.endswith(".tmp") or ".tmp_" in f or f == ".DS_Store" or f == "Thumbs.db":
                    continue
                
                rel_path = (rel_root / f).as_posix()
                stat = file_path.stat()
                result[rel_path] = {
                    "type": "file",
                    "size": stat.st_size,
                    "mtime": stat.st_mtime,
                    "sha256": compute_sha256(file_path),
                }

        return result

    @staticmethod
    def create_directory_structure(target_base: Path, dir_paths: List[str]) -> None:
        """Creates nested directories in target_base from relative POSIX paths."""
        target_base = Path(target_base)
        for rel_dir in sorted(dir_paths):
            dest = target_base / rel_dir
            dest.mkdir(parents=True, exist_ok=True)
