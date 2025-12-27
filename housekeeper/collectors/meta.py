from __future__ import annotations
from typing import Any, Dict
from ..shell import ShellRunner


def collect_meta(sh: ShellRunner) -> Dict[str, Any]:
    uname = sh.run(["uname", "-a"])
    uptime = sh.run(["uptime"])
    return {
        "uname": uname.stdout.strip(),
        "uptime": uptime.stdout.strip(),
    }
