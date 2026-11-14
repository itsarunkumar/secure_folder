"""Integration tests for Vault lifecycle (Milestones M2, M3, M4, M5)."""

import os
import hashlib
import pytest
from pathlib import Path

from secure_folder.core.vault import Vault
from secure_folder.utils.exceptions import AuthenticationError, IntegrityError, VaultCorruptedError

PASSWORD = "TestMasterPassword123!"

def test_vault_init_and_status(tmp_path):
    vault_dir = tmp_path / "my_vault"
    Vault.init_vault(vault_dir, PASSWORD)
    
    status = Vault.get_status(vault_dir)
    assert status["exists"] is True
    assert status["status"] == "locked"
    assert status["workspace"] is None

def test_vault_wrong_password_rejected(tmp_path):
    vault_dir = tmp_path / "my_vault"
    Vault.init_vault(vault_dir, PASSWORD)
    
    with pytest.raises(AuthenticationError):
        Vault.authenticate(vault_dir, "WrongPassword!")

def test_vault_lock_unlock_workflow(tmp_path):
    """Tests complete workflow: init -> unlock -> populate files -> lock -> unlock -> verify bytes."""
    vault_dir = tmp_path / "secure_vault"
    Vault.init_vault(vault_dir, PASSWORD)
    
    # 1. Unlock into workspace
    ws_dir = tmp_path / "unlocked_workspace"
    Vault.unlock(vault_dir, PASSWORD, target_workspace=ws_dir)
    assert ws_dir.exists()
    assert Vault.get_status(vault_dir)["status"] == "unlocked"
    
    # 2. Add files and nested directories
    doc_dir = ws_dir / "documents" / "finance"
    doc_dir.mkdir(parents=True, exist_ok=True)
    
    file1 = ws_dir / "root_note.txt"
    file1.write_text("Top secret root notes", encoding="utf-8")
    
    file2 = doc_dir / "tax_2026.pdf"
    file2_data = os.urandom(64 * 1024)  # 64 KB random binary
    file2.write_bytes(file2_data)
    
    file2_sha256 = hashlib.sha256(file2_data).hexdigest()
    
    # 3. Lock vault
    lock_stats = Vault.lock(vault_dir, PASSWORD)
    assert lock_stats["added"] == 2
    assert not ws_dir.exists()  # Workspace cleaned up
    assert Vault.get_status(vault_dir)["status"] == "locked"
    
    # 4. Verify that plaintext filenames are NOT in objects/
    objects_dir = vault_dir / "objects"
    object_names = [p.name for p in objects_dir.iterdir()]
    assert len(object_names) == 2
    for obj_name in object_names:
        assert "root_note" not in obj_name
        assert "tax" not in obj_name
        assert obj_name.startswith("obj_")
        assert obj_name.endswith(".enc")
    
    # 5. Unlock again and verify byte-for-byte exactness
    new_ws_dir = tmp_path / "new_workspace"
    Vault.unlock(vault_dir, PASSWORD, target_workspace=new_ws_dir)
    
    restored_file1 = new_ws_dir / "root_note.txt"
    restored_file2 = new_ws_dir / "documents" / "finance" / "tax_2026.pdf"
    
    assert restored_file1.exists()
    assert restored_file1.read_text(encoding="utf-8") == "Top secret root notes"
    
    assert restored_file2.exists()
    assert hashlib.sha256(restored_file2.read_bytes()).hexdigest() == file2_sha256

def test_vault_modify_add_delete_sync(tmp_path):
    """Tests modifying an existing file, adding a new one, deleting an old one."""
    vault_dir = tmp_path / "secure_vault"
    Vault.init_vault(vault_dir, PASSWORD)
    
    ws_dir = tmp_path / "ws"
    Vault.unlock(vault_dir, PASSWORD, target_workspace=ws_dir)
    
    f_keep = ws_dir / "keep.txt"
    f_modify = ws_dir / "modify.txt"
    f_delete = ws_dir / "delete.txt"
    
    f_keep.write_text("keep me")
    f_modify.write_text("original content")
    f_delete.write_text("delete me soon")
    
    Vault.lock(vault_dir, PASSWORD)
    
    # Unlock again and make modifications
    Vault.unlock(vault_dir, PASSWORD, target_workspace=ws_dir)
    
    # Modify
    f_modify.write_text("UPDATED CONTENT!")
    # Delete
    f_delete.unlink()
    # Add
    f_new = ws_dir / "brand_new.txt"
    f_new.write_text("newly added")
    
    lock_stats = Vault.lock(vault_dir, PASSWORD)
    assert lock_stats["added"] == 1
    assert lock_stats["modified"] == 1
    assert lock_stats["deleted"] == 1
    assert lock_stats["unchanged"] == 1
    
    # Unlock and verify final state
    Vault.unlock(vault_dir, PASSWORD, target_workspace=ws_dir)
    assert (ws_dir / "keep.txt").read_text() == "keep me"
    assert (ws_dir / "modify.txt").read_text() == "UPDATED CONTENT!"
    assert (ws_dir / "brand_new.txt").read_text() == "newly added"
    assert not (ws_dir / "delete.txt").exists()

def test_vault_change_password(tmp_path):
    vault_dir = tmp_path / "vault_pwd"
    Vault.init_vault(vault_dir, "OldPassword123!")
    
    ws_dir = tmp_path / "ws"
    Vault.unlock(vault_dir, "OldPassword123!", target_workspace=ws_dir)
    (ws_dir / "secret.txt").write_text("secret information")
    Vault.lock(vault_dir, "OldPassword123!")
    
    # Change password
    NEW_PASSWORD = "NewPassword456!@"
    Vault.change_password(vault_dir, "OldPassword123!", NEW_PASSWORD)
    
    # Old password must fail
    with pytest.raises(AuthenticationError):
        Vault.unlock(vault_dir, "OldPassword123!", target_workspace=ws_dir)
    
    # New password must succeed
    Vault.unlock(vault_dir, NEW_PASSWORD, target_workspace=ws_dir)
    assert (ws_dir / "secret.txt").read_text() == "secret information"

def test_vault_integrity_and_corruption_detection(tmp_path):
    vault_dir = tmp_path / "vault_int"
    Vault.init_vault(vault_dir, PASSWORD)
    
    ws_dir = tmp_path / "ws"
    Vault.unlock(vault_dir, PASSWORD, target_workspace=ws_dir)
    (ws_dir / "file.txt").write_text("integrity test")
    Vault.lock(vault_dir, PASSWORD)
    
    # Check healthy
    report = Vault.verify(vault_dir, PASSWORD)
    assert report["healthy"] is True
    assert report["total_files"] == 1
    
    # Corrupt an object in objects/
    objects = list((vault_dir / "objects").glob("*.enc"))
    assert len(objects) == 1
    enc_data = bytearray(objects[0].read_bytes())
    enc_data[-1] ^= 0x01
    objects[0].write_bytes(enc_data)
    
    # Verify should now report unhealthy and detect corrupted file
    report_bad = Vault.verify(vault_dir, PASSWORD)
    assert report_bad["healthy"] is False
    assert len(report_bad["corrupted_files"]) == 1
    assert "file.txt" in report_bad["corrupted_files"]
