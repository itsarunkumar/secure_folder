# SecureFolder User Manual

**Version 2.0 (Zero-Block Portable Edition)**  
*Cross-Platform Authenticated Password-Protected Vault*

---

## 1. Introduction & Overview

**SecureFolder** protects your sensitive files and folders by storing them in an encrypted vault. It is designed especially for external hard drives (HDDs/SSDs), USB flash drives, or personal folders across **Windows, Linux, and macOS**.

### Key Concepts

- **The Vault Directory (`my_vault/`)**:
  The secured folder containing encrypted objects and metadata:
  - All file contents are encrypted with **AES-256-GCM**.
  - All original file and folder names are hidden inside an encrypted manifest (`manifest.enc`).
  - Files are stored as opaque identifiers (`obj_a1b2c3d4...enc`).
- **The Unlocked Workspace (`my_vault_unlocked/`)**:
  When you unlock your vault, SecureFolder decrypts your files into a temporary workspace folder. You can open, edit, create, or delete files just like in any normal folder.
- **Locking**:
  When you lock the vault, SecureFolder scans what changed in your workspace, re-encrypts updated or newly added files, deletes removed files from the vault, verifies cryptographic integrity, and securely deletes the unencrypted workspace.

---

## 2. Zero-Block Portable Drive (Immune to Windows 11 Smart App Control)

Windows 11 features **Smart App Control (SAC)**, which blocks newly compiled or unsigned `.exe` files. 

To ensure your external drive runs on **any Windows PC without ever being blocked**:
The external drive carries **Microsoft's officially signed portable Python runtime** inside `SecureFolder/python/`. Because `python.exe` is digitally signed by Microsoft Corporation / Python Software Foundation, Smart App Control **never blocks it**.

### Drive Contents Layout:
```text
External Hard Drive Root (e.g., E:\)
├── Unlock_Vault.bat           <-- Double-click to unlock your vault
├── Lock_Vault.bat             <-- Double-click to lock your vault
├── Status_Vault.bat           <-- Double-click to check status
├── Verify_Vault.bat           <-- Double-click to verify file integrity
├── emergency_recover.py       <-- Standalone zero-dependency emergency decrypter
├── SecureFolder/              <-- Self-contained signed runtime & engine
│   ├── python/                <-- Official Microsoft-signed Python 3.11 runtime
│   └── src/                   <-- SecureFolder source code
├── my_vault/                  <-- Encrypted vault
└── USER_MANUAL.md             <-- Documentation
```

### Staging to an External Hard Drive:
To deploy the ready-to-run bundle directly onto a flash drive or external HDD (e.g. drive `E:`):
```powershell
python scripts/stage_drive.py E:\
```
*(Or simply drag and drop the files inside `dist/portable_bundle/` to your drive).*

---

## 3. Daily Usage with 1-Click Launchers

No terminal commands needed on the drive:

1. **To Unlock**:
   Double-click **`Unlock_Vault.bat`** on the drive. Enter your password. Your files appear in `my_vault_unlocked/`.
2. **To Work**:
   Open, edit, create, or delete files inside `my_vault_unlocked/` normally.
3. **To Lock**:
   Double-click **`Lock_Vault.bat`** on the drive. Enter your password. Changes are re-encrypted, integrity is verified, and the plaintext workspace is safely removed.

---

## 4. The "Anti-Lock-In" Guarantee & Emergency Recovery

You are **never locked into this software**. Even if the SecureFolder launcher is deleted:
- Your drive carries **`emergency_recover.py`**, a single standalone script with zero app dependencies that can decrypt any vault on any machine with Python:
  ```bash
  python emergency_recover.py my_vault
  ```

---

## 5. Command Reference (Terminal / Advanced)

If running directly from terminal:
```bash
# Using bundled signed python:
.\SecureFolder\python\python.exe -m secure_folder.main <command> my_vault

# Or using system python:
python -m secure_folder.main <command> my_vault
```

| Command | Syntax | Description |
| :--- | :--- | :--- |
| `init` | `... init <vault_dir>` | Initializes a new empty encrypted vault. |
| `status` | `... status <vault_dir>` | Shows if the vault is `LOCKED` or `UNLOCKED`. |
| `unlock` | `... unlock <vault_dir> [-w <ws>]` | Decrypts vault contents into an unlocked workspace. |
| `lock` | `... lock <vault_dir>` | Re-encrypts workspace changes and securely wipes the workspace. |
| `verify` | `... verify <vault_dir>` | Validates cryptographic authentication tags across all files. |
| `change-password` | `... change-password <vault_dir>` | Updates master password without re-encrypting data files. |

---

## 6. Safety & Disconnect Protocol

1. **Always Run `Lock_Vault.bat` Before Disconnecting**:
   Before unplugging your external drive, always lock the vault to ensure changes are encrypted and temporary files are cleared.
2. **Safely Remove Hardware**:
   Use Windows "Safely Remove Hardware" before unplugging to prevent physical file corruption.
