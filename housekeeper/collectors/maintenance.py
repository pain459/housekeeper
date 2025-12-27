from __future__ import annotations

from typing import Any, Dict

from ..shell import ShellRunner


def collect_maintenance(sh: ShellRunner) -> Dict[str, Any]:
    """
    Maintenance-related signals (read-only):
    - journal size
    - fstrim.timer state (weekly SSD TRIM scheduler)
    """
    journal_usage = sh.run(["journalctl", "--disk-usage"])
    fstrim_timer = sh.run(["systemctl", "status", "fstrim.timer", "--no-pager"])

    return {
        "journalctl_disk_usage": journal_usage.stdout.strip(),
        "fstrim_timer_status": fstrim_timer.stdout.strip() or fstrim_timer.stderr.strip(),
    }
