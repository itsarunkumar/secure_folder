# SecureFolder Developer Guide

Technical documentation for developers, contributors, and maintainers of the **SecureFolder** project.

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
├── scripts/                      # Launchers, bundle builder, and drive staging
├── dist/portable_bundle/         # Zero-block signed portable distribution for external drives
├── .github/workflows/ci.yml      # Multi-OS automated testing pipeline
├── pyproject.toml                # Build system & project metadata
├── requirements.txt              # Dependencies (cryptography, pytest)
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
All tests must pass before opening PRs:
```bash
# Run all tests
python -m pytest -v

# Run specific modules
python -m pytest tests/test_encryption.py -v
python -m pytest tests/test_vault.py -v
python -m pytest tests/test_emergency_recover.py -v
```

---

## 4. Zero-Cost Portability Architecture

### 4.1 Why We Avoid Unsigned Executable Binaries
Modern operating systems (especially Windows 11 Smart App Control and macOS Gatekeeper) block custom compiled `.exe` / `.app` binaries unless they are signed with an expensive Authenticode / Apple Developer certificate.

To ensure SecureFolder remains **100% free, open-source, and guaranteed to run on any computer**:
- We use **Microsoft's officially signed portable Python runtime** inside `dist/portable_bundle/SecureFolder/python/`.
- Because the binaries (`python.exe`, DLLs) are signed by Microsoft Corporation and the Python Software Foundation, Windows 11 Smart App Control allows them immediately without warnings.

### 4.2 Rebuilding the Portable Bundle
To regenerate the portable bundle:
```bash
python scripts/build_portable_bundle.py
```
This downloads the official signed Python embeddable runtime, installs `cryptography`, copies the source code, and creates 1-click batch launchers.

---

## 5. Standalone Utilities

### 5.1 `emergency_recover.py`
A completely self-contained recovery script with **zero dependencies on the `secure_folder` package**. It exists to guarantee users are never trapped in any proprietary tool.
- When modifying vault wire format or KDF parameters, **always** verify `emergency_recover.py` via `tests/test_emergency_recover.py`.

### 5.2 `scripts/stage_drive.py`
Deploys the portable bundle directly onto an external USB or HDD:
```bash
python scripts/stage_drive.py E:\
```
Copies the signed runtime, double-click batch launchers, `emergency_recover.py`, and documentation to the target drive.
