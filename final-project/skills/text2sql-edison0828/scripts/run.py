#!/usr/bin/env python3
"""
text2sql skill — final output wrapper.

Reads a JSON payload from argv[1] containing {task_id, sql, rationale, confidence},
validates the contract minimally, and writes the Basic Track output contract to
AIASE_RESULT_PATH (or ./aiase_result.json when unset).

The LLM (Hermes agent) is responsible for filling in `sql` (via the Procedure in
SKILL.md). This script only enforces the deterministic output shape.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path


CONTRACT_FIELDS = ("task_id", "sql", "rationale", "confidence")
FENCED_SQL_RE = re.compile(r"^\s*```(?:sql)?\s*(.*?)\s*```\s*$", re.DOTALL | re.IGNORECASE)


def emit_contract(obj: dict) -> int:
    out = {
        "task_id": str(obj.get("task_id", "")),
        "sql": _clean_sql(obj.get("sql", "")),
        "rationale": str(obj.get("rationale", "")),
        "confidence": _clamp_confidence(obj.get("confidence", 0.5)),
    }
    # 任何 extra fields 一律忽略(規格書 §1.4 #3)。
    return write_result(out)


def write_result(obj: dict) -> int:
    path = Path(os.environ.get("AIASE_RESULT_PATH") or "aiase_result.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[aiase] wrote result to {path}")
    return 0


def _clean_sql(v) -> str:
    sql = str(v or "").strip()
    m = FENCED_SQL_RE.match(sql)
    if m:
        sql = m.group(1).strip()
    return sql


def _clamp_confidence(v) -> float:
    try:
        f = float(v)
    except (TypeError, ValueError):
        return 0.0
    if f < 0.0:
        return 0.0
    if f > 1.0:
        return 1.0
    return f


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        # 失敗也要產出契約 JSON,不可只噴錯(規格書 §1.4 #7)。
        return emit_contract({
            "task_id": "",
            "sql": "",
            "rationale": "run.py invoked without argv payload",
            "confidence": 0.0,
        })

    try:
        payload = json.loads(argv[1])
        if not isinstance(payload, dict):
            raise ValueError("payload not an object")
    except (json.JSONDecodeError, ValueError) as e:
        return emit_contract({
            "task_id": "",
            "sql": "",
            "rationale": f"invalid argv JSON: {e}",
            "confidence": 0.0,
        })

    return emit_contract(payload)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
