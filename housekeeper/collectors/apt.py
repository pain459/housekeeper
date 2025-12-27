from __future__ import annotations
from typing import Any, Dict
from ..shell import ShellRunner


def collect_apt(sh: ShellRunner) -> Dict[str, Any]:
    # read-only audit signals
    upd = sh.run(["apt", "update"])
    upg = sh.run(["apt", "list", "--upgradable"])
    sim = sh.run(["apt-get", "-s", "dist-upgrade"])

    return {
        "apt_update_rc": upd.returncode,
        "upgradable": upg.stdout.strip(),
        "dist_upgrade_simulation": sim.stdout.strip(),
    }
