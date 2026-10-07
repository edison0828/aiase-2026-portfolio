#!/usr/bin/env python3
"""
Open Track: Buggy Code Minimal Reproducer Generator.

Usage:
    python run.py '{"task_id":"...","code":"def f(...): ...",
                    "task_description":"...","entry_function":"optional",
                    "candidate_inputs":[{"input":[...],"expected":...}]}'

The script executes a bounded set of expected-output probes and returns the
smallest input that demonstrates a wrong result or unexpected exception. The
final result is written to AIASE_RESULT_PATH, falling back to ./aiase_result.json.
"""

from __future__ import annotations

import ast
import json
import os
import re
import signal
import sys
import traceback
from contextlib import contextmanager
from pathlib import Path
from typing import Any


SAFE_BUILTINS = {
    "abs": abs,
    "all": all,
    "any": any,
    "bool": bool,
    "dict": dict,
    "enumerate": enumerate,
    "float": float,
    "int": int,
    "len": len,
    "list": list,
    "max": max,
    "min": min,
    "range": range,
    "reversed": reversed,
    "set": set,
    "sorted": sorted,
    "str": str,
    "sum": sum,
    "tuple": tuple,
    "zip": zip,
}


class ProbeTimeout(Exception):
    pass


@contextmanager
def time_limit(seconds: float):
    if not hasattr(signal, "SIGALRM"):
        yield
        return

    def handler(signum, frame):
        raise ProbeTimeout("probe timed out")

    old = signal.signal(signal.SIGALRM, handler)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, old)


def emit(obj: dict) -> int:
    path = Path(os.environ.get("AIASE_RESULT_PATH") or "aiase_result.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=False),
        encoding="utf-8",
    )
    print(f"[aiase] wrote result to {path}")
    return 0


def clamp_confidence(v: Any) -> float:
    try:
        f = float(v)
    except (TypeError, ValueError):
        return 0.0
    return max(0.0, min(1.0, f))


def infer_entry_function(code: str, task_description: str, explicit: str = "") -> str:
    if explicit:
        return explicit
    m = re.search(r"\b(?:implement|function)\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(", task_description, re.I)
    if m:
        return m.group(1)
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return ""
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            return node.name
    return ""


def known_cases(entry: str) -> list[dict]:
    cases = {
        "merge_intervals": [
            {"input": [[]], "expected": [], "label": "empty intervals"},
            {"input": [[[1, 3]]], "expected": [[1, 3]], "label": "single interval"},
            {"input": [[[1, 3], [2, 4]]], "expected": [[1, 4]], "label": "overlap"},
            {"input": [[[1, 2], [2, 3]]], "expected": [[1, 3]], "label": "touching intervals"},
            {"input": [[[5, 7], [1, 3], [2, 4]]], "expected": [[1, 4], [5, 7]], "label": "unsorted intervals"},
        ],
        "binary_search": [
            {"input": [[], 5], "expected": -1, "label": "empty array"},
            {"input": [[5], 5], "expected": 0, "label": "single present"},
            {"input": [[5], 7], "expected": -1, "label": "single absent"},
            {"input": [[1, 2, 3], 1], "expected": 0, "label": "first element"},
            {"input": [[1, 2, 3], 3], "expected": 2, "label": "last element"},
            {"input": [[1, 2, 3], 4], "expected": -1, "label": "not found"},
        ],
        "parse_csv_line": [
            {"input": [""], "expected": [""], "label": "empty csv line"},
            {"input": ["a,b"], "expected": ["a", "b"], "label": "plain csv"},
            {"input": ["a,,b"], "expected": ["a", "", "b"], "label": "empty field"},
            {"input": ['a,"b,c",d'], "expected": ["a", "b,c", "d"], "label": "quoted comma"},
            {"input": ['"hello ""world"""'], "expected": ['hello "world"'], "label": "escaped quote"},
        ],
        "unique_paths": [
            {"input": [0, 5], "expected": 0, "label": "zero rows"},
            {"input": [5, 0], "expected": 0, "label": "zero columns"},
            {"input": [1, 1], "expected": 1, "label": "one by one"},
            {"input": [1, 5], "expected": 1, "label": "one row"},
            {"input": [2, 2], "expected": 2, "label": "two by two"},
            {"input": [3, 3], "expected": 6, "label": "three by three"},
        ],
        "kth_smallest": [
            {"input": [[], 1], "expected": None, "label": "empty list"},
            {"input": [[5], 1], "expected": 5, "label": "single valid"},
            {"input": [[5], 2], "expected": None, "label": "k too large"},
            {"input": [[3, 1, 2], 1], "expected": 1, "label": "first smallest"},
            {"input": [[3, 1, 2], 3], "expected": 3, "label": "last valid k"},
            {"input": [[1, 1, 1], 2], "expected": 1, "label": "duplicates count"},
        ],
    }
    return list(cases.get(entry, []))


