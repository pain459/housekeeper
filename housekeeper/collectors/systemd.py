from __future__ import annotations
from typing import Any, Dict
from ..shell import ShellRunner


def collect_systemd(sh: ShellRunner) -> Dict[str, Any]:
    failed = sh.run(["systemctl", "--failed", "--no-pager"])
    return {"failed_units": failed.stdout.strip()}
