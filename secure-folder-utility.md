# SecureFolder

**Cross-platform password-protected folder utility**

> Project specification and development plan --- Version 1.0

## 1. Project objective

Develop a lightweight, portable, cross-platform utility that creates and
manages a password-protected folder directly on an external storage
device.

The utility encrypts files and folder names without compression,
preserves original file contents exactly, and provides a password-based
unlock and lock workflow.

**Primary goal:** Protect selected files and folders without encrypting
the entire hard disk or affecting other storage areas.

### Core objectives

1.  Create a password-protected private vault on an external HDD.
2.  Support Windows, Linux, and macOS through a common Python codebase.
3.  Encrypt files using authenticated encryption.
4.  Preserve file contents byte-for-byte after decryption.
5.  Protect filenames and directory structures.
6.  Support large files without loading entire files into memory.
7.  Allow users to unlock, access, modify, and relock files.
8.  Detect corruption, tampering, and incomplete operations.
9.  Avoid storing passwords or encryption keys in plaintext.
10. Keep the remaining HDD storage completely independent of the vault.

## 2. Project scope

### In scope

-   Folder encryption
-   Password authentication
-   AES-256-GCM authenticated encryption
-   Cross-platform support
-   File and folder name encryption
-   File integrity verification
-   Large-file streaming
-   Backup and recovery support
-   Portable execution
-   Command-line interface

### Out of scope for the initial version

-   Cloud synchronization
-   Multi-user access
-   Compression
-   Mobile applications
-   Network sharing
-   GUI application
-   Forensic-grade deletion

### Important architectural decision

The vault will be a directory containing encrypted file objects and
encrypted metadata, not a compressed archive.

When unlocked, files will be available in a temporary working directory.
When locked, updated files will be encrypted back into the vault.

## 3. Technical architecture

The application is divided into five layers:

1.  **User interface / CLI:** Commands, password prompts, and status
    output.
2.  **Application layer:** Initialization, unlock, lock, verify, and
    status workflows.
3.  **Core services:** Encryption, key management, metadata, and
    integrity.
4.  **Platform and filesystem services:** OS detection, file operations,
    and workspace handling.
5.  **Storage layer:** Encrypted vault, temporary workspace, and
    transaction journal.

### Recommended technology stack

  Area                            Technology
  ------------------------------- ---------------------
  Language                        Python 3
  Encryption library              `cryptography`
  Encryption algorithm            AES-256-GCM
  Password-based key derivation   Scrypt
  File operations                 `pathlib`, `shutil`
  OS detection                    `platform`
  CLI                             `argparse`
  Testing                         `pytest`
  Packaging                       PyInstaller
  Configuration                   JSON

### Security design decisions

-   Use a unique, cryptographically random nonce for every encryption
    operation.
-   Derive a key-encryption key from the password using Scrypt and a
    random salt.
-   Generate a random vault data-encryption key.
-   Encrypt the vault data key using the password-derived key. This
    supports password changes without re-encrypting all vault data.
-   Encrypt filenames and directory metadata.
-   Authenticate encrypted data before releasing plaintext.
-   Use temporary files and atomic replacement where supported.
-   Never overwrite original files during initial encryption.
-   Keep an independent backup before enabling destructive operations.
-   Define and version the encrypted file format.

**Large-file encryption requirement:** Use independently authenticated
chunks with a carefully specified nonce and associated-data scheme. Do
not invent an unsafe streaming AES-GCM implementation or reuse nonces
with the same key.

## 4. Proposed project structure

