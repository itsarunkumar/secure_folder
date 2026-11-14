"""SecureFolder main CLI entry point."""

import argparse
import sys
from pathlib import Path

from secure_folder import __version__
from secure_folder.commands.init import handle_init
from secure_folder.commands.unlock import handle_unlock
from secure_folder.commands.lock import handle_lock
from secure_folder.commands.verify import handle_verify
from secure_folder.commands.status import handle_status
from secure_folder.commands.change_password import handle_change_password

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="secure-folder",
        description="Cross-platform password-protected folder utility.",
    )
    parser.add_argument(
        "-v", "--version", action="version", version=f"%(prog)s {__version__}"
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Enable verbose debug logging."
    )

    subparsers = parser.add_subparsers(dest="command", required=True, help="Subcommands")

    # init
    p_init = subparsers.add_parser("init", help="Initialize a new secure vault.")
    p_init.add_argument("vault_dir", type=Path, help="Directory path to create the vault in.")
    p_init.add_argument("--password", type=str, default=None, help="Vault master password (optional).")

    # unlock
    p_unlock = subparsers.add_parser("unlock", help="Unlock vault files into a working workspace.")
    p_unlock.add_argument("vault_dir", type=Path, help="Directory path of the vault.")
    p_unlock.add_argument("-w", "--workspace", type=Path, default=None, help="Target workspace directory.")
    p_unlock.add_argument("--password", type=str, default=None, help="Vault master password (optional).")

    # lock
    p_lock = subparsers.add_parser("lock", help="Lock vault and re-encrypt updated workspace files.")
    p_lock.add_argument("vault_dir", type=Path, help="Directory path of the vault.")
    p_lock.add_argument("--password", type=str, default=None, help="Vault master password (optional).")

    # verify
    p_verify = subparsers.add_parser("verify", help="Verify integrity of all files and structures in vault.")
    p_verify.add_argument("vault_dir", type=Path, help="Directory path of the vault.")
    p_verify.add_argument("--password", type=str, default=None, help="Vault master password (optional).")

    # status
    p_status = subparsers.add_parser("status", help="Show current lock status of vault.")
    p_status.add_argument("vault_dir", type=Path, help="Directory path of the vault.")

    # change-password
    p_cp = subparsers.add_parser("change-password", help="Change the vault master password.")
    p_cp.add_argument("vault_dir", type=Path, help="Directory path of the vault.")
    p_cp.add_argument("--old-password", type=str, default=None, help="Current master password.")
    p_cp.add_argument("--new-password", type=str, default=None, help="New master password.")

    return parser

def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    cmd = args.command
    verbose = args.verbose

    if cmd == "init":
        code = handle_init(args.vault_dir, password=args.password, verbose=verbose)
    elif cmd == "unlock":
        code = handle_unlock(
            args.vault_dir,
            target_workspace=args.workspace,
            password=args.password,
            verbose=verbose,
        )
    elif cmd == "lock":
        code = handle_lock(args.vault_dir, password=args.password, verbose=verbose)
    elif cmd == "verify":
        code = handle_verify(args.vault_dir, password=args.password, verbose=verbose)
    elif cmd == "status":
        code = handle_status(args.vault_dir, verbose=verbose)
    elif cmd == "change-password":
        code = handle_change_password(
            args.vault_dir,
            old_password=args.old_password,
            new_password=args.new_password,
            verbose=verbose,
        )
    else:
        parser.print_help()
        code = 1

    sys.exit(code)

if __name__ == "__main__":
    main()
