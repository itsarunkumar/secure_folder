"""Handler for 'unlock' command."""

import getpass
import os
from pathlib import Path
from typing import Optional

from secure_folder.core.vault import Vault
from secure_folder.utils.exceptions import SecureFolderError
from secure_folder.utils.logger import get_logger

def handle_unlock(
    vault_dir: Path,
    target_workspace: Optional[Path] = None,
    password: Optional[str] = None,
    verbose: bool = False,
) -> int:
    """Unlocks a vault into target_workspace."""
    logger = get_logger("secure_folder", verbose)
    vault_path = Path(vault_dir).resolve()

    if not password:
        password = os.environ.get("SECURE_FOLDER_PASSWORD") or getpass.getpass("Enter vault master password: ")

    try:
        ws_path = Vault.unlock(vault_path, password, target_workspace)
        logger.info(f"Vault unlocked successfully.")
        logger.info(f"Working files are available at: {ws_path}")
        return 0
    except SecureFolderError as e:
        logger.error(f"Unlock failed: {e}")
        return 1
