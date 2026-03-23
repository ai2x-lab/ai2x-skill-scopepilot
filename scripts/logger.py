from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class ActionLogger:
    text_log_path: Path | None = None
    json_log_path: Path | None = None
    entries: list[dict[str, Any]] = field(default_factory=list)

    def log(self, event: str, **payload: Any) -> None:
        entry = {
            "timestamp": utc_now(),
            "event": event,
            **payload,
        }
        self.entries.append(entry)

        if self.text_log_path is not None:
            self.text_log_path.parent.mkdir(parents=True, exist_ok=True)
            line = json.dumps(entry, ensure_ascii=True)
            with self.text_log_path.open("a", encoding="utf-8") as handle:
                handle.write(line + "\n")

    def finalize(self, summary: dict[str, Any]) -> None:
        result = {
            "summary": summary,
            "entries": self.entries,
        }
        if self.json_log_path is not None:
            self.json_log_path.parent.mkdir(parents=True, exist_ok=True)
            with self.json_log_path.open("w", encoding="utf-8") as handle:
                json.dump(result, handle, indent=2, ensure_ascii=True)
