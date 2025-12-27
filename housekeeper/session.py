from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional


def default_data_dir() -> Path:
    return Path.home() / ".local" / "share" / "housekeeper"


class SessionLogger:
    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = base_dir or default_data_dir()
        self.base_dir.mkdir(parents=True, exist_ok=True)
        (self.base_dir / "audits").mkdir(exist_ok=True)
        (self.base_dir / "plans").mkdir(exist_ok=True)
        (self.base_dir / "runs").mkdir(exist_ok=True)

    def _now_id(self) -> str:
        return datetime.now().strftime("%Y%m%d_%H%M%S")

    def write_audit(self, audit: Dict[str, Any]) -> Path:
        p = self.base_dir / "audits" / f"audit_{self._now_id()}.json"
        p.write_text(json.dumps(audit, indent=2))
        return p

    def write_plan(self, plan: Dict[str, Any]) -> Path:
        p = self.base_dir / "plans" / f"plan_{self._now_id()}.json"
        p.write_text(json.dumps(plan, indent=2))
        return p

    def append_run_event(self, run_id: str, event: Dict[str, Any]) -> Path:
        p = self.base_dir / "runs" / f"run_{run_id}.jsonl"
        event2 = {"ts": datetime.now().isoformat(timespec="seconds"), **event}
        with p.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event2) + "\n")
        return p

    def to_jsonable(self, obj: Any) -> Any:
        if is_dataclass(obj):
            return asdict(obj)
        return obj
