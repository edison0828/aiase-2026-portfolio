from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from models import DatabaseError, Note, Paper


def empty_database_state() -> dict[str, Any]:

    return {
        "next_paper_id": 1,
        "next_note_id": 1,
        "papers": [],
        "notes": [],
    }


def load_database(path: str) -> dict[str, Any]:

    db_path = Path(path)
    if not db_path.exists():
        return empty_database_state()

    try:
        raw = json.loads(db_path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise ValueError("database root must be an object")

        papers_raw = raw.get("papers", [])
        notes_raw = raw.get("notes", [])
        if not isinstance(papers_raw, list) or not isinstance(notes_raw, list):
            raise ValueError("papers and notes must be lists")

        papers = [Paper.from_dict(item) for item in papers_raw]
        notes = [Note.from_dict(item) for item in notes_raw]

        next_paper_id = max(int(raw.get("next_paper_id", 1)), _next_id(papers))
        next_note_id = max(int(raw.get("next_note_id", 1)), _next_id(notes))

        return {
            "next_paper_id": next_paper_id,
            "next_note_id": next_note_id,
            "papers": papers,
            "notes": notes,
        }
    except (OSError, json.JSONDecodeError, TypeError, ValueError, KeyError) as exc:
        raise DatabaseError("Error: failed to read database") from exc


def save_database(path: str, state: dict[str, Any]) -> None:

    db_path = Path(path)
    payload = {
        "next_paper_id": max(int(state["next_paper_id"]), _next_id(state["papers"])),
        "next_note_id": max(int(state["next_note_id"]), _next_id(state["notes"])),
        "papers": [paper.to_dict() for paper in state["papers"]],
        "notes": [note.to_dict() for note in state["notes"]],
    }

    try:
        db_path.parent.mkdir(parents=True, exist_ok=True)
        db_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except (OSError, TypeError, KeyError) as exc:
        raise DatabaseError("Error: failed to write database") from exc


def _next_id(items: list[Any]) -> int:

    max_id = max((item.id for item in items), default=0)
    return max_id + 1

