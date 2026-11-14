# SecureFolder Developer Guide

Comprehensive technical documentation for developers, contributors, and maintainers of the **SecureFolder** project.

---

## 1. Project Architecture

The codebase follows a modular 5-tier architecture:

```text
secure_folder/
├── src/secure_folder/
│   ├── core/
│   │   ├── encryption.py         # AES-256-GCM chunked streaming (no compression)
│   │   ├── key_manager.py        # Scrypt KDF, Vault Data Key (VDK), HKDF per-file keys
│   │   ├── manifest.py           # Encrypted directory & file structure (manifest.enc)
│   │   ├── integrity.py          # Authentication tag verification & corruption detection
│   │   └── vault.py              # High-level lifecycle (init, unlock, lock, verify, change-password)
│   ├── filesystem/
│   │   ├── file_manager.py       # Bounded-memory SHA-256 calculation & atomic replacements
│   │   ├── directory_manager.py  # Recursive directory scanning & structure recreation
│   │   └── workspace.py          # Workspace change detection (added/modified/deleted) & cleanup
│   ├── platform/
│   │   ├── detector.py           # Cross-platform OS detection (Windows, Linux, macOS)
│   │   ├── windows.py            # Windows hidden file attribute management
│   │   ├── linux.py              # Linux dotfile helpers
│   │   └── macos.py              # macOS chflags helpers
│   ├── commands/                 # CLI subcommand handlers (init, unlock, lock, verify, etc.)
│   ├── utils/                    # Constants, exception classes, and safe logging
│   └── main.py                   # CLI entry point and argument parsing
├── tests/                        # Automated pytest test suite
├── scripts/                      # Platform launchers, build scripts, and drive staging
├── dist/                         # Compiled standalone binaries
├── .github/workflows/            # GitHub Actions CI/CD workflows
├── pyproject.toml                # Build system & project metadata
├── requirements.txt              # Production and test dependencies
├── emergency_recover.py          # Standalone, zero-app-dependency recovery tool
├── USER_MANUAL.md                # End-user documentation
└── DEVELOPER.md                  # Developer & maintainer guide (this file)
```

---

## 2. Cryptographic Specifications

SecureFolder uses standardized authenticated encryption:

### 2.1 Key Derivation & Wrapping
1. **Key-Encryption Key (KEK)**:
   - Derived from master password using **Scrypt**.
   - Parameters: $N = 32768$ ($2^{15}$), $r = 8$, $p = 1$, salt = 32 random bytes (`os.urandom(32)`).
2. **Vault Data Key (VDK)**:
   - 256-bit cryptographically secure random key (`os.urandom(32)`).
   - Encrypted with KEK using AES-256-GCM.
   - Associated Data: `b"SecureFolder-VDK-v1"`.
   - Stored in `vault.json`.
3. **Per-File Data Key**:
   - Derived independently for each file via **HKDF-SHA256**:
     $$\text{file\_key} = \text{HKDF}(\text{IKM}=\text{VDK}, \text{salt}=\text{file\_id}, \text{info}=\texttt{b"SecureFolder-FileKey-v1"}, \text{len}=32)$$
   - Guarantees each file has an isolated AES key, preventing any risk of nonce collisions across files.

### 2.2 File Container Wire Format
Files are encrypted without compression into chunked streams:

- **File Header (26 bytes)**:
  - Magic (4 bytes): `b"SECF"`
  - Version (2 bytes unsigned short): `1`
  - Chunk Size (4 bytes unsigned int): `4194304` (4 MiB)
  - File ID (16 bytes): Random per-file identifier
- **Chunk Layout (Sequence of chunks)**:
  - Payload length (4 bytes unsigned int): Length of ciphertext + 16-byte tag
  - Last-chunk flag (1 byte unsigned char): `1` if final chunk, `0` otherwise
  - Nonce (12 bytes): `b"\x00"*8 + chunk_index.to_bytes(4, "big")`
  - Ciphertext + Tag: AES-256-GCM encrypted payload
  - Authenticated Associated Data (AAD):
    $$\text{AAD} = \texttt{b"SECF"} \mathbin{\Vert} \text{version} \mathbin{\Vert} \text{file\_id} \mathbin{\Vert} \text{chunk\_index} \mathbin{\Vert} \text{is\_last}$$

