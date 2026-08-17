from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


class SerperCache:
    def __init__(self, directory: Path):
        self.directory = directory
        self.directory.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def key(payload: dict[str, Any]) -> str:
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def path_for(self, payload: dict[str, Any]) -> Path:
        return self.directory / f"{self.key(payload)}.json"

    def get(self, payload: dict[str, Any]) -> dict[str, Any] | None:
        path = self.path_for(payload)
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else None
        except (OSError, json.JSONDecodeError):
            return None

    def put(self, payload: dict[str, Any], response: dict[str, Any]) -> Path:
        path = self.path_for(payload)
        path.write_text(json.dumps(response, ensure_ascii=False, indent=2), encoding="utf-8")
        return path