``` text
secure-folder/
│
├── src/
│   └── secure_folder/
│       ├── __init__.py
│       ├── main.py
│       │
│       ├── core/
│       │   ├── vault.py
│       │   ├── encryption.py
│       │   ├── key_manager.py
│       │   ├── manifest.py
│       │   └── integrity.py
│       │
│       ├── filesystem/
│       │   ├── file_manager.py
│       │   ├── directory_manager.py
│       │   └── workspace.py
│       │
│       ├── platform/
│       │   ├── detector.py
│       │   ├── windows.py
│       │   ├── linux.py
│       │   └── macos.py
│       │
│       ├── commands/
│       │   ├── init.py
│       │   ├── unlock.py
│       │   ├── lock.py
│       │   ├── verify.py
│       │   └── status.py
│       │
│       └── utils/
│           ├── constants.py
│           ├── exceptions.py
│           └── logger.py
│
├── tests/
│   ├── test_encryption.py
│   ├── test_key_manager.py
│   ├── test_manifest.py
│   ├── test_integrity.py
│   ├── test_vault.py
│   ├── test_large_files.py
│   └── test_cross_platform.py
│
├── scripts/
│   ├── run_windows.bat
│   ├── run_linux.sh
│   └── run_macos.command
│
├── requirements.txt
├── pyproject.toml
├── README.md
└── .gitignore
```

### Module responsibilities

  Module                   Responsibility
  ------------------------ -----------------------------------------------
  `main.py`                Application entry point and command routing
  `vault.py`               Overall vault lifecycle
  `encryption.py`          File encryption and decryption
  `key_manager.py`         Password handling, Scrypt, and key management
  `manifest.py`            Encrypted file and directory metadata
  `integrity.py`           Authentication and corruption checks
  `file_manager.py`        File copying and streaming
  `directory_manager.py`   Directory traversal and structure
  `workspace.py`           Temporary unlocked workspace
  `detector.py`            Operating-system detection
  `windows.py`             Windows-specific behavior
  `linux.py`               Linux-specific behavior
  `macos.py`               macOS-specific behavior

## 5. Work plan and development phases

Each phase should produce a working deliverable before the next phase
begins.

### Phase 1 --- Project foundation

-   [ ] Create repository and Python package.
-   [ ] Configure dependencies.
-   [ ] Implement OS detection.
-   [ ] Implement CLI command structure.
-   [ ] Define vault directory structure.
-   [ ] Define versioned storage format.

**Deliverable:** Application skeleton running on all three platforms.

### Phase 2 --- Encryption engine

-   [ ] Implement Scrypt key derivation.
-   [ ] Generate cryptographically secure random salts and nonces.
-   [ ] Implement AES-256-GCM encryption.
-   [ ] Implement chunked authenticated encryption.
-   [ ] Implement decryption.
-   [ ] Validate authentication tags.
-   [ ] Add encryption/decryption round-trip tests.

**Deliverable:** Ability to encrypt and decrypt individual files without
compression.

### Phase 3 --- Vault management

-   [ ] Implement vault initialization.
-   [ ] Generate random vault data key.
-   [ ] Encrypt vault data key with password-derived key.
-   [ ] Implement encrypted manifest.
-   [ ] Implement unlock authentication.
-   [ ] Implement password-change workflow.
-   [ ] Handle wrong passwords safely.

**Deliverable:** A functioning encrypted vault.

### Phase 4 --- File and directory management

-   [ ] Implement recursive directory traversal.
-   [ ] Implement individual file encryption.
-   [ ] Implement filename encryption.
-   [ ] Preserve nested directory structures.
-   [ ] Handle duplicate filenames.
-   [ ] Support large files through streaming.
-   [ ] Preserve original files during initial backup.
-   [ ] Implement byte-for-byte restoration tests.

**Deliverable:** Complete directory backup and restoration.

### Phase 5 --- Unlock and lock workflow

-   [ ] Implement workspace creation.
-   [ ] Decrypt files into workspace.
-   [ ] Allow normal file editing.
-   [ ] Detect added files.
-   [ ] Detect modified files.
-   [ ] Detect deleted files.
-   [ ] Re-encrypt changes during locking.
-   [ ] Validate encrypted data before workspace cleanup.

**Deliverable:** Complete password-protected folder workflow.

