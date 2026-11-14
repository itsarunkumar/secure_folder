#!/usr/bin/env python3
"""
SecureFolder Emergency Recovery Script (Standalone - Zero App Dependencies)
-------------------------------------------------------------------------
This single-file utility allows anyone to decrypt and recover their files
from a SecureFolder vault without requiring the main SecureFolder application.
It only requires standard Python 3.9+ with the 'cryptography' library.

Usage:
    python emergency_recover.py /path/to/my_vault [/path/to/output_folder]
"""

import sys
import os
import json
import struct
import getpass
import hashlib
from pathlib import Path

try:
    from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
    from cryptography.hazmat.primitives.kdf.hkdf import HKDF
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.exceptions import InvalidTag
except ImportError:
    print("Error: The 'cryptography' library is required to run emergency recovery.")
    print("Install it with: pip install cryptography")
    sys.exit(1)

# Wire constants
FILE_MAGIC = b"SECF"
HEADER_STRUCT = struct.Struct(">4sHI16s")
CHUNK_HDR_STRUCT = struct.Struct(">IB")
VDK_AAD = b"SecureFolder-VDK-v1"
MANIFEST_AAD = b"SecureFolder-Manifest-v1"
HKDF_INFO = b"SecureFolder-FileKey-v1"

def derive_kek(password: str, salt: bytes, n: int, r: int, p: int) -> bytes:
    kdf = Scrypt(salt=salt, length=32, n=n, r=r, p=p)
    return kdf.derive(password.encode("utf-8"))

def decrypt_vdk(config_data: dict, kek: bytes) -> bytes:
    enc_info = config_data["encrypted_key"]
    nonce = bytes.fromhex(enc_info["nonce"])
    ciphertext = bytes.fromhex(enc_info["ciphertext"])
    aesgcm = AESGCM(kek)
    return aesgcm.decrypt(nonce, ciphertext, VDK_AAD)

def decrypt_manifest(vault_dir: Path, vdk: bytes) -> dict:
    manifest_file = vault_dir / "manifest.enc"
    data = manifest_file.read_bytes()
    nonce = data[:12]
    ciphertext = data[12:]
    aesgcm = AESGCM(vdk)
    raw_json = aesgcm.decrypt(nonce, ciphertext, MANIFEST_AAD)
    return json.loads(raw_json.decode("utf-8"))

def decrypt_file_object(enc_path: Path, dst_path: Path, vdk: bytes) -> bool:
    dst_path.parent.mkdir(parents=True, exist_ok=True)
    with open(enc_path, "rb") as fin, open(dst_path, "wb") as fout:
        header_bytes = fin.read(HEADER_STRUCT.size)
        magic, version, chunk_size, file_id = HEADER_STRUCT.unpack(header_bytes)
        if magic != FILE_MAGIC:
            raise ValueError(f"Invalid magic: {magic}")

        # Derive file key using HKDF
        hkdf = HKDF(algorithm=hashes.SHA256(), length=32, salt=file_id, info=HKDF_INFO)
        file_key = hkdf.derive(vdk)
        aesgcm = AESGCM(file_key)

        chunk_idx = 0
        while True:
            hdr_bytes = fin.read(CHUNK_HDR_STRUCT.size)
            if not hdr_bytes:
                break
            payload_len, is_last_flag = CHUNK_HDR_STRUCT.unpack(hdr_bytes)
            is_last = (is_last_flag == 1)
            nonce = fin.read(12)
            ciphertext = fin.read(payload_len)
            aad = FILE_MAGIC + version.to_bytes(2, "big") + file_id + chunk_idx.to_bytes(4, "big") + (b"\x01" if is_last else b"\x00")
            plaintext = aesgcm.decrypt(nonce, ciphertext, aad)
            fout.write(plaintext)
            chunk_idx += 1
            if is_last:
                break
    return True

def main():
    print("==================================================")
    print("SecureFolder Standalone Emergency Recovery Tool")
    print("==================================================")

    if len(sys.argv) < 2:
        vault_input = input("Enter path to your vault directory: ").strip()
    else:
        vault_input = sys.argv[1]

    vault_dir = Path(vault_input).resolve()
    config_file = vault_dir / "vault.json"

    if not config_file.is_file():
        print(f"Error: No vault configuration found at: {config_file}")
        sys.exit(1)

    password = getpass.getpass("Enter master password: ")

    try:
        config_data = json.loads(config_file.read_text(encoding="utf-8"))
        kdf_info = config_data["kdf"]
        salt = bytes.fromhex(kdf_info["salt"])
        kek = derive_kek(password, salt, kdf_info["n"], kdf_info["r"], kdf_info["p"])
        vdk = decrypt_vdk(config_data, kek)
        print("[+] Authentication successful!")
    except Exception as e:
        print(f"[-] Authentication failed: Invalid password or corrupted vault ({e})")
        sys.exit(1)

    try:
        manifest_data = decrypt_manifest(vault_dir, vdk)
        entries = manifest_data.get("entries", {})
        print(f"[+] Decrypted manifest. Found {len(entries)} file/folder entries.")
    except Exception as e:
        print(f"[-] Failed to decrypt manifest: {e}")
        sys.exit(1)

    if len(sys.argv) >= 3:
        out_dir = Path(sys.argv[2]).resolve()
    else:
        out_dir = vault_dir.parent / f"{vault_dir.name}_recovered"

    print(f"[*] Recovering files to: {out_dir}")
    out_dir.mkdir(parents=True, exist_ok=True)

    objects_dir = vault_dir / "objects"
    recovered_count = 0

    for rel_path, meta in entries.items():
        if meta.get("type") == "file":
            obj_id = meta["object_id"]
            enc_path = objects_dir / obj_id
            dst_path = out_dir / rel_path
            if not enc_path.exists():
                print(f"[!] Warning: Missing object {obj_id} for {rel_path}")
                continue
            try:
                decrypt_file_object(enc_path, dst_path, vdk)
                recovered_count += 1
                print(f"  [OK] Restored: {rel_path}")
            except Exception as e:
                print(f"  [FAIL] Error restoring {rel_path}: {e}")
        elif meta.get("type") == "directory":
            (out_dir / rel_path).mkdir(parents=True, exist_ok=True)

    print(f"\n==================================================")
    print(f"[+] Recovery complete! Restored {recovered_count} files.")
    print(f"Location: {out_dir}")
    print(f"==================================================")

if __name__ == "__main__":
    main()
