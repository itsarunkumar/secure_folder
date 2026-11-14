"""Core encryption and decryption engine with chunked authenticated streaming."""

import os
import struct
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.exceptions import InvalidTag

from secure_folder.utils.constants import (
    FILE_MAGIC,
    FILE_FORMAT_VERSION,
    DEFAULT_CHUNK_SIZE,
    NONCE_LEN,
    TAG_LEN,
)
from secure_folder.utils.exceptions import IntegrityError
from secure_folder.core.key_manager import KeyManager

# Header format: MAGIC (4s), VERSION (H = 2 bytes), CHUNK_SIZE (I = 4 bytes), FILE_ID (16s)
HEADER_STRUCT = struct.Struct(">4sHI16s")
HEADER_SIZE = HEADER_STRUCT.size  # 4 + 2 + 4 + 16 = 26 bytes

# Chunk header format: PAYLOAD_LEN (I = 4 bytes), IS_LAST (B = 1 byte)
CHUNK_HDR_STRUCT = struct.Struct(">IB")
CHUNK_HDR_SIZE = CHUNK_HDR_STRUCT.size  # 5 bytes

def _build_chunk_nonce(chunk_index: int) -> bytes:
    """Builds a deterministic 12-byte nonce for a given chunk index within a file."""
    return b"\x00" * 8 + chunk_index.to_bytes(4, byteorder="big")

def _build_chunk_aad(file_id: bytes, version: int, chunk_index: int, is_last: bool) -> bytes:
    """Builds authenticated associated data (AAD) binding chunk index, file ID, and last marker."""
    return (
        FILE_MAGIC
        + version.to_bytes(2, "big")
        + file_id
        + chunk_index.to_bytes(4, "big")
        + (b"\x01" if is_last else b"\x00")
    )

def encrypt_bytes(data: bytes, key: bytes, associated_data: Optional[bytes] = None) -> bytes:
    """Encrypts arbitrary bytes using AES-256-GCM.
    Returns: 12-byte nonce + ciphertext + 16-byte tag.
    """
    nonce = os.urandom(NONCE_LEN)
    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(nonce, data, associated_data)
    return nonce + ciphertext

def decrypt_bytes(data: bytes, key: bytes, associated_data: Optional[bytes] = None) -> bytes:
    """Decrypts bytes previously encrypted with encrypt_bytes.
    Raises: IntegrityError if verification fails.
    """
    if len(data) < NONCE_LEN + TAG_LEN:
        raise IntegrityError("Encrypted payload too short to contain nonce and tag.")
    nonce = data[:NONCE_LEN]
    ciphertext = data[NONCE_LEN:]
    aesgcm = AESGCM(key)
    try:
        return aesgcm.decrypt(nonce, ciphertext, associated_data)
    except InvalidTag as e:
        raise IntegrityError("Authentication tag verification failed for payload.") from e

def encrypt_file(
    src_path: Path,
    dst_path: Path,
    vault_data_key: bytes,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
) -> Dict[str, Any]:
    """Encrypts a file in chunks using AES-256-GCM without compression.
    Writes atomically via a temporary file. Never modifies src_path.
    
    Returns:
        Dict with 'original_size', 'encrypted_size', 'sha256' of plaintext, and 'file_id'.
    """
    src_path = Path(src_path)
    dst_path = Path(dst_path)
    
    if not src_path.is_file():
        raise FileNotFoundError(f"Source file not found: {src_path}")
    
    file_id = os.urandom(16)
    file_key = KeyManager.derive_file_key(vault_data_key, file_id)
    aesgcm = AESGCM(file_key)
    
    dst_path.parent.mkdir(parents=True, exist_ok=True)
    temp_dst = dst_path.with_name(f"{dst_path.name}.tmp_{os.urandom(4).hex()}")
    
    sha256_hasher = hashlib.sha256()
    original_size = 0
    encrypted_size = 0
    
    try:
        with open(src_path, "rb") as fin, open(temp_dst, "wb") as fout:
            # Write file header
            header_bytes = HEADER_STRUCT.pack(FILE_MAGIC, FILE_FORMAT_VERSION, chunk_size, file_id)
            fout.write(header_bytes)
            encrypted_size += len(header_bytes)
            
            chunk_index = 0
            while True:
                chunk = fin.read(chunk_size)
                # Check if this is the final chunk by peeking 1 byte
                peek = fin.read(1)
                if peek:
                    # Put back peek byte by seeking backwards
                    fin.seek(-1, os.SEEK_CUR)
                    is_last = False
                else:
                    is_last = True
                
                original_size += len(chunk)
                sha256_hasher.update(chunk)
                
                nonce = _build_chunk_nonce(chunk_index)
                aad = _build_chunk_aad(file_id, FILE_FORMAT_VERSION, chunk_index, is_last)
                
                # Encrypt chunk (returns ciphertext + 16-byte tag)
                ciphertext = aesgcm.encrypt(nonce, chunk, aad)
                
                # Write chunk header: payload_len (I) + is_last (B) + nonce (12s) + ciphertext
                chunk_hdr = CHUNK_HDR_STRUCT.pack(len(ciphertext), 1 if is_last else 0)
                fout.write(chunk_hdr)
                fout.write(nonce)
                fout.write(ciphertext)
                
                encrypted_size += len(chunk_hdr) + len(nonce) + len(ciphertext)
                
                chunk_index += 1
                if is_last:
                    break
        
        # Atomic replace
        os.replace(temp_dst, dst_path)
        
        return {
            "original_size": original_size,
            "encrypted_size": encrypted_size,
            "sha256": sha256_hasher.hexdigest(),
            "file_id": file_id.hex(),
            "chunk_count": chunk_index,
        }
    except Exception:
        if temp_dst.exists():
            try:
                temp_dst.unlink()
            except OSError:
                pass
        raise