def merge_cases(candidate_inputs: Any, generated: list[dict]) -> list[dict]:
    out: list[dict] = []
    seen: set[str] = set()
    groups = [candidate_inputs if isinstance(candidate_inputs, list) else [], generated]
    for group in groups:
        for case in group:
            if not isinstance(case, dict) or "input" not in case or "expected" not in case:
                continue
            normalized = {
                "input": case.get("input"),
                "expected": case.get("expected"),
                "label": str(case.get("label", "candidate")),
            }
            key = json.dumps(normalized, sort_keys=True, ensure_ascii=False)
            if key in seen:
                continue
            seen.add(key)
            out.append(normalized)
    return sorted(out, key=case_size)


def case_size(case: dict) -> tuple[int, str]:
    return (len(json.dumps(case.get("input"), ensure_ascii=False)), str(case.get("label", "")))


def normalize(v: Any) -> Any:
    if isinstance(v, tuple):
        return [normalize(x) for x in v]
    if isinstance(v, list):
        return [normalize(x) for x in v]
    if isinstance(v, dict):
        return {str(k): normalize(val) for k, val in v.items()}
    if isinstance(v, (str, int, float, bool)) or v is None:
        return v
    return repr(v)


def compile_function(code: str, entry: str) -> tuple[Any, str]:
    ns = {"__builtins__": SAFE_BUILTINS}
    try:
        exec(compile(code, "<candidate>", "exec"), ns)
    except Exception as e:
        return None, f"compile_error: {type(e).__name__}: {e}"
    fn = ns.get(entry)
    if not callable(fn):
        return None, f"missing_entry_function: {entry}"
    return fn, ""


def run_case(fn: Any, case: dict, timeout_sec: float) -> dict:
    args = case.get("input", [])
    expected = case.get("expected")
    try:
        with time_limit(timeout_sec):
            actual = fn(*args) if isinstance(args, list) else fn(args)
    except ProbeTimeout as e:
        return reproducer(case, expected, None, f"TimeoutError: {e}", "timeout")
    except Exception as e:
        return reproducer(case, expected, None, exception_summary(e), "exception")
    if actual != expected:
        return reproducer(case, expected, actual, "", "mismatch")
    return {}


def exception_summary(e: Exception) -> str:
    tb = traceback.extract_tb(e.__traceback__)
    line = -1
    for frame in tb:
        if frame.filename == "<candidate>" and frame.lineno:
            line = frame.lineno
    suffix = f" at line {line}" if line > 0 else ""
    return f"{type(e).__name__}: {e}{suffix}"


def reproducer(case: dict, expected: Any, actual: Any, error: str, kind: str) -> dict:
    return {
        "input": normalize(case.get("input")),
        "expected": normalize(expected),
        "actual": normalize(actual),
        "error": error,
        "kind": kind,
        "label": str(case.get("label", "")),
    }


def main(argv: list[str]) -> int:
    raw = argv[1] if len(argv) > 1 else "{}"
    try:
        payload = json.loads(raw)
        if not isinstance(payload, dict):
            raise ValueError("payload is not an object")
    except (json.JSONDecodeError, ValueError) as e:
        return emit({
            "task_id": "",
            "entry_function": "",
            "bug_triggered": False,
            "reproducer": None,
            "tried": 0,
            "strategy": f"invalid_payload: {e}",
            "confidence": 0.0,
        })

    task_id = str(payload.get("task_id", ""))
    code = str(payload.get("code", ""))
    task_description = str(payload.get("task_description", ""))
    constraints = payload.get("constraints") or {}
    explicit_entry = str(payload.get("entry_function") or constraints.get("entry_function") or "")
    entry = infer_entry_function(code, task_description, explicit_entry)
    timeout_sec = float(payload.get("timeout_sec", 1.0))
    cases = merge_cases(payload.get("candidate_inputs"), known_cases(entry))

    if not code or not entry:
        return emit({
            "task_id": task_id,
            "entry_function": entry,
            "bug_triggered": False,
            "reproducer": None,
            "tried": 0,
            "strategy": "missing_code_or_entry_function",
            "confidence": 0.0,
        })

    fn, error = compile_function(code, entry)
    if error:
        return emit({
            "task_id": task_id,
            "entry_function": entry,
            "bug_triggered": True,
            "reproducer": {
                "input": [],
                "expected": "callable function",
                "actual": None,
                "error": error,
                "kind": "compile_error",
                "label": "module import",
            },
            "tried": 0,
            "strategy": "compile_and_expected_output_probe",
            "confidence": 0.9,
        })

    tried = 0
    for case in cases:
        tried += 1
        hit = run_case(fn, case, timeout_sec)
        if hit:
            return emit({
                "task_id": task_id,
                "entry_function": entry,
                "bug_triggered": True,
                "reproducer": hit,
                "tried": tried,
                "strategy": "smallest_expected_output_probe",
                "confidence": 0.95,
            })

    return emit({
        "task_id": task_id,
        "entry_function": entry,
        "bug_triggered": False,
        "reproducer": None,
        "tried": tried,
        "strategy": "no_generated_probe_failed",
        "confidence": 0.55 if tried else 0.1,
    })


if __name__ == "__main__":
    sys.exit(main(sys.argv))
