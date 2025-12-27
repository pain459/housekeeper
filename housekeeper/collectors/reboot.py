from __future__ import annotations

from pathlib import Path
from typing import Any, Dict


def collect_reboot_required() -> Dict[str, Any]:
    """
    Ubuntu/Pop!_OS often creates /var/run/reboot-required when a reboot is recommended
    (e.g., after kernel/libc updates).
    """
    flag = Path("/var/run/reboot-required")
    pkgs = Path("/var/run/reboot-required.pkgs")

    out: Dict[str, Any] = {
        "reboot_required": flag.exists(),
    }

    if pkgs.exists():
        try:
            out["reboot_required_pkgs"] = pkgs.read_text(errors="replace").strip()
        except Exception:
            out["reboot_required_pkgs"] = None
    else:
        out["reboot_required_pkgs"] = None

    return out
