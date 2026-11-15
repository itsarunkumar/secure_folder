"""SecureFolder pywebview desktop UI - Python API bridge."""

import os
import sys
import threading
import subprocess
from pathlib import Path

import webview

# Resolve src path for imports when running from portable bundle
_ui_dir = Path(__file__).resolve().parent
_src_dir = _ui_dir.parent.parent.parent  # src/
if str(_src_dir) not in sys.path:
    sys.path.insert(0, str(_src_dir))

from secure_folder.core.vault import Vault
from secure_folder.utils.exceptions import (
    SecureFolderError, AuthenticationError
)

HTML_FILE = Path(__file__).parent / "index.html"


def _find_vault_dir(hint: Path = None) -> Path:
    """Resolve vault directory: explicit hint → CWD/my_vault → next to script."""
    if hint is not None:
        return Path(hint).resolve()
    # When launched via `python -m secure_folder.ui.app` or launch_ui.py from project root
    cwd_vault = Path.cwd() / "my_vault"
    if cwd_vault.exists():
        return cwd_vault
    # Fallback: my_vault next to the package root
    pkg_root = _ui_dir.parent.parent.parent.parent  # Desktop/security/secure_folder
    fallback = pkg_root / "my_vault"
    return fallback


class VaultAPI:
    """Python API exposed to JavaScript via window.pywebview.api.*"""

    def __init__(self, vault_dir: Path):
        self.vault_dir = Path(vault_dir).resolve()
        self._window = None

    def set_window(self, window):
        self._window = window

    # ------------------------------------------------------------------ status
    def get_status(self):
        try:
            status = Vault.get_status(self.vault_dir)
            return {"ok": True, "data": status}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def get_vault_name(self):
        return self.vault_dir.name

    def get_vault_path(self):
        return str(self.vault_dir)

    # ------------------------------------------------------------------ init
    def init_vault(self, password: str):
        try:
            Vault.init_vault(self.vault_dir, password)
            return {"ok": True, "message": f"Vault created at {self.vault_dir.name}"}
        except SecureFolderError as e:
            return {"ok": False, "error": str(e)}

    # ------------------------------------------------------------------ unlock
    def unlock(self, password: str):
        try:
            workspace = Vault.unlock(self.vault_dir, password)
            # Open workspace in File Explorer automatically
            self._open_folder(workspace)
            return {"ok": True, "workspace": str(workspace)}
        except AuthenticationError:
            return {"ok": False, "error": "Incorrect password. Please try again."}
        except SecureFolderError as e:
            return {"ok": False, "error": str(e)}

    # ------------------------------------------------------------------ lock
    def lock(self, password: str):
        try:
            stats = Vault.lock(self.vault_dir, password)
            return {"ok": True, "stats": stats}
        except AuthenticationError:
            return {"ok": False, "error": "Incorrect password. Please try again."}
        except SecureFolderError as e:
            return {"ok": False, "error": str(e)}

    # ------------------------------------------------------------------ verify
    def verify(self, password: str):
        try:
            report = Vault.verify(self.vault_dir, password)
            return {"ok": True, "report": report}
        except AuthenticationError:
            return {"ok": False, "error": "Incorrect password. Please try again."}
        except SecureFolderError as e:
            return {"ok": False, "error": str(e)}

    # ------------------------------------------------------------------ change password
    def change_password(self, old_password: str, new_password: str):
        try:
            Vault.change_password(self.vault_dir, old_password, new_password)
            return {"ok": True, "message": "Password changed successfully."}
        except AuthenticationError:
            return {"ok": False, "error": "Current password is incorrect."}
        except SecureFolderError as e:
            return {"ok": False, "error": str(e)}

    # ------------------------------------------------------------------ open workspace in explorer
    def open_workspace(self):
        try:
            status = Vault.get_status(self.vault_dir)
            ws = status.get("workspace")
            if ws and Path(ws).exists():
                self._open_folder(Path(ws))
                return {"ok": True}
            return {"ok": False, "error": "No active workspace found."}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    # ------------------------------------------------------------------ helpers
    def _open_folder(self, path: Path):
        try:
            if sys.platform == "win32":
                os.startfile(str(path))
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(path)])
            else:
                subprocess.Popen(["xdg-open", str(path)])
        except Exception:
            pass


def launch(vault_dir: Path = None):
    """Launch the SecureFolder desktop UI window."""
    resolved = _find_vault_dir(vault_dir)

    api = VaultAPI(resolved)

    window = webview.create_window(
        title="SecureFolder",
        url=str(HTML_FILE.as_uri()),
        js_api=api,
        width=520,
        height=660,
        resizable=False,
        text_select=False,
        background_color="#0f172a",
        easy_drag=True,
    )
    api.set_window(window)
    webview.start(debug=False)


if __name__ == "__main__":
    # Accept optional vault path as CLI arg
    vault_path = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    launch(vault_path)