### Phase 6 --- Integrity and recovery

-   [ ] Detect corrupted encrypted files.
-   [ ] Detect interrupted encryption.
-   [ ] Add transaction journal.
-   [ ] Implement interrupted-operation recovery.
-   [ ] Prevent accidental overwrite.
-   [ ] Handle insufficient storage space.
-   [ ] Implement vault verification command.

**Deliverable:** Reliable failure recovery.

### Phase 7 --- Cross-platform compatibility

-   [ ] Test Windows 10/11.
-   [ ] Test Linux.
-   [ ] Test macOS.
-   [ ] Implement launch scripts.
-   [ ] Resolve filesystem-specific behavior.
-   [ ] Package standalone executables for each OS.

**Deliverable:** Portable application releases.

### Phase 8 --- Final testing and documentation

-   [ ] Run security tests.
-   [ ] Test large files.
-   [ ] Test incorrect passwords.
-   [ ] Test corrupted data.
-   [ ] Test interrupted operations.
-   [ ] Write recovery procedure.
-   [ ] Complete user documentation.

**Deliverable:** SecureFolder v1.0.

## 6. Detailed implementation checklist

Use this checklist to track individual development tasks.

### Project foundation

-   [ ] Create repository and Python package.
-   [ ] Configure `pyproject.toml` and dependencies.
-   [ ] Implement OS detection.
-   [ ] Implement CLI command parser.
-   [ ] Define vault directory structure.
-   [ ] Define versioned storage format.

### Encryption engine

-   [ ] Implement Scrypt key derivation.
-   [ ] Generate cryptographically secure random salt and nonce.
-   [ ] Implement AES-256-GCM encryption.
-   [ ] Implement chunked authenticated encryption.
-   [ ] Implement decryption.
-   [ ] Validate authentication tags.
-   [ ] Add encryption/decryption round-trip tests.

### Vault management

-   [ ] Implement vault initialization.
-   [ ] Generate random vault data key.
-   [ ] Encrypt vault data key with password-derived key.
-   [ ] Implement encrypted manifest.
-   [ ] Implement unlock authentication.
-   [ ] Implement password change.
-   [ ] Handle wrong password safely.

### File management

-   [ ] Implement recursive directory traversal.
-   [ ] Implement individual file encryption.
-   [ ] Implement filename encryption.
-   [ ] Preserve nested folder structure.
-   [ ] Handle duplicate filenames.
-   [ ] Support large files with bounded memory.
-   [ ] Preserve original files during initial backup.
-   [ ] Implement byte-for-byte restoration tests.

### Workspace management

-   [ ] Create temporary workspace.
-   [ ] Unlock vault into workspace.
-   [ ] Detect modified files.
-   [ ] Detect new files.
-   [ ] Detect deleted files.
-   [ ] Re-encrypt changes safely.
-   [ ] Verify successful encryption before cleanup.
-   [ ] Implement lock operation.

### Integrity and recovery

-   [ ] Verify encrypted file authentication.
-   [ ] Detect truncated files.
-   [ ] Add transaction journal.
-   [ ] Implement interrupted-operation recovery.
-   [ ] Prevent accidental overwrite.
-   [ ] Handle disk-full errors.
-   [ ] Implement vault verification command.

### Cross-platform support

-   [ ] Test Windows 10/11.
-   [ ] Test Linux.
-   [ ] Test macOS.
-   [ ] Create Windows launcher.
-   [ ] Create Linux launcher.
-   [ ] Create macOS launcher.
-   [ ] Build platform-specific executables.

### Release

-   [ ] Run complete test suite.
-   [ ] Test wrong-password scenarios.
-   [ ] Test large-file scenarios.
-   [ ] Test interrupted lock/unlock.
-   [ ] Test external HDD removal.
-   [ ] Document recovery procedure.
-   [ ] Write README and release notes.

