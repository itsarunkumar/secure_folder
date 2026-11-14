# SecureFolder User Manual

**Version 1.0**  
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

## 2. Using on External Hard Drives & Moving Between Systems

One of the core design goals of SecureFolder is **100% portability** across different machines. You can keep your vault and the utility directly on an external hard drive and unlock it on any system.

### Why It Works Across Different Computers

1. **Drive Letter Independence**:
   SecureFolder uses relative POSIX paths internally. It does not hardcode drive letters (`C:`, `D:`, `E:`). If your drive mounts as `D:` on your desktop and `F:` on your laptop, the vault unlocks seamlessly.
2. **Independent Storage**:
   The vault is just one folder on your external drive. All other unencrypted files, movies, documents, or games on the drive remain untouched and completely independent.
3. **Cross-Platform Cryptography**:
   Scrypt and AES-256-GCM are standardized cryptographic algorithms that run identically on Windows, Linux, and macOS.

### Recommended Hard Drive Layout

```text
External Hard Drive (e.g., E:\)
├── SecureFolder/                 <-- Utility codebase or standalone executable
│   ├── src/
│   ├── scripts/
│   └── ...
├── my_vault/                     <-- Encrypted vault (leave here permanently)
│   ├── vault.json
│   ├── manifest.enc
│   └── objects/
└── Other Normal Files/           <-- Regular drive files remain untouched
```

### Unlocking on Another Computer

#### Option A: If the target computer has Python installed
Open a terminal on the drive and run:
```bash
python -m secure_folder.main unlock my_vault
```
Or run the platform-specific launcher script from the `scripts/` folder:
- **Windows**: Double-click or run `scripts\run_windows.bat unlock my_vault`
- **Linux**: Run `./scripts/run_linux.sh unlock my_vault`
- **macOS**: Run `./scripts/run_macos.command unlock my_vault`

#### Option B: If the target computer does NOT have Python installed
You can package SecureFolder into a standalone executable (e.g. `secure-folder.exe`) using PyInstaller:
- Keep `secure-folder.exe` on the external drive.
- Plug into any Windows computer and run:
  ```cmd
  secure-folder.exe unlock my_vault
  ```
  Zero installation or setup required.

---

## 3. Step-by-Step Daily Workflow

### Step 1: Initialize a New Vault
Create a vault named `personal_vault` on your drive:
```powershell
python -m secure_folder.main init personal_vault
```
You will be prompted to enter and confirm a master password.

### Step 2: Check Vault Status
To inspect whether a vault is currently locked or unlocked:
```powershell
python -m secure_folder.main status personal_vault
```

### Step 3: Unlock Your Files
When you need to work on your private documents:
```powershell
python -m secure_folder.main unlock personal_vault
```
- Enter your master password when prompted.
- Your files will be decrypted into `personal_vault_unlocked/`.
- Open `personal_vault_unlocked/` in File Explorer or your editor and work normally.

### Step 4: Lock and Secure Your Files
Once you finish editing or adding files:
```powershell
python -m secure_folder.main lock personal_vault
```
- Enter your password to authenticate.
- SecureFolder detects added, modified, or deleted files, encrypts changes, updates the manifest, verifies integrity, and securely wipes the `personal_vault_unlocked` folder.

---

## 4. Command Reference

All commands use the syntax: `python -m secure_folder.main <command> [options]` (or `secure-folder.exe <command>` if using the standalone binary).

| Command | Syntax | Description |
| :--- | :--- | :--- |
| `init` | `python -m secure_folder.main init <vault_dir>` | Initializes a new empty encrypted vault. |
| `status` | `python -m secure_folder.main status <vault_dir>` | Shows if the vault is `LOCKED` or `UNLOCKED` without needing a password. |
| `unlock` | `python -m secure_folder.main unlock <vault_dir> [-w <workspace>]` | Decrypts vault contents into an unlocked workspace folder. |
| `lock` | `python -m secure_folder.main lock <vault_dir>` | Encrypts workspace changes back into the vault and deletes the workspace. |
| `verify` | `python -m secure_folder.main verify <vault_dir>` | Validates cryptographic authentication tags across all objects to detect corruption. |
| `change-password` | `python -m secure_folder.main change-password <vault_dir>` | Updates master password without needing to re-encrypt data files. |

---

## 5. Advanced Options & Workflows

### Custom Workspace Path
By default, unlocking creates `<vault_dir>_unlocked`. You can specify a custom working folder using `-w` or `--workspace`:
```powershell
python -m secure_folder.main unlock personal_vault -w "D:\working_folder"
```
When locking, SecureFolder automatically remembers the active workspace from configuration.

### Non-Interactive & Automated Scripting
You can supply the password directly via CLI argument or environment variable:
- **Command flag:**
  ```powershell
  python -m secure_folder.main unlock personal_vault --password "MySecretPass"
  ```
- **Environment variable (`SECURE_FOLDER_PASSWORD`):**
  ```powershell
  $env:SECURE_FOLDER_PASSWORD="MySecretPass"
  python -m secure_folder.main unlock personal_vault
  ```

### Verifying Vault Health
To verify that no files on your external drive have suffered silent bit rot, drive failure, or tampering:
```powershell
python -m secure_folder.main verify personal_vault
```
This inspects all authentication tags chunk-by-chunk without needing to extract files to disk.

### Instant Password Change
If you want to update your master password, SecureFolder uses key wrapping (Scrypt KEK wraps the random Vault Data Key). Changing the password takes only a second and never re-encrypts your actual data files:
```powershell
python -m secure_folder.main change-password personal_vault
```

---

## 6. Security & Safety Rules

1. **Always Lock Before Unplugging**:
   Before disconnecting an external hard drive, always run `lock` to ensure all changes are committed, authenticated, and that the unencrypted workspace is cleaned. Then use the OS "Safely Remove Hardware" option.
2. **Keep Independent Backups**:
   The vault protects your data from unauthorized access, but if your hard drive suffers physical hardware damage or you forget your master password, encrypted data cannot be recovered. Keep a backup copy of your vault folder in a secondary location.
3. **Never Edit Files Inside `objects/` Directly**:
   Do not rename or alter files inside `personal_vault/objects/` or modify `manifest.enc`. SecureFolder uses authenticated encryption; altering even a single bit will trigger tamper detection.

---

## 7. Troubleshooting

- **Error: `Invalid password or corrupted vault key`**:
  Make sure you entered the correct password (passwords are case-sensitive).
- **Error: `Corrupted chunk: authentication tag mismatch`**:
  An encrypted file was tampered with, truncated, or suffered disk corruption. Run `verify` to identify which file is affected.
- **Workspace not removed on lock**:
  If re-encryption or integrity validation fails during `lock`, SecureFolder deliberately keeps your workspace untouched to prevent any loss of your modified work.
- **Drive letter changed between computers**:
  This is expected and fully supported. SecureFolder does not rely on drive letters—just pass the relative or absolute path on the current machine (e.g., `E:\personal_vault`).
