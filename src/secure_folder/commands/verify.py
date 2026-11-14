"""Handler for 'verify' command."""

import getpass
import os
from pathlib import Path
from typing import Optional

from secure_folder.core.vault import Vault
from secure_folder.utils.exceptions import SecureFolderError
from secure_folder.utils.logger import get_logger

def handle_verify(
    vault_dir: Path,
    password: Optional[str] = None,
    verbose: bool = False,
) -> int:
    """Verifies authentication and integrity across all vault items."""
    logger = get_logger("secure_folder", verbose)
    vault_path = Path(vault_dir).resolve()

    if not password:
        password = os.environ.get("SECURE_FOLDER_PASSWORD") or getpass.getpass("Enter vault master password to verify: ")

    try:
        report = Vault.verify(vault_path, password)
        if report["healthy"]:
            logger.info("Vault integrity check: PASSED (Healthy)")
            logger.info(
                f"Verified {report['verified_files_count']}/{report['total_files']} files, "
                f"{report['total_directories']} directories."
            )
            return 0
        else:
            logger.error("Vault integrity check: FAILED (Corruption or missing objects detected)")
            if report["corrupted_files"]:
                logger.error(f"Corrupted files: {report['corrupted_files']}")
            if report["missing_objects"]:
                logger.error(f"Missing objects: {report['missing_objects']}")
            return 1
    except SecureFolderError as e:
        logger.error(f"Verification failed: {e}")
        return 1
