"""Operating system detector."""

import platform
import sys
from secure_folder.utils.exceptions import UnsupportedPlatformError

PLATFORM_WINDOWS = "windows"
PLATFORM_LINUX = "linux"
PLATFORM_MACOS = "macos"

def get_platform_name() -> str:
    """Returns the normalized platform name: 'windows', 'linux', or 'macos'."""
    sys_name = platform.system().lower()
    if sys_name == "windows":
        return PLATFORM_WINDOWS
    elif sys_name == "linux":
        return PLATFORM_LINUX
    elif sys_name == "darwin":
        return PLATFORM_MACOS
    else:
        raise UnsupportedPlatformError(f"Unsupported operating system: {sys_name}")

def is_windows() -> bool:
    return get_platform_name() == PLATFORM_WINDOWS

def is_linux() -> bool:
    return get_platform_name() == PLATFORM_LINUX

def is_macos() -> bool:
    return get_platform_name() == PLATFORM_MACOS
