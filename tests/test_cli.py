"""CLI integration tests."""

import pytest
from pathlib import Path
from secure_folder.main import build_parser
from secure_folder.commands.init import handle_init
from secure_folder.commands.unlock import handle_unlock
from secure_folder.commands.lock import handle_lock
from secure_folder.commands.verify import handle_verify
from secure_folder.commands.status import handle_status

def test_cli_parser():
    parser = build_parser()
    args = parser.parse_args(["init", "my_vault", "--password", "Secret123"])
    assert args.command == "init"
    assert str(args.vault_dir) == "my_vault"
    assert args.password == "Secret123"

def test_cli_full_flow(tmp_path):
    vault_dir = tmp_path / "cli_vault"
    ws_dir = tmp_path / "cli_ws"
    pwd = "CLISecretPassword123!"

    # 1. Init
    rc = handle_init(vault_dir, password=pwd)
    assert rc == 0

    # 2. Status
    rc = handle_status(vault_dir)
    assert rc == 0

    # 3. Unlock
    rc = handle_unlock(vault_dir, target_workspace=ws_dir, password=pwd)
    assert rc == 0
    assert ws_dir.exists()

    # Create test file
    (ws_dir / "cli_test.txt").write_text("Hello from CLI!")

    # 4. Lock
    rc = handle_lock(vault_dir, password=pwd)
    assert rc == 0
    assert not ws_dir.exists()

    # 5. Verify
    rc = handle_verify(vault_dir, password=pwd)
    assert rc == 0

    # 6. Unlock and check file
    rc = handle_unlock(vault_dir, target_workspace=ws_dir, password=pwd)
    assert rc == 0
    assert (ws_dir / "cli_test.txt").read_text() == "Hello from CLI!"
