"""Encrypted vault manifest handling file/directory hierarchy and object mapping."""

import json
import uuid
from pathlib import Path
from typing import Dict, Any, List, Optional

from secure_folder.core.encryption import encrypt_bytes, decrypt_bytes
from secure_folder.utils.constants import VAULT_MANIFEST_NAME
from secure_folder.utils.exceptions import VaultCorruptedError, IntegrityError

MANIFEST_AAD = b"SecureFolder-Manifest-v1"

class VaultManifest:
    """Represents the encrypted manifest of files and directories within a vault."""

    def __init__(self, entries: Optional[Dict[str, Any]] = None):
        # entries: dict mapping rel_path -> metadata
        # for file: { "type": "file", "object_id": str, "size": int, "sha256": str, "mtime": float }
        # for directory: { "type": "directory", "mtime": float }
        self.entries: Dict[str, Dict[str, Any]] = entries or {}

    def add_file(
        self,
        rel_path: str,
        object_id: str,
        size: int,
        sha256: str,
        mtime: float,
    ) -> None:
        """Adds or updates a file entry in the manifest."""
        self.entries[rel_path] = {
            "type": "file",
            "object_id": object_id,
            "size": size,
            "sha256": sha256,
            "mtime": mtime,
        }

    def add_directory(self, rel_path: str, mtime: float) -> None:
        """Adds a directory entry to preserve empty folder hierarchies."""
        self.entries[rel_path] = {
            "type": "directory",
            "mtime": mtime,
        }

    def remove_entry(self, rel_path: str) -> Optional[Dict[str, Any]]:
        """Removes an entry from the manifest and returns it."""
        return self.entries.pop(rel_path, None)

    def get_entry(self, rel_path: str) -> Optional[Dict[str, Any]]:
        return self.entries.get(rel_path)

    def list_files(self) -> Dict[str, Dict[str, Any]]:
        """Returns all file entries."""
        return {k: v for k, v in self.entries.items() if v.get("type") == "file"}

    def list_directories(self) -> List[str]:
        """Returns relative paths of all recorded directories."""
        return [k for k, v in self.entries.items() if v.get("type") == "directory"]

    @staticmethod
    def generate_object_id() -> str:
        """Generates a unique opaque object identifier for storage in objects/ directory."""
        return f"obj_{uuid.uuid4().hex}.enc"

    def serialize(self, vault_data_key: bytes) -> bytes:
        """Serializes entries to JSON and encrypts with AES-256-GCM."""
        payload = {
            "version": 1,
            "entries": self.entries,
        }
        json_bytes = json.dumps(payload, indent=2).encode("utf-8")
        return encrypt_bytes(json_bytes, vault_data_key, associated_data=MANIFEST_AAD)

    @classmethod
    def deserialize(cls, encrypted_bytes: bytes, vault_data_key: bytes) -> "VaultManifest":
        """Decrypts and parses an encrypted manifest."""
        try:
            raw_json = decrypt_bytes(encrypted_bytes, vault_data_key, associated_data=MANIFEST_AAD)
            data = json.loads(raw_json.decode("utf-8"))
            return cls(entries=data.get("entries", {}))
        except IntegrityError as e:
            raise VaultCorruptedError("Corrupted manifest: authentication tag failed.") from e
        except Exception as e:
            raise VaultCorruptedError(f"Failed to read manifest: {e}") from e

    def save(self, vault_dir: Path, vault_data_key: bytes) -> None:
        """Encrypts and atomically saves manifest to vault_dir / manifest.enc."""
        vault_dir = Path(vault_dir)
        manifest_path = vault_dir / VAULT_MANIFEST_NAME
        temp_path = manifest_path.with_name(f"{manifest_path.name}.tmp_{uuid.uuid4().hex[:8]}")
        enc_data = self.serialize(vault_data_key)
        try:
            temp_path.write_bytes(enc_data)
            temp_path.replace(manifest_path)
        except Exception:
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except OSError:
                    pass
            raise

    @classmethod
    def load(cls, vault_dir: Path, vault_data_key: bytes) -> "VaultManifest":
        """Loads and decrypts manifest from vault_dir / manifest.enc."""
        manifest_path = Path(vault_dir) / VAULT_MANIFEST_NAME
        if not manifest_path.is_file():
            raise VaultCorruptedError(f"Manifest not found: {manifest_path}")
        return cls.deserialize(manifest_path.read_bytes(), vault_data_key)