## 7. Functional requirements and acceptance criteria

  ID      Requirement          Expected result
  ------- -------------------- ---------------------------------------
  FR-01   Create vault         Vault created with password
  FR-02   Unlock vault         Correct password grants access
  FR-03   Wrong password       Access denied
  FR-04   Encrypt files        No compression
  FR-05   Restore files        Original bytes identical
  FR-06   Preserve structure   Nested directories restored
  FR-07   Protect names        Filenames not visible while locked
  FR-08   Lock vault           Updated files encrypted
  FR-09   Integrity            Corruption detected
  FR-10   Portability          Works on Windows, Linux, and macOS
  FR-11   Large files          Streaming without loading entire file
  FR-12   Recovery             Interrupted operations recover safely

## 8. Engineering and security rules

1.  **No compression:** Never use ZIP, TAR, GZIP, or other compression
    in the encryption pipeline.
2.  **No original deletion:** Initial encryption must never delete
    source files.
3.  **Authenticated encryption:** Use AES-GCM and authenticate every
    encrypted chunk.
4.  **Unique nonces:** Never reuse a nonce with the same encryption key.
5.  **Key separation:** Keep the vault data key separate from the
    password-derived key.
6.  **Memory efficiency:** Process files in chunks, for example 4 MiB at
    a time.
7.  **Safe writes:** Use temporary files and atomic replacement where
    possible.
8.  **Recovery:** Never destroy the workspace if re-encryption or
    verification fails.
9.  **Password safety:** Never log or persist passwords.
10. **Backup:** Keep an independent copy of the vault before risky
    modifications.

### Additional operational cautions

-   Locking a vault does not guarantee secure erasure of plaintext from
    SSDs, temporary directories, filesystem caches, or backups.
-   A computer may retain plaintext in application temporary files or
    swap/page files.
-   The vault must not be treated as a backup by itself. Maintain an
    independent backup.
-   If the password and recovery material are lost, the encrypted data
    may be unrecoverable.
-   Test recovery procedures before trusting important data to the
    utility.

## 9. Initial development milestones

  Milestone   Completion criteria
  ----------- ---------------------------------------
  M1          Single-file encryption and decryption
  M2          Folder encryption and restoration
  M3          Password-protected vault
  M4          Unlock and lock workflow
  M5          Integrity and recovery
  M6          Cross-platform release

### Recommended starting point: M1 --- Encryption Engine

Do not start with the CLI, launchers, or UI. First prove that the
application can:

1.  Read a source file.
2.  Encrypt it without compression.
3.  Decrypt it.
4.  Calculate SHA-256 hashes of the original and restored files.
5.  Confirm that both hashes match.

This establishes the core correctness requirement before building the
rest of the system.

## 10. Definition of done --- Version 1.0

-   [ ] One common Python codebase.
-   [ ] Windows, Linux, and macOS support.
-   [ ] Password-protected vault.
-   [ ] AES-256-GCM encryption.
-   [ ] No compression.
-   [ ] Encrypted filenames and metadata.
-   [ ] Large-file streaming.
-   [ ] Unlock and lock functionality.
-   [ ] Integrity verification.
-   [ ] Interrupted-operation recovery.
-   [ ] Independent backup and restore procedure.
-   [ ] Platform-specific standalone executables.

------------------------------------------------------------------------

## 11. Development principles

SecureFolder should be developed as a small security engineering
project.

The priorities, in order, are:

1.  **Correctness:** Decryption must reproduce the original bytes
    exactly.
2.  **Security:** Encryption, key management, and authentication must be
    implemented correctly.
3.  **Reliability:** Interrupted operations must not destroy data.
4.  **Portability:** The common codebase must behave consistently across
    supported systems.
5.  **Usability:** Locking and unlocking should be straightforward.
6.  **Maintainability:** Each module should have a clear responsibility
    and automated tests.

**Final recommendation:** Build and test the encryption engine first.
Get the cryptography and recovery model right, then build folder
management and the user interface around it.
