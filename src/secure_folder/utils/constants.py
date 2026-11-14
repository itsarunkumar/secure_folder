"""Constants for the SecureFolder utility."""

# File container constants
FILE_MAGIC = b"SECF"
FILE_FORMAT_VERSION = 1
DEFAULT_CHUNK_SIZE = 4 * 1024 * 1024  # 4 MiB

# Cryptographic parameters
KEY_LEN = 32          # 256 bits for AES-256
NONCE_LEN = 12        # 96 bits for standard AES-GCM
TAG_LEN = 16          # 128 bits for AES-GCM authentication tag
SCRYPT_SALT_LEN = 32  # 256-bit random salt
SCRYPT_N = 32768      # CPU/memory cost parameter (2^15)
SCRYPT_R = 8          # Block size
SCRYPT_P = 1          # Parallelization parameter

# Vault directory structure
VAULT_CONFIG_NAME = "vault.json"
VAULT_MANIFEST_NAME = "manifest.enc"
VAULT_OBJECTS_DIR = "objects"
VAULT_JOURNAL_NAME = "journal.json"
DEFAULT_WORKSPACE_NAME = "unlocked_workspace"
