#!/usr/bin/env python3
"""
bug-hunter skill — final output wrapper.

Reads JSON from argv[1] with {task_id, verdict, bugs, confidence};
enforces shape and the rule "verdict=clean -> bugs=[]"; writes the result to
AIASE_RESULT_PATH (or ./aiase_result.json when unset).
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path


ALLOWED_VERDICTS = {"buggy", "clean"}
ALLOWED_TYPES = {
    "off_by_one", "null_deref", "type_error", "logic_error",
    "edge_case", "api_misuse", "inefficient", "unhandled_input",
}
ALLOWED_SEVERITIES = {"critical", "high", "medium", "low"}
FENCED_JSON_RE = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.DOTALL | re.IGNORECASE)


def _clamp_confidence(v) -> float:
    try:
        f = float(v)
    except (TypeError, ValueError):
        return 0.0
    return max(0.0, min(1.0, f))


def _sanitize_bug(b: dict) -> dict | None:
    if not isinstance(b, dict):
        return None
    try:
        ls = int(b.get("line_start"))
        le = int(b.get("line_end", ls))
    except (TypeError, ValueError):
        return None
    if ls < 1 or le < ls:
        return None
    sev = str(b.get("severity", "")).strip().lower()
    typ = str(b.get("type", "")).strip().lower()
    if sev not in ALLOWED_SEVERITIES or typ not in ALLOWED_TYPES:
        return None
    return {
        "line_start": ls,
        "line_end": le,
        "severity": sev,
        "type": typ,
        "description": str(b.get("description", "")),
        "suggested_fix": str(b.get("suggested_fix", "")),
    }


def emit_contract(obj: dict) -> int:
    obj = _with_analyzer_evidence(obj)
    verdict = str(obj.get("verdict", "")).strip().lower()
    if verdict not in ALLOWED_VERDICTS:
        verdict = "clean"

    raw_bugs = obj.get("bugs") or []
    if not isinstance(raw_bugs, list):
        raw_bugs = []
    bugs = [b for b in (_sanitize_bug(x) for x in raw_bugs) if b is not None]

    # 規格:verdict=clean 時 bugs[] 必須是 []。
    if verdict == "clean":
        bugs = []
    # 若有 bugs 卻 verdict=clean 已被擋;反之有 bug 但 verdict=buggy ok。
    if verdict == "buggy" and not bugs:
        # buggy 但沒列任何 bug 是 contract 違規,但我們不自動翻為 clean — 留給評分器扣分。
        pass

    out = {
        "task_id": str(obj.get("task_id", "")),
        "verdict": verdict,
        "bugs": bugs,
        "confidence": _clamp_confidence(obj.get("confidence", 0.5)),
    }
    return write_result(out)


def _with_analyzer_evidence(obj: dict) -> dict:
    """Prefer deterministic analyzer output when the original code is available."""
    if not obj.get("code"):
        return obj
    analysis = _run_analyzer(obj)
    if not analysis:
        return obj

    suggested = analysis.get("suggested_bugs") or []
    bad_probes = [
        p for p in analysis.get("probes", [])
        if isinstance(p, dict) and p.get("outcome") in {"crash", "timeout", "mismatch"}
    ]

    out = dict(obj)
    if suggested:
        out["verdict"] = "buggy"
        out["bugs"] = suggested
        out.setdefault("confidence", 0.9)
    elif bad_probes:
        entry_line = int((analysis.get("ast_lines") or {}).get("entry_def") or 1)
        out["verdict"] = "buggy"
        out["bugs"] = [{
            "line_start": entry_line,
            "line_end": entry_line,
            "severity": "high",
            "type": "logic_error",
            "description": "Deterministic probes failed against expected behavior.",
            "suggested_fix": "Re-check the implementation against the task description and add the failing edge case.",
        }]
        out.setdefault("confidence", 0.75)
    else:
        out["verdict"] = "clean"
        out["bugs"] = []
        out.setdefault("confidence", 0.85)
    return out


def _run_analyzer(obj: dict) -> dict:
    payload = {
        "task_id": str(obj.get("task_id", "")),
        "code": str(obj.get("code", "")),
        "task_description": str(obj.get("task_description", "")),
    }
    if obj.get("entry_function"):
        payload["entry_function"] = str(obj.get("entry_function"))
    script = Path(__file__).with_name("analyze.py")
    try:
        proc = subprocess.run(
            [sys.executable, str(script), json.dumps(payload, ensure_ascii=False)],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=10,
        )
    except Exception:
        return {}
    text = proc.stdout.strip()
    match = FENCED_JSON_RE.search(text)
    if match:
        text = match.group(1).strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def write_result(obj: dict) -> int:
    path = Path(os.environ.get("AIASE_RESULT_PATH") or "aiase_result.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[aiase] wrote result to {path}")
    return 0


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        return emit_contract({"task_id": "", "verdict": "clean", "bugs": [], "confidence": 0.0})
    try:
        payload = json.loads(argv[1])
        if not isinstance(payload, dict):
            raise ValueError("payload not an object")
    except (json.JSONDecodeError, ValueError):
        return emit_contract({"task_id": "", "verdict": "clean", "bugs": [], "confidence": 0.0})
    return emit_contract(payload)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
