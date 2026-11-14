"""Custom exception hierarchy for SecureFolder."""

class SecureFolderError(Exception):
    """Base exception for all SecureFolder errors."""
    pass

class AuthenticationError(SecureFolderError):
    """Raised when password authentication or decryption of keys fails."""
    pass

class IntegrityError(SecureFolderError):
    """Raised when data tampering, corruption, or invalid auth tag is detected."""
    pass

class VaultCorruptedError(SecureFolderError):
    """Raised when the vault structure, manifest, or config is unreadable or invalid."""
    pass

class VaultLockedError(SecureFolderError):
    """Raised when an operation requires an unlocked vault but it is locked."""
    pass

class VaultUnlockedError(SecureFolderError):
    """Raised when an operation requires a locked vault but it is currently unlocked."""
    pass

class FileOperationError(SecureFolderError):
    """Raised when a filesystem read/write/traversal error occurs."""
    pass

class UnsupportedPlatformError(SecureFolderError):
    """Raised when an unsupported platform is encountered."""
    pass
