from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal


Risk = Literal["read_only", "safe", "disruptive", "blocked"]


@dataclass(frozen=True)
class PolicyDecision:
    risk: Risk
    reason: str


class CommandPolicy:
    """
    Conservative command policy.

    Design principles:
    - Audit collectors may run read-only commands automatically.
    - Apply will only execute commands that are allowlisted here,
      and only after user confirmation (handled by apply layer).
    - 'sudo' is supported, but only for a tight allowlist of subcommands.
    """

    # Block obvious foot-guns and "download & execute" patterns
    BLOCK_PATTERNS = [
        r"\brm\b.*\s-(?:rf|fr|r)\b",         # rm -r / -rf / -fr
        r"\bdd\b",                          # raw disk writes
        r"\bmkfs(\.\w+)?\b",                # formatting filesystems
        r"\bmount\b.*\s-o\s+.*\b",          # mounting with options (too broad for v1)
        r"\bchmod\b\s+777\b",               # insecure perms
        r"\bchown\b\s+-R\b",                # recursive ownership changes
        r"\bcurl\b.*\|\s*(sh|bash)\b",      # curl | sh
        r"\bwget\b.*\|\s*(sh|bash)\b",      # wget | sh
        r"\b:\(\)\s*\{\s*:\|\:&\s*\};:\b",  # fork bomb
    ]

    READ_ONLY_ALLOW = {
        "df", "du", "lsblk", "uname", "uptime", "free", "top", "ps",
        "journalctl", "systemctl", "ss",
        "apt", "apt-get",
    }

    # Package-changing apt operations (always disruptive)
    APT_MUTATING = {"install", "remove", "purge", "upgrade", "dist-upgrade", "full-upgrade"}

    # systemctl operations that can disrupt services
    SYSTEMCTL_MUTATING = {"restart", "stop", "disable", "mask", "enable"}

    # ufw operations that mutate firewall state/rules
    UFW_MUTATING = {"enable", "disable", "reset", "delete", "allow", "deny", "reject", "limit", "insert", "route"}

    def _blocked_by_pattern(self, s: str) -> str | None:
        for pat in self.BLOCK_PATTERNS:
            if re.search(pat, s):
                return pat
        return None

    def classify(self, cmd: list[str]) -> PolicyDecision:
        if not cmd:
            return PolicyDecision("blocked", "Empty command")

        s = " ".join(cmd).strip()
        pat = self._blocked_by_pattern(s)
        if pat:
            return PolicyDecision("blocked", f"Blocked by pattern: {pat}")

        exe = cmd[0]

        # ---- controlled sudo support ----
        if exe == "sudo":
            if len(cmd) < 2:
                return PolicyDecision("blocked", "sudo without subcommand")

            sub = cmd[1]
            subcmd = cmd[2] if len(cmd) >= 3 else None

            # sudo apt / apt-get
            if sub in ("apt", "apt-get"):
                # If any mutating token appears anywhere, treat as disruptive
                if any(tok in self.APT_MUTATING for tok in cmd):
                    return PolicyDecision("disruptive", "Package changes require approval")
                return PolicyDecision("safe", "sudo apt operation (approval required)")

            # sudo journalctl vacuum (time- or size-based)
            if sub == "journalctl":
                if "--vacuum-time" in cmd or "--vacuum-size" in cmd:
                    return PolicyDecision("safe", "Log vacuum (approval required)")
                # Keep other sudo journalctl usages blocked for v1
                return PolicyDecision("blocked", "sudo journalctl allowed only with --vacuum-time/--vacuum-size")

            # sudo fstrim
            if sub == "fstrim":
                return PolicyDecision("safe", "SSD TRIM (approval required)")

            # sudo ufw
            if sub == "ufw":
                # read-only status/show should be safe
                if subcmd in ("status", "status-numbered", "show"):
                    return PolicyDecision("safe", "Firewall status check (approval required)")
                # anything that changes state/rules is disruptive
                if any(tok in self.UFW_MUTATING for tok in cmd):
                    return PolicyDecision("disruptive", "Firewall rule changes require approval")
                # default to disruptive if we can't be sure
                return PolicyDecision("disruptive", "Firewall operation requires approval")

            return PolicyDecision("blocked", f"sudo subcommand not allowlisted: {sub}")

        # ---- non-sudo allowlist ----
        if exe in self.READ_ONLY_ALLOW:
            if exe in ("apt", "apt-get"):
                # non-sudo package changes are still disruptive (though they may fail without sudo)
                if any(tok in self.APT_MUTATING for tok in cmd):
                    return PolicyDecision("disruptive", "Package changes require approval")
                return PolicyDecision("read_only", "Read-only package query")

            if exe == "systemctl":
                if any(tok in self.SYSTEMCTL_MUTATING for tok in cmd):
                    return PolicyDecision("disruptive", "Service changes require approval")
                return PolicyDecision("read_only", "Read-only systemctl query")

            return PolicyDecision("read_only", "Read-only command")

        return PolicyDecision("blocked", f"Executable not allowlisted: {exe}")
