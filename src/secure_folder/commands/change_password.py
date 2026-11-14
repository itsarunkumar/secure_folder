"""Handler for 'change-password' command."""

import getpass
import os
from pathlib import Path
from typing import Optional

from secure_folder.core.vault import Vault
from secure_folder.utils.exceptions import SecureFolderError
from secure_folder.utils.logger import get_logger

def handle_change_password(
    vault_dir: Path,
    old_password: Optional[str] = None,
    new_password: Optional[str] = None,
    verbose: bool = False,
) -> int:
    """Changes the vault password."""
    logger = get_logger("secure_folder", verbose)
    vault_path = Path(vault_dir).resolve()

    if not old_password:
        old_password = getpass.getpass("Enter current master password: ")

    if not new_password:
        p1 = getpass.getpass("Enter new master password: ")
        p2 = getpass.getpass("Confirm new master password: ")
        if p1 != p2:
            logger.error("New passwords do not match.")
            return 1
        if len(p1) < 6:
            logger.error("Password is too short. Minimum 6 characters required.")
            return 1
        new_password = p1

    try:
        Vault.change_password(vault_path, old_password, new_password)
        logger.info("Vault password changed successfully.")
        return 0
    except SecureFolderError as e:
        logger.error(f"Password change failed: {e}")
        return 1
