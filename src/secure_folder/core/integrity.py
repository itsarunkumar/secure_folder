"""Integrity verification and corruption detection services."""

import os
import struct
from pathlib import Path
from typing import Dict, Any, List
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.exceptions import InvalidTag

from secure_folder.core.manifest import VaultManifest
from secure_folder.core.key_manager import KeyManager
from secure_folder.core.encryption import (
    HEADER_STRUCT,
    HEADER_SIZE,
    CHUNK_HDR_STRUCT,
    CHUNK_HDR_SIZE,
    _build_chunk_nonce,
    _build_chunk_aad,
)
from secure_folder.utils.constants import (
    VAULT_OBJECTS_DIR,
    VAULT_CONFIG_NAME,
    VAULT_MANIFEST_NAME,
    FILE_MAGIC,
    FILE_FORMAT_VERSION,
    NONCE_LEN,
)
from secure_folder.utils.exceptions import IntegrityError

def verify_encrypted_object(object_path: Path, vault_data_key: bytes) -> bool:
    """Verifies that an encrypted file object has valid headers, chunk structures,
    and authentication tags without writing decrypted output to disk.
    Returns True if authentic and uncorrupted, False otherwise.
    """
    if not object_path.is_file():
        return False

    try:
        with open(object_path, "rb") as fin:
            header_bytes = fin.read(HEADER_SIZE)
            if len(header_bytes) < HEADER_SIZE:
                return False
            
            magic, version, chunk_size, file_id = HEADER_STRUCT.unpack(header_bytes)
            if magic != FILE_MAGIC or version != FILE_FORMAT_VERSION:
                return False
            
            file_key = KeyManager.derive_file_key(vault_data_key, file_id)
            aesgcm = AESGCM(file_key)
            
            chunk_index = 0
            has_last = False
            
            while True:
                hdr_bytes = fin.read(CHUNK_HDR_SIZE)
                if not hdr_bytes:
                    break
                if len(hdr_bytes) < CHUNK_HDR_SIZE:
                    return False
                
                payload_len, is_last_flag = CHUNK_HDR_STRUCT.unpack(hdr_bytes)
                is_last = (is_last_flag == 1)
                
                nonce = fin.read(NONCE_LEN)
                if len(nonce) < NONCE_LEN:
                    return False
                if nonce != _build_chunk_nonce(chunk_index):
                    return False
                
                ciphertext = fin.read(payload_len)
                if len(ciphertext) < payload_len:
                    return False
                
                aad = _build_chunk_aad(file_id, version, chunk_index, is_last)
                
                # Verify tag by attempting decrypt (plaintext is discarded in memory)
                try:
                    aesgcm.decrypt(nonce, ciphertext, aad)
                except InvalidTag:
                    return False
                
                chunk_index += 1
                if is_last:
                    has_last = True
                    extra = fin.read(1)
                    if extra:
                        return False
                    break
            
            return has_last
    except Exception:
        return False

def verify_vault_integrity(vault_dir: Path, vault_data_key: bytes) -> Dict[str, Any]:
    """Performs a comprehensive integrity scan across the vault manifest and objects.
    
    Returns:
        Dict with summary statistics and details of corrupted/missing/orphaned objects.
    """
    vault_dir = Path(vault_dir)
    objects_dir = vault_dir / VAULT_OBJECTS_DIR
    manifest = VaultManifest.load(vault_dir, vault_data_key)
    
    file_entries = manifest.list_files()
    directories = manifest.list_directories()
    
    verified_files: List[str] = []
    corrupted_files: List[str] = []
    missing_objects: List[str] = []
    
    referenced_objects = set()
    
    for rel_path, meta in file_entries.items():
        obj_id = meta.get("object_id")
        if not obj_id:
            corrupted_files.append(rel_path)
            continue
        
        referenced_objects.add(obj_id)
        obj_path = objects_dir / obj_id
        
        if not obj_path.exists():
            missing_objects.append(rel_path)
            continue
        
        if verify_encrypted_object(obj_path, vault_data_key):
            verified_files.append(rel_path)
        else:
            corrupted_files.append(rel_path)
    
    # Check for orphaned objects in objects/
    orphaned_objects: List[str] = []
    if objects_dir.exists():
        for item in objects_dir.iterdir():
            if item.is_file() and item.name not in referenced_objects:
                orphaned_objects.append(item.name)
    
    is_healthy = (len(corrupted_files) == 0 and len(missing_objects) == 0)
    
    return {
        "healthy": is_healthy,
        "total_files": len(file_entries),
        "total_directories": len(directories),
        "verified_files_count": len(verified_files),
        "corrupted_files": corrupted_files,
        "missing_objects": missing_objects,
        "orphaned_objects": orphaned_objects,
    }
