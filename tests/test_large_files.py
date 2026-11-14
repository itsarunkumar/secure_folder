"""Tests for large file streaming and bounded memory processing."""

import os
import hashlib
import pytest
from pathlib import Path
from secure_folder.core.encryption import encrypt_file, decrypt_file
from secure_folder.core.key_manager import KeyManager

def test_stream_multi_chunk_file(tmp_path):
    """Encrypt and decrypt a multi-chunk file (5 MB with 1 MB chunks) to verify streaming."""
    vault_data_key = KeyManager.generate_data_key()
    
    src = tmp_path / "large_file.bin"
    enc = tmp_path / "large_file.enc"
    dec = tmp_path / "large_file_restored.bin"
    
    # Generate 5 MB of structured test data
    chunk_1mb = os.urandom(1024 * 1024)
    hasher = hashlib.sha256()
    with open(src, "wb") as f:
        for _ in range(5):
            f.write(chunk_1mb)
            hasher.update(chunk_1mb)
    expected_sha256 = hasher.hexdigest()
    
    # Encrypt with 1 MB chunks
    enc_stats = encrypt_file(src, enc, vault_data_key, chunk_size=1024 * 1024)
    assert enc_stats["original_size"] == 5 * 1024 * 1024
    assert enc_stats["chunk_count"] == 5
    assert enc_stats["sha256"] == expected_sha256
    
    # Decrypt
    dec_stats = decrypt_file(enc, dec, vault_data_key)
    assert dec_stats["restored_size"] == 5 * 1024 * 1024
    assert dec_stats["chunk_count"] == 5
    assert dec_stats["sha256"] == expected_sha256
    
    # Verify hash of restored file on disk
    restored_hasher = hashlib.sha256()
    with open(dec, "rb") as f:
        while True:
            chunk = f.read(1024 * 1024)
            if not chunk:
                break
            restored_hasher.update(chunk)
    assert restored_hasher.hexdigest() == expected_sha256
