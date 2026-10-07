# Source: TAICA AIASE 2026 HW4 Python starter (ktchuang/TAICA_AIASE2026).
# Student-completed scoring/persistence retained; portfolio edits only simplify scaffold comments.
"""持久層：把記憶存成 JSON 檔，重啟後讀得回來，並用 id 去重。
load()/_persist()/add() 為作業完成的持久化實作。"""
from __future__ import annotations
import json
import os


class JsonStore:
    def __init__(self, path: str):
        self.path = path
        self.items: list[dict] = []
        self.load()

    def load(self) -> None:
        """Load a JSON list; missing or unreadable input becomes an empty store."""
        if not os.path.exists(self.path):
            self.items = []
            return

        try:
            with open(self.path, encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError):
            self.items = []
            return

        self.items = data if isinstance(data, list) else []

    def _persist(self) -> None:
        """Write current observations as UTF-8 JSON."""
        parent = os.path.dirname(self.path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.items, f, ensure_ascii=False, indent=2)

    def add(self, obs: dict) -> bool:
        """Persist a new observation unless its id already exists."""
        if any(o.get("id") == obs.get("id") for o in self.items):
            return False
        self.items.append(obs)
        self._persist()
        return True

    def all(self) -> list[dict]:
        return list(self.items)

    def clear(self) -> None:
        self.items = []
        self._persist()
