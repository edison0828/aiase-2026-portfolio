#!/usr/bin/env python3
"""
code-author skill — final output wrapper.

Reads JSON from argv[1] with the fields needed by the contract, validates shape,
writes the contract to AIASE_RESULT_PATH (or ./aiase_result.json when unset).
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path


FENCED_PY_RE = re.compile(r"^\s*```(?:python|py)?\s*(.*?)\s*```\s*$", re.DOTALL | re.IGNORECASE)


def _clamp_confidence(v) -> float:
    try:
        f = float(v)
    except (TypeError, ValueError):
        return 0.0
    return max(0.0, min(1.0, f))


def _clean_code(v) -> str:
    code = str(v or "").strip()
    m = FENCED_PY_RE.match(code)
    if m:
        code = m.group(1).strip()
    return code


def _int_or_zero(v) -> int:
    try:
        return int(v)
    except (TypeError, ValueError):
        return 0


def emit_contract(obj: dict) -> int:
    self_test = obj.get("self_test_results") or {}
    if not isinstance(self_test, dict):
        self_test = {"passed": 0, "failed": 0, "_warning": "non-object coerced"}
    self_test.setdefault("passed", 0)
    self_test.setdefault("failed", 0)

    out = {
        "task_id": str(obj.get("task_id", "")),
        "code": _clean_code(obj.get("code", "")),
        "loc": _int_or_zero(obj.get("loc", 0)),
        "self_test_results": self_test,
        "rationale": str(obj.get("rationale", "")),
        "confidence": _clamp_confidence(obj.get("confidence", 0.5)),
    }
    return write_result(out)


def write_result(obj: dict) -> int:
    path = Path(os.environ.get("AIASE_RESULT_PATH") or "aiase_result.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[aiase] wrote result to {path}")
    return 0


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        return emit_contract({
            "task_id": "", "code": "", "loc": 0,
            "self_test_results": {"passed": 0, "failed": 0},
            "rationale": "run.py invoked without argv payload",
            "confidence": 0.0,
        })
    try:
        payload = json.loads(argv[1])
        if not isinstance(payload, dict):
            raise ValueError("payload not an object")
    except (json.JSONDecodeError, ValueError) as e:
        return emit_contract({
            "task_id": "", "code": "", "loc": 0,
            "self_test_results": {"passed": 0, "failed": 0},
            "rationale": f"invalid argv JSON: {e}",
            "confidence": 0.0,
        })
    return emit_contract(payload)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