---

## 3. Development & Testing

### 3.1 Setup Development Environment
```bash
# Clone the repository
git clone <repo-url>
cd secure_folder

# Install dependencies in editable mode
pip install -r requirements.txt
pip install -e . --no-build-isolation --no-deps
```

### 3.2 Running the Test Suite
All tests must pass before opening PRs or tagging releases:
```bash
# Run all tests
python -m pytest -v

# Run a specific test module
python -m pytest tests/test_encryption.py -v
python -m pytest tests/test_vault.py -v
python -m pytest tests/test_emergency_recover.py -v
```

---

## 4. Standalone Binaries & Compilation

SecureFolder compiles into zero-prerequisite standalone executables using **PyInstaller**.

### 4.1 PyInstaller Specification (`secure_folder.spec`)
- **Single-File Mode (`--onefile`)**: Bundles the Python runtime, dependencies, and code into a single binary.
- **Dynamic C-Extension Bundling**: Explicitly collects the `cryptography` package binaries (OpenSSL DLLs/shared objects).
- **Free-Threaded ABI Support (Python 3.15+)**: Automatically includes `abi3t-compat/python3t.dll` if building with Python 3.15 free-threaded builds.

### 4.2 Local Compilation
- **Windows**:
  ```cmd
  scripts\build_windows.bat
  ```
  Output: `dist\secure-folder-windows.exe`
- **Linux**:
  ```bash
  bash scripts/build_linux.sh
  ```
  Output: `dist/secure-folder-linux`
- **macOS**:
  ```bash
  bash scripts/build_macos.sh
  ```
  Output: `dist/secure-folder-macos`

---

## 5. CI/CD & GitHub Releases Workflow

Automated multi-platform builds and release creation are handled by `.github/workflows/build_binaries.yml`.

### 5.1 Release Triggers & Workflow Logic
The workflow compiles all 3 binaries on native GitHub runners:
- `windows-latest` $\rightarrow$ `secure-folder-windows.exe`
- `ubuntu-22.04` $\rightarrow$ `secure-folder-linux`
- `macos-latest` $\rightarrow$ `secure-folder-macos`

#### When Does It Create a GitHub Release?
1. **Push to `main` branch**:
   - Automatically builds all binaries and updates a rolling **`latest`** pre-release with attached binary assets.
2. **Version Tag Push (e.g., `v1.0.0`)**:
   - Creates a permanent tagged release (e.g. `SecureFolder v1.0.0`) with release notes and binary assets.
3. **Manual Trigger (`workflow_dispatch`)**:
   - Can be triggered manually anytime via the **Actions** tab in GitHub by clicking **"Run workflow"**.

### 5.2 Creating a Tagged Version Release
To release a new official version:
```bash
# 1. Update version in src/secure_folder/__init__.py and pyproject.toml
# 2. Commit changes
git add .
git commit -m "Release v1.1.0"

# 3. Create and push Git tag
git tag v1.1.0
git push origin v1.1.0
```

### 5.3 Required GitHub Token Permissions
The workflow requires write permissions to create releases. Ensure:
- In `.github/workflows/build_binaries.yml`:
  ```yaml
  permissions:
    contents: write
  ```
- In GitHub Repository Settings: **Settings $\rightarrow$ Actions $\rightarrow$ General $\rightarrow$ Workflow permissions $\rightarrow$ Read and write permissions**.

---

## 6. Standalone Utilities

### 6.1 `emergency_recover.py`
A completely self-contained recovery script that has **no dependencies on the `secure_folder` package**. It exists to guarantee users are never trapped in a proprietary tool.
- When modifying vault wire format or KDF parameters, **always** update and test `emergency_recover.py` via `tests/test_emergency_recover.py`.

### 6.2 `scripts/stage_drive.py`
Staging script to prepare an external USB or HDD:
```bash
python scripts/stage_drive.py E:\
```
Deploys `secure-folder.exe`, double-click launcher `.bat` scripts, `emergency_recover.py`, and user documentation to the external storage device.
