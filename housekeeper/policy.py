from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal


Risk = Literal["read_only", "safe", "disruptive", "blocked"]


@dataclass
class PolicyDecision:
    risk: Risk
    reason: str


class CommandPolicy:
    """
    v1 policy:
    - allowlist common safe read-only tools
    - allow some safe cleanup/update commands as "safe" or "disruptive"
    - block dangerous patterns
    """

    BLOCK_PATTERNS = [
        r"\brm\b.*\s-.*r",             # rm -r / -rf patterns
        r"\bdd\b",
        r"\bmkfs\b",
        r"\bchmod\b\s+777\b",
        r"\bchown\b\s+-R\b",
        r"\bcurl\b.*\|\s*(sh|bash)",
        r"\bwget\b.*\|\s*(sh|bash)",
        r"\b:\(\)\s*\{\s*:\|\:&\s*\};:\b",  # fork bomb
    ]

    READ_ONLY_ALLOW = {
        "df", "du", "lsblk", "uname", "uptime", "free", "top", "ps",
        "journalctl", "systemctl", "ss",
        "apt", "apt-get",
    }

    def classify(self, cmd: list[str]) -> PolicyDecision:
        s = " ".join(cmd).strip()

        for pat in self.BLOCK_PATTERNS:
            if re.search(pat, s):
                return PolicyDecision("blocked", f"Blocked by pattern: {pat}")

        if not cmd:
            return PolicyDecision("blocked", "Empty command")

        exe = cmd[0]

        # ---- NEW: controlled sudo support ----
        if exe == "sudo":
            if len(cmd) < 2:
                return PolicyDecision("blocked", "sudo without subcommand")

            sub = cmd[1]

            # allow sudo apt / apt-get
            if sub in ("apt", "apt-get"):
                if any(x in cmd for x in ["install", "remove", "purge", "upgrade", "dist-upgrade"]):
                    return PolicyDecision("disruptive", "Package changes require approval")
                return PolicyDecision("safe", "sudo apt read-only or metadata operation")

            # allow sudo ufw
            if sub == "ufw":
                return PolicyDecision("disruptive", "Firewall changes require approval")

            # allow sudo journalctl vacuum
            if sub == "journalctl" and "--vacuum-time" in cmd:
                return PolicyDecision("safe", "Log vacuum (approval required)")

            # allow sudo fstrim
            if sub == "fstrim":
                return PolicyDecision("safe", "SSD TRIM (approval required)")

            return PolicyDecision("blocked", f"sudo subcommand not allowlisted: {sub}")

        # ---- existing logic ----
        if exe in self.READ_ONLY_ALLOW:
            if exe in ("apt", "apt-get"):
                if any(x in cmd for x in ["install", "remove", "purge", "upgrade", "dist-upgrade"]):
                    return PolicyDecision("disruptive", "Package changes require approval")
                return PolicyDecision("read_only", "Read-only package query")

            if exe == "systemctl" and any(x in cmd for x in ["restart", "stop", "disable", "mask"]):
                return PolicyDecision("disruptive", "Service changes require approval")

            return PolicyDecision("read_only", "Read-only command")

        return PolicyDecision("blocked", f"Executable not allowlisted: {exe}")

