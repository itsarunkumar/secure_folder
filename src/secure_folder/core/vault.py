"""High-level Vault lifecycle: init, unlock, lock, change-password, and status."""

import os
import json
import time
from pathlib import Path
from typing import Dict, Any, Optional

from secure_folder.utils.constants import (
    VAULT_CONFIG_NAME,
    VAULT_MANIFEST_NAME,
    VAULT_OBJECTS_DIR,
    VAULT_JOURNAL_NAME,
    SCRYPT_SALT_LEN,
    SCRYPT_N,
    SCRYPT_R,
    SCRYPT_P,
)
from secure_folder.utils.exceptions import (
    AuthenticationError,
    IntegrityError,
    VaultCorruptedError,
    VaultLockedError,
    VaultUnlockedError,
)
from secure_folder.core.key_manager import KeyManager
from secure_folder.core.manifest import VaultManifest
from secure_folder.core.encryption import encrypt_file, decrypt_file
from secure_folder.core.integrity import verify_vault_integrity, verify_encrypted_object
from secure_folder.filesystem.directory_manager import DirectoryManager
from secure_folder.filesystem.workspace import WorkspaceManager

class Vault:
    """Manages vault lifecycle operations."""

    @staticmethod
    def init_vault(vault_dir: Path, password: str) -> None:
        """Initializes a new SecureFolder vault in vault_dir."""
        vault_dir = Path(vault_dir).resolve()
        config_path = vault_dir / VAULT_CONFIG_NAME
        
        if config_path.exists():
            raise VaultCorruptedError(f"A vault already exists at: {vault_dir}")
        
        vault_dir.mkdir(parents=True, exist_ok=True)
        objects_dir = vault_dir / VAULT_OBJECTS_DIR
        objects_dir.mkdir(parents=True, exist_ok=True)

        salt = os.urandom(SCRYPT_SALT_LEN)
        kek = KeyManager.derive_kek(password, salt, n=SCRYPT_N, r=SCRYPT_R, p=SCRYPT_P)
        vdk = KeyManager.generate_data_key()
        encrypted_key_info = KeyManager.encrypt_data_key(vdk, kek)

        config_data = {
            "format_version": 1,
            "created_at": time.time(),
            "kdf": {
                "algorithm": "scrypt",
                "salt": salt.hex(),
                "n": SCRYPT_N,
                "r": SCRYPT_R,
                "p": SCRYPT_P,
            },
            "encrypted_key": encrypted_key_info,
            "status": "locked",
            "workspace": None,
        }

        # Write config
        temp_config = config_path.with_name(f"{config_path.name}.tmp")
        temp_config.write_text(json.dumps(config_data, indent=2), encoding="utf-8")
        temp_config.replace(config_path)

        # Initialize empty manifest
        manifest = VaultManifest()
        manifest.save(vault_dir, vdk)

        # Initialize journal
        journal_path = vault_dir / VAULT_JOURNAL_NAME
        journal_path.write_text(json.dumps({"state": "idle", "timestamp": time.time()}), encoding="utf-8")

    @staticmethod
    def authenticate(vault_dir: Path, password: str) -> bytes:
        """Authenticates password against vault.json and returns the Vault Data Key (VDK)."""
        vault_dir = Path(vault_dir).resolve()
        config_path = vault_dir / VAULT_CONFIG_NAME
        if not config_path.is_file():
            raise VaultCorruptedError(f"Vault config not found at: {config_path}")

        try:
            config = json.loads(config_path.read_text(encoding="utf-8"))
            kdf_info = config["kdf"]
            salt = bytes.fromhex(kdf_info["salt"])
            kek = KeyManager.derive_kek(
                password=password,
                salt=salt,
                n=kdf_info.get("n", SCRYPT_N),
                r=kdf_info.get("r", SCRYPT_R),
                p=kdf_info.get("p", SCRYPT_P),
            )
            return KeyManager.decrypt_data_key(config["encrypted_key"], kek)
        except AuthenticationError:
            raise
        except Exception as e:
            raise VaultCorruptedError(f"Corrupted or invalid vault configuration: {e}") from e

    @classmethod
    def unlock(cls, vault_dir: Path, password: str, target_workspace: Optional[Path] = None) -> Path:
        """Unlocks vault files into the workspace directory."""
        vault_dir = Path(vault_dir).resolve()
        vdk = cls.authenticate(vault_dir, password)
        config_path = vault_dir / VAULT_CONFIG_NAME
        config = json.loads(config_path.read_text(encoding="utf-8"))

        if target_workspace:
            workspace_dir = Path(target_workspace).resolve()
        else:
            workspace_dir = vault_dir.parent / f"{vault_dir.name}_unlocked"

        workspace_dir.mkdir(parents=True, exist_ok=True)
        manifest = VaultManifest.load(vault_dir, vdk)
        objects_dir = vault_dir / VAULT_OBJECTS_DIR

        # 1. Reconstruct directories
        DirectoryManager.create_directory_structure(workspace_dir, manifest.list_directories())

        # 2. Decrypt files
        for rel_path, meta in manifest.list_files().items():
            obj_id = meta["object_id"]
            enc_file_path = objects_dir / obj_id
            dst_file_path = workspace_dir / rel_path

            if not enc_file_path.exists():
                raise IntegrityError(f"Missing encrypted object for file: {rel_path}")

            decrypt_file(enc_file_path, dst_file_path, vdk)
            
            # Restore mtime if present
            mtime = meta.get("mtime")
            if mtime:
                try:
                    os.utime(dst_file_path, (mtime, mtime))
                except OSError:
                    pass

        # Update vault status
        config["status"] = "unlocked"
        config["workspace"] = str(workspace_dir)
        config_path.write_text(json.dumps(config, indent=2), encoding="utf-8")

        return workspace_dir

    @classmethod
    def lock(cls, vault_dir: Path, password: str) -> Dict[str, Any]:
        """Scans workspace, re-encrypts changes into the vault, validates integrity, and cleans workspace."""
        vault_dir = Path(vault_dir).resolve()
        vdk = cls.authenticate(vault_dir, password)
        config_path = vault_dir / VAULT_CONFIG_NAME
        config = json.loads(config_path.read_text(encoding="utf-8"))

        workspace_str = config.get("workspace")
        if not workspace_str:
            # Fallback to default
            default_ws = vault_dir.parent / f"{vault_dir.name}_unlocked"
            if default_ws.exists():
                workspace_dir = default_ws
            else:
                raise VaultLockedError("Vault has no active unlocked workspace recorded.")
        else:
            workspace_dir = Path(workspace_str)

        if not workspace_dir.exists():
            raise VaultLockedError(f"Workspace directory does not exist: {workspace_dir}")

        manifest = VaultManifest.load(vault_dir, vdk)
        objects_dir = vault_dir / VAULT_OBJECTS_DIR
        objects_dir.mkdir(parents=True, exist_ok=True)

        changes = WorkspaceManager.detect_changes(workspace_dir, manifest)
        
        # Track objects to clean up if modified or deleted
        objects_to_delete = []

        # 1. Handle deleted files
        for rel_path in changes["deleted"]:
            old_entry = manifest.remove_entry(rel_path)
            if old_entry and "object_id" in old_entry:
                objects_to_delete.append(old_entry["object_id"])

        # 2. Handle added & modified files
        files_to_encrypt = changes["added"] + changes["modified"]
        for rel_path in files_to_encrypt:
            src_file = workspace_dir / rel_path
            new_obj_id = VaultManifest.generate_object_id()
            dst_obj_path = objects_dir / new_obj_id

            enc_result = encrypt_file(src_file, dst_obj_path, vdk)
            
            # Verify the freshly encrypted object
            if not verify_encrypted_object(dst_obj_path, vdk):
                # Abort immediately, delete bad object
                if dst_obj_path.exists():
                    dst_obj_path.unlink()
                raise IntegrityError(f"Failed to verify encrypted object for {rel_path}. Workspace retained.")

            old_entry = manifest.get_entry(rel_path)
            if old_entry and "object_id" in old_entry:
                objects_to_delete.append(old_entry["object_id"])

            stat = src_file.stat()
            manifest.add_file(
                rel_path=rel_path,
                object_id=new_obj_id,
                size=enc_result["original_size"],
                sha256=enc_result["sha256"],
                mtime=stat.st_mtime,
            )

        # 3. Handle directories
        for d in changes["deleted_dirs"]:
            manifest.remove_entry(d)
        for d in changes["current_dirs"]:
            manifest.add_directory(d, mtime=time.time())

        # Save manifest
        manifest.save(vault_dir, vdk)

        # Delete superseded object files
        for old_obj_id in objects_to_delete:
            old_path = objects_dir / old_obj_id
            if old_path.exists():
                try:
                    old_path.unlink()
                except OSError:
                    pass

        # Perform overall integrity verification before cleaning workspace
        integrity_report = verify_vault_integrity(vault_dir, vdk)
        if not integrity_report["healthy"]:
            raise IntegrityError(f"Vault verification failed after encryption: {integrity_report}. Workspace retained.")

        # Safely remove unlocked workspace
        WorkspaceManager.safe_cleanup(workspace_dir)

        # Update vault config
        config["status"] = "locked"
        config["workspace"] = None
        config_path.write_text(json.dumps(config, indent=2), encoding="utf-8")

        return {
            "added": len(changes["added"]),
            "modified": len(changes["modified"]),
            "deleted": len(changes["deleted"]),
            "unchanged": len(changes["unchanged"]),
        }

    @classmethod
    def verify(cls, vault_dir: Path, password: str) -> Dict[str, Any]:
        """Verifies the integrity of all objects in the vault."""
        vault_dir = Path(vault_dir).resolve()
        vdk = cls.authenticate(vault_dir, password)
        return verify_vault_integrity(vault_dir, vdk)

    @classmethod
    def change_password(cls, vault_dir: Path, old_password: str, new_password: str) -> None:
        """Changes the vault password by re-encrypting the VDK with a new KEK."""
        vault_dir = Path(vault_dir).resolve()
        vdk = cls.authenticate(vault_dir, old_password)
        config_path = vault_dir / VAULT_CONFIG_NAME
        config = json.loads(config_path.read_text(encoding="utf-8"))

        new_salt = os.urandom(SCRYPT_SALT_LEN)
        new_kek = KeyManager.derive_kek(new_password, new_salt, n=SCRYPT_N, r=SCRYPT_R, p=SCRYPT_P)
        new_encrypted_key = KeyManager.encrypt_data_key(vdk, new_kek)

        config["kdf"]["salt"] = new_salt.hex()
        config["encrypted_key"] = new_encrypted_key

        temp_config = config_path.with_name(f"{config_path.name}.tmp")
        temp_config.write_text(json.dumps(config, indent=2), encoding="utf-8")
        temp_config.replace(config_path)

    @staticmethod
    def get_status(vault_dir: Path) -> Dict[str, Any]:
        """Returns non-sensitive vault status without requiring password."""
        vault_dir = Path(vault_dir).resolve()
        config_path = vault_dir / VAULT_CONFIG_NAME
        if not config_path.is_file():
            return {"exists": False}
        try:
            config = json.loads(config_path.read_text(encoding="utf-8"))
            return {
                "exists": True,
                "status": config.get("status", "unknown"),
                "workspace": config.get("workspace"),
                "created_at": config.get("created_at"),
            }
        except Exception:
            return {"exists": True, "status": "corrupted"}
