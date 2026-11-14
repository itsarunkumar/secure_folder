"""Handler for 'lock' command."""

import getpass
import os
from pathlib import Path
from typing import Optional

from secure_folder.core.vault import Vault
from secure_folder.utils.exceptions import SecureFolderError
from secure_folder.utils.logger import get_logger

def handle_lock(
    vault_dir: Path,
    password: Optional[str] = None,
    verbose: bool = False,
) -> int:
    """Locks a vault by re-encrypting changed files and securely removing workspace."""
    logger = get_logger("secure_folder", verbose)
    vault_path = Path(vault_dir).resolve()

    if not password:
        password = os.environ.get("SECURE_FOLDER_PASSWORD") or getpass.getpass("Enter vault master password to lock: ")

    try:
        stats = Vault.lock(vault_path, password)
        logger.info("Vault locked successfully.")
        logger.info(
            f"Summary: {stats['added']} added, {stats['modified']} modified, "
            f"{stats['deleted']} deleted, {stats['unchanged']} unchanged."
        )
        return 0
    except SecureFolderError as e:
        logger.error(f"Lock failed: {e}")
        return 1
