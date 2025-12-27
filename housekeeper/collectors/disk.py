from __future__ import annotations
from typing import Any, Dict
from ..shell import ShellRunner


def collect_disk(sh: ShellRunner) -> Dict[str, Any]:
    df = sh.run(["df", "-hT"])
    journal_usage = sh.run(["journalctl", "--disk-usage"])
    lsblk = sh.run(["lsblk", "-f"])
    return {
        "df": df.stdout.strip(),
        "journalctl_disk_usage": journal_usage.stdout.strip(),
        "lsblk": lsblk.stdout.strip(),
    }
