# SecureFolder

**Cross-platform password-protected folder utility (Version 1.0)**

SecureFolder is a lightweight, portable utility that creates and manages password-protected encrypted vaults directly on local or external storage devices without encrypting the entire drive.

## Key Features

- **Authenticated Encryption**: Uses AES-256-GCM with independently authenticated chunks and unique nonces.
- **Key Separation**: Password derives a Key-Encryption Key (KEK) using Scrypt (`N=32768, r=8, p=1`). A random 256-bit Vault Data Key (VDK) is generated and encrypted with the KEK. Per-file keys are derived using HKDF-SHA256.
- **Hidden Structure & Names**: File and directory names are never stored in plaintext. They are encrypted inside an authenticated manifest (`manifest.enc`). Vault storage contains opaque identifiers (`obj_<id>.enc`).
- **No Compression**: Preserves exact byte-for-byte integrity without compression side-channel risks.
- **Large-File Streaming**: Encrypts and decrypts files in 4 MiB chunks with bounded memory overhead.
- **Safe Atomic Operations**: Writes files via temporary buffers and atomically replaces them only after cryptographic validation succeeds.
- **Cross-Platform**: Supports Windows, Linux, and macOS from a single Python codebase.

---

## Installation

Requirements: Python 3.9+

```bash
pip install -r requirements.txt
```

---

## Usage

### 1. Initialize a new vault
```bash
python -m secure_folder.main init /path/to/my_vault
```
You will be prompted to enter and confirm your master password.

### 2. Check vault status
```bash
python -m secure_folder.main status /path/to/my_vault
```

### 3. Unlock vault files
```bash
python -m secure_folder.main unlock /path/to/my_vault
```
Decrypts files into a workspace directory. You can edit, add, or delete files directly inside the workspace.

### 4. Lock vault
```bash
python -m secure_folder.main lock /path/to/my_vault
```
Scans the workspace, re-encrypts new or modified files, cleans deleted files from the vault, updates the encrypted manifest, verifies integrity, and securely removes the unlocked workspace.

### 5. Verify vault integrity
```bash
python -m secure_folder.main verify /path/to/my_vault
```
Scans and authenticates all encrypted objects and manifest entries to verify there is no corruption or tampering.

### 6. Change master password
```bash
python -m secure_folder.main change-password /path/to/my_vault
```
Re-encrypts the vault data key with a new Scrypt-derived KEK without having to re-encrypt any data files.

---

## Running the Test Suite

Run all unit and integration tests with pytest:

```bash
python -m pytest tests -v
```
