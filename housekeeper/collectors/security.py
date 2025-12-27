from __future__ import annotations
from typing import Any, Dict
from ..shell import ShellRunner


def collect_security(sh: ShellRunner) -> Dict[str, Any]:
    ufw = sh.run(["sudo", "ufw", "status", "verbose"])
    ss = sh.run(["ss", "-ltnp"])
    warnings = sh.run(["sudo", "journalctl", "-p", "warning..alert", "--since", "24 hours ago", "--no-pager"])
    return {
        "ufw_status": ufw.stdout.strip() or ufw.stderr.strip(),
        "listening_ports": ss.stdout.strip(),
        "recent_warnings": warnings.stdout.strip(),
    }
