"""Handler for 'init' command."""

import getpass
import os
from pathlib import Path
from typing import Optional

from secure_folder.core.vault import Vault
from secure_folder.utils.exceptions import SecureFolderError
from secure_folder.utils.logger import get_logger

def handle_init(vault_dir: Path, password: Optional[str] = None, verbose: bool = False) -> int:
    """Initializes a new vault."""
    logger = get_logger("secure_folder", verbose)
    vault_path = Path(vault_dir).resolve()
    
    if not password:
        env_pwd = os.environ.get("SECURE_FOLDER_PASSWORD")
        if env_pwd:
            password = env_pwd
        else:
            p1 = getpass.getpass("Enter master password for new vault: ")
            p2 = getpass.getpass("Confirm master password: ")
            if p1 != p2:
                logger.error("Passwords do not match.")
                return 1
            if len(p1) < 6:
                logger.error("Password is too short. Minimum 6 characters required.")
                return 1
            password = p1

    try:
        Vault.init_vault(vault_path, password)
        logger.info(f"Successfully initialized secure vault at: {vault_path}")
        return 0
    except SecureFolderError as e:
        logger.error(f"Initialization failed: {e}")
        return 1
