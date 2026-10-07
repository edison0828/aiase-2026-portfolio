#!/usr/bin/env python3
"""Repo-root fallback result writer for AIASE file-based grading.

Some Hermes runs execute `python3 scripts/run.py ...` from the repository root
instead of changing into the selected skill directory first. The official skill
wrappers still live under `skills/<skill>/scripts/run.py`; this small fallback
accepts the same JSON payloads and writes the result contract to
`AIASE_RESULT_PATH`.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path


FENCED_SQL_RE = re.compile(r"^\s*```(?:sql)?\s*(.*?)\s*```\s*$", re.DOTALL | re.IGNORECASE)
FENCED_PY_RE = re.compile(r"^\s*```(?:python|py)?\s*(.*?)\s*```\s*$", re.DOTALL | re.IGNORECASE)


def _confidence(v) -> float:
    try:
        f = float(v)
    except (TypeError, ValueError):
        return 0.0
    return max(0.0, min(1.0, f))


def _clean(v, pattern: re.Pattern[str]) -> str:
    text = str(v or "").strip()
    m = pattern.match(text)
    return m.group(1).strip() if m else text


def _write(obj: dict) -> int:
    path = Path(os.environ.get("AIASE_RESULT_PATH") or "aiase_result.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[aiase-root] wrote result to {path}")
    return 0


def _text2sql(obj: dict) -> dict:
    return {
        "task_id": str(obj.get("task_id", "")),
        "sql": _clean(obj.get("sql", ""), FENCED_SQL_RE),
        "rationale": str(obj.get("rationale", "")),
        "confidence": _confidence(obj.get("confidence", 0.5)),
    }


def _code_author(obj: dict) -> dict:
    self_test = obj.get("self_test_results") or {}
    if not isinstance(self_test, dict):
        self_test = {"passed": 0, "failed": 0}
    self_test.setdefault("passed", 0)
    self_test.setdefault("failed", 0)
    try:
        loc = int(obj.get("loc", 0))
    except (TypeError, ValueError):
        loc = 0
    return {
        "task_id": str(obj.get("task_id", "")),
        "code": _clean(obj.get("code", ""), FENCED_PY_RE),
        "loc": loc,
        "self_test_results": self_test,
        "rationale": str(obj.get("rationale", "")),
        "confidence": _confidence(obj.get("confidence", 0.5)),
    }


def _bug_hunter(obj: dict) -> dict:
    # Delegate to the richer bug-hunter wrapper when possible; it can rerun the
    # analyzer and repair model-produced line ranges.
    skill_run = Path(__file__).resolve().parents[1] / "skills" / "bug-hunter-edison0828" / "scripts" / "run.py"
    if skill_run.exists():
        import subprocess

        proc = subprocess.run([sys.executable, str(skill_run), json.dumps(obj, ensure_ascii=False)])
        raise SystemExit(proc.returncode)
    return {
        "task_id": str(obj.get("task_id", "")),
        "verdict": str(obj.get("verdict", "clean")).lower(),
        "bugs": obj.get("bugs") if isinstance(obj.get("bugs"), list) else [],
        "confidence": _confidence(obj.get("confidence", 0.5)),
    }


def main(argv: list[str]) -> int:
    try:
        obj = json.loads(argv[1]) if len(argv) > 1 else {}
    except json.JSONDecodeError:
        obj = {}
    if not isinstance(obj, dict):
        obj = {}

    if "verdict" in obj or "bugs" in obj:
        return _write(_bug_hunter(obj))
    if "code" in obj and "sql" not in obj:
        return _write(_code_author(obj))
    return _write(_text2sql(obj))


if __name__ == "__main__":
    sys.exit(main(sys.argv))
