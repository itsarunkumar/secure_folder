"""Handler for 'status' command."""

from pathlib import Path
from secure_folder.core.vault import Vault
from secure_folder.utils.logger import get_logger

def handle_status(vault_dir: Path, verbose: bool = False) -> int:
    """Displays vault status without requiring password."""
    logger = get_logger("secure_folder", verbose)
    vault_path = Path(vault_dir).resolve()
    status = Vault.get_status(vault_path)

    if not status["exists"]:
        logger.error(f"No vault found at: {vault_path}")
        return 1

    logger.info(f"Vault: {vault_path}")
    logger.info(f"Status: {status['status'].upper()}")
    if status.get("workspace"):
        logger.info(f"Active Workspace: {status['workspace']}")
    return 0
