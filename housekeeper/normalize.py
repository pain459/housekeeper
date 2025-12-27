from __future__ import annotations
from typing import List, Tuple

def normalize(argv: List[str]) -> Tuple[List[str], str | None]:
    """
    Safe, conservative rewrites for common planner mistakes.
    Returns (new_argv, note). If no change, note is None.
    """
    # Fix invalid: apt-get update -s  (or sudo apt-get update -s)
    # Replace with: apt-get -s dist-upgrade (still a safe simulation)
    if argv in (["apt-get", "update", "-s"], ["apt-get", "update", "--simulate"]):
        return ["apt-get", "-s", "dist-upgrade"], "Rewrote invalid `apt-get update -s` to `apt-get -s dist-upgrade`."
    if argv[:4] == ["sudo", "apt-get", "update", "-s"]:
        return ["apt-get", "-s", "dist-upgrade"], "Rewrote invalid `sudo apt-get update -s` to `apt-get -s dist-upgrade`."
    if argv[:4] == ["sudo", "apt-get", "update", "--simulate"]:
        return ["apt-get", "-s", "dist-upgrade"], "Rewrote invalid `sudo apt-get update --simulate` to `apt-get -s dist-upgrade`."

    # Normalize apt update to apt-get update (either is fine, but keep consistent)
    # (Optional) You can remove this if you prefer apt.
    return argv, None
