# SecureFolder User Manual

**Version 2.0 (Portable Standalone Edition)**  
*Cross-Platform Authenticated Password-Protected Vault*

---

## 1. Introduction & Overview

**SecureFolder** protects your sensitive files and folders by storing them in an encrypted vault. It is designed especially for external hard drives (HDDs/SSDs), USB flash drives, or personal folders across **Windows, Linux, and macOS**.

### Key Concepts

- **The Vault Directory (`my_vault/`)**:
  This is the secured folder containing encrypted objects and metadata. You can safely store, move, or back up this folder. To anyone looking at it without the password:
  - All file contents are encrypted with **AES-256-GCM**.
  - All original file and folder names are hidden inside an encrypted manifest.
  - Files are stored as opaque identifiers (e.g. `obj_a1b2c3d4...enc`).
- **The Unlocked Workspace (`my_vault_unlocked/`)**:
  When you unlock your vault, SecureFolder decrypts your files into a temporary workspace folder. You can open, edit, create, or delete files just like in any normal folder.
- **Locking**:
  When you lock the vault, SecureFolder scans what changed in your workspace, re-encrypts updated or newly added files, deletes removed files from the vault, verifies cryptographic integrity, and securely deletes the unencrypted workspace.

---

## 2. Zero-Prerequisite Standalone Portability

You do **not** need Python installed on foreign computers to unlock and manage your vault.

### Portable Executables for Each Platform
- **Windows**: `secure-folder-windows.exe` (located in `dist/` or copied to drive root as `secure-folder.exe`).
- **Linux**: `secure-folder-linux` (single-file ELF binary).
- **macOS**: `secure-folder-macos` (single-file Mach-O binary).

### Staging Your External Drive Automatically
Run the drive staging utility to copy the executable, convenience double-click launchers, and user manual directly to your external drive (e.g., drive `E:`):
```powershell
python scripts/stage_drive.py E:\
```

This creates the ideal drive layout:
```text
External Drive (E:\)
├── secure-folder.exe          <-- Standalone Windows binary (no Python needed)
├── Unlock_Vault.bat           <-- Double-click to unlock
├── Lock_Vault.bat             <-- Double-click to lock
├── emergency_recover.py       <-- Standalone zero-dependency emergency decrypter
├── my_vault/                  <-- Encrypted vault
└── USER_MANUAL.md             <-- Documentation
```

---

## 3. The "Anti-Lock-In" Guarantee & Emergency Recovery

You are **never locked into this software**. Even if SecureFolder is not installed or the executable cannot be run, your drive carries `emergency_recover.py`:

- **Zero App Dependencies**: A single standalone Python script that directly reads `vault.json`, authenticates with your password, decrypts `manifest.enc`, and restores your files.
- **Open Cryptographic Standards**: Uses standard Scrypt key derivation and AES-256-GCM authenticated encryption.
- **To Recover**:
  ```bash
  python emergency_recover.py my_vault
  ```

---

## 4. Multi-Platform Build Automation (GitHub Actions)

The repository includes a GitHub Actions CI workflow in `.github/workflows/build_binaries.yml` that automatically tests and compiles native standalone binaries for all three major operating systems:
- Windows (`windows-latest`) $\rightarrow$ `secure-folder-windows.exe`
- Linux (`ubuntu-22.04`) $\rightarrow$ `secure-folder-linux`
- macOS (`macos-latest`) $\rightarrow$ `secure-folder-macos`

### Building Binaries Locally:
- **Windows**: Run `scripts\build_windows.bat`
- **Linux**: Run `bash scripts/build_linux.sh`
- **macOS**: Run `bash scripts/build_macos.sh`

---

## 5. Daily Command Reference

You can run commands using `secure-folder.exe <command>` (or `python -m secure_folder.main <command>`):

| Command | Syntax | Description |
| :--- | :--- | :--- |
| `init` | `secure-folder.exe init <vault_dir>` | Initializes a new empty encrypted vault. |
| `status` | `secure-folder.exe status <vault_dir>` | Shows if the vault is `LOCKED` or `UNLOCKED`. |
| `unlock` | `secure-folder.exe unlock <vault_dir> [-w <ws>]` | Decrypts vault contents into an unlocked workspace. |
| `lock` | `secure-folder.exe lock <vault_dir>` | Re-encrypts workspace changes and securely wipes the workspace. |
| `verify` | `secure-folder.exe verify <vault_dir>` | Validates cryptographic authentication tags across all files. |
| `change-password` | `secure-folder.exe change-password <vault_dir>` | Updates master password without re-encrypting data files. |

---

## 6. Safety & Disconnect Protocol

1. **Always Run `lock` Before Disconnecting**:
   Before unplugging your external drive, always run `lock` (or double-click `Lock_Vault.bat`) to re-encrypt modified files, verify integrity, and erase the temporary unencrypted workspace.
2. **Safe Ejection**:
   Use Windows "Safely Remove Hardware and Eject Media" (or macOS/Linux eject) to ensure all disk write caches have flushed to the external hardware.
3. **Emergency Backup**:
   Periodically copy the `my_vault/` folder to a second physical location as an encrypted offline backup.
