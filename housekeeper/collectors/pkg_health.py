from __future__ import annotations

from typing import Any, Dict

from ..shell import ShellRunner


def collect_pkg_health(sh: ShellRunner) -> Dict[str, Any]:
    """
    Package health checks (mostly read-only):
    - dpkg --audit : reports partially installed / broken packages
    - apt-mark showhold : lists held packages (won't upgrade)
    - apt-get -s -f install : simulation of dependency fix
    """
    dpkg_audit = sh.run(["dpkg", "--audit"])
    holds = sh.run(["apt-mark", "showhold"])
    fix_sim = sh.run(["apt-get", "-s", "-f", "install"])

    return {
        "dpkg_audit_rc": dpkg_audit.returncode,
        "dpkg_audit": dpkg_audit.stdout.strip() or dpkg_audit.stderr.strip(),
        "held_packages": holds.stdout.strip(),
        "fix_simulation": fix_sim.stdout.strip(),
    }
