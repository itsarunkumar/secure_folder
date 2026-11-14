# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path
from PyInstaller.utils.hooks import collect_all, collect_submodules

datas = []
binaries = []
hiddenimports = []

# Ensure all cryptographic C-extensions, DLLs, and metadata are bundled
crypto_datas, crypto_binaries, crypto_hidden = collect_all('cryptography')
datas.extend(crypto_datas)
binaries.extend(crypto_binaries)
hiddenimports.extend(crypto_hidden)

# Include Python 3.15 abi3t-compat DLLs if present
python_dir = Path(sys.executable).parent
abi3t_dll = python_dir / "abi3t-compat" / "python3t.dll"
if abi3t_dll.exists():
    binaries.append((str(abi3t_dll), '.'))

dlls_dir = python_dir / "DLLs"
for dll_name in ["libcrypto-3.dll", "libssl-3.dll"]:
    dll_path = dlls_dir / dll_name
    if dll_path.exists():
        binaries.append((str(dll_path), '.'))

# Include all SecureFolder modules
hiddenimports.extend(collect_submodules('secure_folder'))

a = Analysis(
    ['src/secure_folder/main.py'],
    pathex=['src'],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['pytest', 'unittest'],
    noarchive=False,
    optimize=1,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='secure-folder-windows',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
