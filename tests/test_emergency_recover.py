"""Integration test for standalone emergency_recover.py."""

import json
import pytest
from pathlib import Path

from secure_folder.core.vault import Vault
from emergency_recover import derive_kek, decrypt_vdk, decrypt_manifest, decrypt_file_object

PASSWORD = "EmergencyPassword999!"

def test_emergency_recovery_flow(tmp_path):
    vault_dir = tmp_path / "em_vault"
    ws_dir = tmp_path / "em_ws"
    out_dir = tmp_path / "em_recovered"
    
    # 1. Create and populate vault
    Vault.init_vault(vault_dir, PASSWORD)
    Vault.unlock(vault_dir, PASSWORD, target_workspace=ws_dir)
    
    (ws_dir / "nested").mkdir()
    (ws_dir / "note.txt").write_text("Crucial emergency note")
    (ws_dir / "nested" / "data.bin").write_bytes(b"\xde\xad\xbe\xef" * 1024)
    
    Vault.lock(vault_dir, PASSWORD)
    
    # 2. Authenticate and decrypt using emergency_recover standalone logic
    config_data = json.loads((vault_dir / "vault.json").read_text(encoding="utf-8"))
    kdf_info = config_data["kdf"]
    salt = bytes.fromhex(kdf_info["salt"])
    
    kek = derive_kek(PASSWORD, salt, kdf_info["n"], kdf_info["r"], kdf_info["p"])
    vdk = decrypt_vdk(config_data, kek)
    assert len(vdk) == 32
    
    manifest_data = decrypt_manifest(vault_dir, vdk)
    entries = manifest_data["entries"]
    assert "note.txt" in entries
    assert "nested/data.bin" in entries
    
    # 3. Recover files
    for rel_path, meta in entries.items():
        if meta["type"] == "file":
            enc_path = vault_dir / "objects" / meta["object_id"]
            dst_path = out_dir / rel_path
            decrypt_file_object(enc_path, dst_path, vdk)
            
    assert (out_dir / "note.txt").read_text() == "Crucial emergency note"
    assert (out_dir / "nested" / "data.bin").read_bytes() == b"\xde\xad\xbe\xef" * 1024
