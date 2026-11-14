"""Key derivation and management for SecureFolder."""

import os
from typing import Dict, Any, Tuple
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.exceptions import InvalidTag

from secure_folder.utils.constants import (
    KEY_LEN,
    NONCE_LEN,
    SCRYPT_SALT_LEN,
    SCRYPT_N,
    SCRYPT_R,
    SCRYPT_P,
)
from secure_folder.utils.exceptions import AuthenticationError

VDK_ASSOCIATED_DATA = b"SecureFolder-VDK-v1"
HKDF_INFO = b"SecureFolder-FileKey-v1"

class KeyManager:
    """Manages password-based key derivation, vault data keys, and per-file keys."""

    @staticmethod
    def derive_kek(
        password: str,
        salt: bytes,
        n: int = SCRYPT_N,
        r: int = SCRYPT_R,
        p: int = SCRYPT_P,
    ) -> bytes:
        """Derives a 256-bit Key Encryption Key (KEK) from password using Scrypt."""
        kdf = Scrypt(
            salt=salt,
            length=KEY_LEN,
            n=n,
            r=r,
            p=p,
        )
        return kdf.derive(password.encode("utf-8"))

    @staticmethod
    def generate_data_key() -> bytes:
        """Generates a random 256-bit Vault Data Key (VDK)."""
        return os.urandom(KEY_LEN)

    @staticmethod
    def encrypt_data_key(data_key: bytes, kek: bytes) -> Dict[str, Any]:
        """Encrypts the Vault Data Key with KEK using AES-256-GCM."""
        nonce = os.urandom(NONCE_LEN)
        aesgcm = AESGCM(kek)
        # AESGCM.encrypt returns ciphertext + 16-byte tag
        ciphertext = aesgcm.encrypt(nonce, data_key, VDK_ASSOCIATED_DATA)
        return {
            "nonce": nonce.hex(),
            "ciphertext": ciphertext.hex(),
        }

    @staticmethod
    def decrypt_data_key(encrypted_info: Dict[str, Any], kek: bytes) -> bytes:
        """Decrypts the Vault Data Key with KEK. Raises AuthenticationError on invalid password/tag."""
        try:
            nonce = bytes.fromhex(encrypted_info["nonce"])
            ciphertext = bytes.fromhex(encrypted_info["ciphertext"])
            aesgcm = AESGCM(kek)
            data_key = aesgcm.decrypt(nonce, ciphertext, VDK_ASSOCIATED_DATA)
            return data_key
        except (InvalidTag, ValueError, KeyError) as e:
            raise AuthenticationError("Invalid password or corrupted vault key.") from e

    @staticmethod
    def derive_file_key(vault_data_key: bytes, file_id: bytes) -> bytes:
        """Derives a distinct 256-bit AES key for a specific file using HKDF-SHA256."""
        hkdf = HKDF(
            algorithm=hashes.SHA256(),
            length=KEY_LEN,
            salt=file_id,
            info=HKDF_INFO,
        )
        return hkdf.derive(vault_data_key)