def decrypt_file(
    src_path: Path,
    dst_path: Path,
    vault_data_key: bytes,
) -> Dict[str, Any]:
    """Decrypts a chunked encrypted file and verifies authentication tags before releasing.
    Writes atomically via a temporary file.
    
    Returns:
        Dict with 'restored_size', 'sha256' of decrypted file, and 'chunk_count'.
    """
    src_path = Path(src_path)
    dst_path = Path(dst_path)
    
    if not src_path.is_file():
        raise FileNotFoundError(f"Encrypted file not found: {src_path}")
    
    dst_path.parent.mkdir(parents=True, exist_ok=True)
    temp_dst = dst_path.with_name(f"{dst_path.name}.tmp_{os.urandom(4).hex()}")
    
    sha256_hasher = hashlib.sha256()
    restored_size = 0
    
    try:
        with open(src_path, "rb") as fin, open(temp_dst, "wb") as fout:
            # Read and parse header
            header_bytes = fin.read(HEADER_SIZE)
            if len(header_bytes) < HEADER_SIZE:
                raise IntegrityError("Corrupted file: incomplete SecureFolder header.")
            
            magic, version, chunk_size, file_id = HEADER_STRUCT.unpack(header_bytes)
            if magic != FILE_MAGIC:
                raise IntegrityError(f"Invalid magic header: {magic!r}")
            if version != FILE_FORMAT_VERSION:
                raise IntegrityError(f"Unsupported format version: {version}")
            
            file_key = KeyManager.derive_file_key(vault_data_key, file_id)
            aesgcm = AESGCM(file_key)
            
            chunk_index = 0
            has_last = False
            
            while True:
                hdr_bytes = fin.read(CHUNK_HDR_SIZE)
                if not hdr_bytes:
                    if not has_last:
                        raise IntegrityError("Corrupted file: truncated before final chunk.")
                    break
                
                if len(hdr_bytes) < CHUNK_HDR_SIZE:
                    raise IntegrityError("Corrupted chunk header: truncated.")
                
                payload_len, is_last_flag = CHUNK_HDR_STRUCT.unpack(hdr_bytes)
                is_last = (is_last_flag == 1)
                
                nonce = fin.read(NONCE_LEN)
                if len(nonce) < NONCE_LEN:
                    raise IntegrityError(f"Corrupted chunk {chunk_index}: truncated nonce.")
                
                expected_nonce = _build_chunk_nonce(chunk_index)
                if nonce != expected_nonce:
                    raise IntegrityError(f"Corrupted chunk {chunk_index}: nonce mismatch or reordered chunk.")
                
                ciphertext = fin.read(payload_len)
                if len(ciphertext) < payload_len:
                    raise IntegrityError(f"Corrupted chunk {chunk_index}: truncated payload.")
                
                aad = _build_chunk_aad(file_id, version, chunk_index, is_last)
                
                try:
                    plaintext = aesgcm.decrypt(nonce, ciphertext, aad)
                except InvalidTag as e:
                    raise IntegrityError(f"Corrupted chunk {chunk_index}: authentication tag mismatch.") from e
                
                fout.write(plaintext)
                restored_size += len(plaintext)
                sha256_hasher.update(plaintext)
                
                chunk_index += 1
                if is_last:
                    has_last = True
                    # Check for trailing extra bytes
                    extra = fin.read(1)
                    if extra:
                        raise IntegrityError("Corrupted file: trailing data after final chunk.")
                    break
            
            if not has_last:
                raise IntegrityError("Corrupted file: no final chunk marker was found.")
        
        # Atomically move to dst_path
        os.replace(temp_dst, dst_path)
        
        return {
            "restored_size": restored_size,
            "sha256": sha256_hasher.hexdigest(),
            "chunk_count": chunk_index,
        }
    except Exception:
        if temp_dst.exists():
            try:
                temp_dst.unlink()
            except OSError:
                pass
        raise
