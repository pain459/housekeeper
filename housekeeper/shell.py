from __future__ import annotations

import subprocess
from dataclasses import dataclass
from typing import Optional, Sequence


@dataclass
class CmdResult:
    cmd: list[str]
    returncode: int
    stdout: str
    stderr: str


class ShellRunner:
    def __init__(self, *, default_timeout_s: int = 20, max_output_chars: int = 120_000):
        self.default_timeout_s = default_timeout_s
        self.max_output_chars = max_output_chars

    def run(
        self,
        cmd: Sequence[str],
        *,
        timeout_s: Optional[int] = None,
        check: bool = False,
    ) -> CmdResult:
        timeout_s = timeout_s or self.default_timeout_s

        p = subprocess.run(
            list(cmd),
            text=True,
            capture_output=True,
            timeout=timeout_s,
        )

        # truncate to keep logs + prompts small
        out = (p.stdout or "")[: self.max_output_chars]
        err = (p.stderr or "")[: self.max_output_chars]

        if check and p.returncode != 0:
            raise RuntimeError(f"Command failed rc={p.returncode}: {cmd}\n{err}")

        return CmdResult(cmd=list(cmd), returncode=p.returncode, stdout=out, stderr=err)
