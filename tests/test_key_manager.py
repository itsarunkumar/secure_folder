"""Tests for KeyManager."""

import os
import pytest
from secure_folder.core.key_manager import KeyManager
from secure_folder.utils.exceptions import AuthenticationError

def test_kek_derivation_deterministic():
    """Test that the same password and salt produce the exact same KEK."""
    salt = os.urandom(32)
    password = "CorrectHorseBatteryStaple!"
    
    kek1 = KeyManager.derive_kek(password, salt, n=1024, r=8, p=1)
    kek2 = KeyManager.derive_kek(password, salt, n=1024, r=8, p=1)
    assert kek1 == kek2
    assert len(kek1) == 32

def test_kek_different_for_different_passwords():
    salt = os.urandom(32)
    kek1 = KeyManager.derive_kek("password123", salt, n=1024, r=8, p=1)
    kek2 = KeyManager.derive_kek("password124", salt, n=1024, r=8, p=1)
    assert kek1 != kek2

def test_encrypt_decrypt_vdk_roundtrip():
    salt = os.urandom(32)
    password = "SuperSecretPassword123"
    kek = KeyManager.derive_kek(password, salt, n=1024, r=8, p=1)
    
    vdk = KeyManager.generate_data_key()
    assert len(vdk) == 32
    
    encrypted_info = KeyManager.encrypt_data_key(vdk, kek)
    assert "nonce" in encrypted_info
    assert "ciphertext" in encrypted_info
    
    decrypted_vdk = KeyManager.decrypt_data_key(encrypted_info, kek)
    assert decrypted_vdk == vdk

def test_decrypt_vdk_wrong_password():
    salt = os.urandom(32)
    kek_correct = KeyManager.derive_kek("correct_password", salt, n=1024, r=8, p=1)
    kek_wrong = KeyManager.derive_kek("wrong_password", salt, n=1024, r=8, p=1)
    
    vdk = KeyManager.generate_data_key()
    encrypted_info = KeyManager.encrypt_data_key(vdk, kek_correct)
    
    with pytest.raises(AuthenticationError):
        KeyManager.decrypt_data_key(encrypted_info, kek_wrong)

def test_derive_file_key():
    vdk = KeyManager.generate_data_key()
    file_id_1 = os.urandom(16)
    file_id_2 = os.urandom(16)
    
    k1 = KeyManager.derive_file_key(vdk, file_id_1)
    k2 = KeyManager.derive_file_key(vdk, file_id_2)
    
    assert len(k1) == 32
    assert len(k2) == 32
    assert k1 != k2
