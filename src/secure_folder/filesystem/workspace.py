"""Workspace management: tracking changes, syncing, and safe cleanup."""

import shutil
from pathlib import Path
from typing import Dict, Any, List, Set

from secure_folder.core.manifest import VaultManifest
from secure_folder.filesystem.directory_manager import DirectoryManager

class WorkspaceManager:
    """Manages the unlocked working directory and detects file modifications."""

    @staticmethod
    def detect_changes(workspace_dir: Path, manifest: VaultManifest) -> Dict[str, Any]:
        """Compares current files in workspace_dir against the vault manifest.
        
        Returns:
            Dict containing:
                - 'added': list of relative file paths
                - 'modified': list of relative file paths
                - 'deleted': list of relative file paths
                - 'unchanged': list of relative file paths
                - 'workspace_dirs': list of relative dir paths
                - 'deleted_dirs': list of relative dir paths removed
        """
        workspace_dir = Path(workspace_dir).resolve()
        current_scan = DirectoryManager.scan_directory(workspace_dir)
        manifest_files = manifest.list_files()
        manifest_dirs = set(manifest.list_directories())

        current_files = {k: v for k, v in current_scan.items() if v.get("type") == "file"}
        current_dirs = {k for k, v in current_scan.items() if v.get("type") == "directory"}

        added: List[str] = []
        modified: List[str] = []
        unchanged: List[str] = []
        deleted: List[str] = []

        for rel_path, curr_meta in current_files.items():
            if rel_path not in manifest_files:
                added.append(rel_path)
            else:
                man_meta = manifest_files[rel_path]
                # Compare size first for fast check, then sha256
                if curr_meta["size"] != man_meta["size"] or curr_meta["sha256"] != man_meta["sha256"]:
                    modified.append(rel_path)
                else:
                    unchanged.append(rel_path)

        for rel_path in manifest_files:
            if rel_path not in current_files:
                deleted.append(rel_path)

        deleted_dirs = list(manifest_dirs - current_dirs)

        return {
            "added": added,
            "modified": modified,
            "deleted": deleted,
            "unchanged": unchanged,
            "current_dirs": list(current_dirs),
            "deleted_dirs": deleted_dirs,
            "scan_data": current_scan,
        }

    @staticmethod
    def safe_cleanup(workspace_dir: Path) -> None:
        """Removes the workspace directory safely.
        Must only be called after all changes have been encrypted and verified.
        """
        workspace_dir = Path(workspace_dir)
        if workspace_dir.exists() and workspace_dir.is_dir():
            shutil.rmtree(workspace_dir)
