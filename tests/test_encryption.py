"""Tests for encryption engine (Milestone M1)."""

import os
import hashlib
import pytest
from pathlib import Path

from secure_folder.core.encryption import (
    encrypt_file,
    decrypt_file,
    encrypt_bytes,
    decrypt_bytes,
)
from secure_folder.core.key_manager import KeyManager
from secure_folder.utils.exceptions import IntegrityError

@pytest.fixture
def data_key():
    return KeyManager.generate_data_key()

def test_encrypt_decrypt_bytes(data_key):
    """Test in-memory encrypt_bytes and decrypt_bytes."""
    data = b"Hello, SecureFolder world! Testing authenticated encryption."
    aad = b"associated-data-context"
    
    ciphertext = encrypt_bytes(data, data_key, associated_data=aad)
    assert ciphertext != data
    
    decrypted = decrypt_bytes(ciphertext, data_key, associated_data=aad)
    assert decrypted == data
    
    # Test wrong key
    wrong_key = KeyManager.generate_data_key()
    with pytest.raises(IntegrityError):
        decrypt_bytes(ciphertext, wrong_key, associated_data=aad)
    
    # Test wrong AAD
    with pytest.raises(IntegrityError):
        decrypt_bytes(ciphertext, data_key, associated_data=b"wrong-aad")
    
    # Test tampering
    corrupted = bytearray(ciphertext)
    corrupted[-1] ^= 0x01
    with pytest.raises(IntegrityError):
        decrypt_bytes(bytes(corrupted), data_key, associated_data=aad)

@pytest.mark.parametrize("file_size,chunk_size", [
    (0, 1024),            # Empty file
    (100, 1024),          # Sub-chunk file
    (1024, 1024),         # Exact chunk boundary
    (3000, 1024),         # Multi-chunk file (3 chunks)
    (1024 * 64, 16384),   # 64 KiB with 16 KiB chunks (4 chunks)
])
def test_file_encryption_roundtrip(tmp_path, data_key, file_size, chunk_size):
    """M1 Core Test: Read source file, encrypt without compression, decrypt, check SHA-256 match."""
    src_file = tmp_path / "original.dat"
    enc_file = tmp_path / "encrypted.dat"
    dec_file = tmp_path / "restored.dat"
    
    # Generate random bytes for realistic test data
    content = os.urandom(file_size)
    src_file.write_bytes(content)
    expected_sha256 = hashlib.sha256(content).hexdigest()
    
    # Encrypt
    enc_meta = encrypt_file(src_file, enc_file, data_key, chunk_size=chunk_size)
    assert enc_file.exists()
    assert enc_meta["original_size"] == file_size
    assert enc_meta["sha256"] == expected_sha256
    
    # Ensure source file is untouched
    assert src_file.read_bytes() == content
    
    # Decrypt
    dec_meta = decrypt_file(enc_file, dec_file, data_key)
    assert dec_file.exists()
    assert dec_meta["restored_size"] == file_size
    assert dec_meta["sha256"] == expected_sha256
    
    # Byte-for-byte identity check
    assert dec_file.read_bytes() == content

def test_tampered_ciphertext_detected(tmp_path, data_key):
    """Integrity test: modifying any byte of ciphertext must fail decryption."""
    src_file = tmp_path / "original.dat"
    enc_file = tmp_path / "encrypted.dat"
    dec_file = tmp_path / "restored.dat"
    
    content = b"Critical confidential content that must not be modified."
    src_file.write_bytes(content)
    
    encrypt_file(src_file, enc_file, data_key, chunk_size=64)
    
    # Read and flip a byte near the end (in ciphertext or tag)
    enc_data = bytearray(enc_file.read_bytes())
    enc_data[-1] ^= 0xFF
    enc_file.write_bytes(enc_data)
    
    with pytest.raises(IntegrityError):
        decrypt_file(enc_file, dec_file, data_key)
    
    # Ensure no partial or corrupted file was left
    assert not dec_file.exists()

def test_truncated_file_detected(tmp_path, data_key):
    """Integrity test: truncated file must fail decryption."""
    src_file = tmp_path / "original.dat"
    enc_file = tmp_path / "encrypted.dat"
    dec_file = tmp_path / "restored.dat"
    
    content = os.urandom(10000)
    src_file.write_bytes(content)
    
    encrypt_file(src_file, enc_file, data_key, chunk_size=1024)
    
    # Truncate by dropping last 50 bytes
    enc_data = enc_file.read_bytes()
    enc_file.write_bytes(enc_data[:-50])
    
    with pytest.raises(IntegrityError):
        decrypt_file(enc_file, dec_file, data_key)
    assert not dec_file.exists()

def test_wrong_key_rejected(tmp_path, data_key):
    """Security test: decrypting with a wrong key must raise IntegrityError."""
    src_file = tmp_path / "original.dat"
    enc_file = tmp_path / "encrypted.dat"
    dec_file = tmp_path / "restored.dat"
    
    src_file.write_bytes(b"Secret data")
    encrypt_file(src_file, enc_file, data_key)
    
    wrong_key = KeyManager.generate_data_key()
    with pytest.raises(IntegrityError):
        decrypt_file(enc_file, dec_file, wrong_key)
    assert not dec_file.exists()
