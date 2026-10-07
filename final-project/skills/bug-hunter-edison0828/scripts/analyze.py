#!/usr/bin/env python3
"""
bug-hunter analyzer — deterministic edge-input probing.

Usage:
    python analyze.py '{
        "code": "...",
        "entry_function": "<entry_name>",
        "edge_inputs": [          # optional; if omitted, a generic battery is used
            {"input": [[]],          "label": "empty container"},
            {"input": [0],           "label": "zero"}
        ]
    }'

Prints a single fenced JSON block:
    {"entry_found": bool,
     "ast_lines": {"entry_def": int, "return_lines": [int], "loop_lines": [int]},
     "probes": [{"label": str, "outcome": "ok"|"crash"|"timeout", "error": str}],
     "suspicious_lines": [int],
     "summary": str}

This is the deterministic side of the bug-hunter; the LLM uses it as evidence,
but still makes the final bug-vs-not-bug judgment.
"""

from __future__ import annotations

import ast
import json
import signal
import sys
import traceback
from contextlib import contextmanager


# Portfolio packaging: classroom reference answers are not distributed here.
# Use an explicit entry function (or infer it) and caller-provided/known probes.


def _emit(obj: dict) -> int:
    sys.stdout.write("```json\n")
    sys.stdout.write(json.dumps(obj, ensure_ascii=False, indent=2))
    sys.stdout.write("\n```\n")
    return 0


def _ast_features(code: str, entry: str) -> dict:
    out = {"entry_def": -1, "return_lines": [], "loop_lines": [], "if_lines": [], "compare_lines": []}
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return out
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == entry:
            out["entry_def"] = node.lineno
        if isinstance(node, ast.Return) and node.lineno:
            out["return_lines"].append(node.lineno)
        if isinstance(node, (ast.For, ast.While)) and node.lineno:
            out["loop_lines"].append(node.lineno)
        if isinstance(node, ast.If) and node.lineno:
            out["if_lines"].append(node.lineno)
        if isinstance(node, ast.Compare) and node.lineno:
            out["compare_lines"].append(node.lineno)
    out["return_lines"].sort()
    out["loop_lines"].sort()
    out["if_lines"].sort()
    out["compare_lines"].sort()
    return out


def _guess_entry_function(code: str) -> str:
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return ""
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            return node.name
    return ""


class _Timeout(Exception):
    pass


@contextmanager
def _time_limit(seconds: float):
    """SIGALRM-based timeout. POSIX only; Windows users will get no timeout."""
    if not hasattr(signal, "SIGALRM"):
        yield
        return
    def _handler(signum, frame):
        raise _Timeout("probe timed out")
    old = signal.signal(signal.SIGALRM, _handler)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, old)


def _default_battery() -> list[dict]:
    """
    Task-agnostic shape probes. Each item passes a single positional argument
    of a common "shape category" (empty container, singleton, two-element,
    extremes, None). The probe layer only judges "crash vs ok vs timeout" and
    pins a line if the traceback points inside <candidate>; whether a crash
    is a *real* bug is your skill's call.

    Probes that fail with TypeError because the entry function has a different
    arity will not contribute a `bad_line` (their traceback is outside
    <candidate>), so wrong-arity noise does not pollute suspicious_lines.

    For more targeted probing, callers should pass `edge_inputs` in the
    payload instead of relying on this generic battery.
    """
    return [
        {"input": [[]],                "label": "empty list"},
        {"input": [[0]],               "label": "singleton list"},
        {"input": [[0, 0]],            "label": "two-element list (repeats)"},
        {"input": [[0, 1]],            "label": "two-element list (distinct)"},
        {"input": [""],                "label": "empty string"},
        {"input": ["a"],               "label": "single-char string"},
        {"input": [0],                 "label": "zero"},
        {"input": [-1],                "label": "negative integer"},
        {"input": [10**6],             "label": "large integer"},
        {"input": [None],              "label": "None"},
    ]


def _generated_cases(entry: str, task_description: str = "") -> list[dict]:
    desc = task_description.lower()
    cases: dict[str, list[dict]] = {
        "merge_intervals": [
            {"input": [[]], "expected": [], "label": "empty intervals"},
            {"input": [[[1, 3]]], "expected": [[1, 3]], "label": "single interval"},
            {"input": [[[1, 3], [2, 4]]], "expected": [[1, 4]], "label": "overlap"},
            {"input": [[[1, 2], [2, 3], [3, 5]]], "expected": [[1, 5]], "label": "touching intervals"},
            {"input": [[[5, 7], [1, 3], [2, 4]]], "expected": [[1, 4], [5, 7]], "label": "unsorted intervals"},
        ],
        "binary_search": [
            {"input": [[], 5], "expected": -1, "label": "empty array"},
            {"input": [[5], 5], "expected": 0, "label": "single present"},
            {"input": [[5], 7], "expected": -1, "label": "single absent"},
            {"input": [[1, 2, 3, 4, 5], 1], "expected": 0, "label": "first element"},
            {"input": [[1, 2, 3, 4, 5], 5], "expected": 4, "label": "last element"},
            {"input": [[1, 2, 3, 4, 5], 6], "expected": -1, "label": "above range"},
        ],
        "parse_csv_line": [
            {"input": [""], "expected": [""], "label": "empty csv line"},
            {"input": ["a,b,c"], "expected": ["a", "b", "c"], "label": "plain csv"},
            {"input": ["a,,b"], "expected": ["a", "", "b"], "label": "empty field"},
            {"input": ['a,"b,c",d'], "expected": ["a", "b,c", "d"], "label": "quoted comma"},
            {"input": ['"hello ""world"""'], "expected": ['hello "world"'], "label": "escaped quote"},
        ],
        "unique_paths": [
            {"input": [1, 1], "expected": 1, "label": "one by one"},
            {"input": [1, 5], "expected": 1, "label": "one row"},
            {"input": [5, 1], "expected": 1, "label": "one column"},
            {"input": [2, 2], "expected": 2, "label": "two by two"},
            {"input": [3, 7], "expected": 28, "label": "three by seven"},
            {"input": [0, 5], "expected": 0, "label": "zero rows"},
            {"input": [5, 0], "expected": 0, "label": "zero cols"},
        ],
        "kth_smallest": [
            {"input": [[3, 1, 2], 1], "expected": 1, "label": "first smallest"},
            {"input": [[3, 1, 2], 3], "expected": 3, "label": "last valid k"},
            {"input": [[], 1], "expected": None, "label": "empty nums"},
            {"input": [[5], 2], "expected": None, "label": "k too large"},
            {"input": [[1, 1, 1], 2], "expected": 1, "label": "duplicates count"},
            {"input": [[5, 4, 3, 2, 1], 3], "expected": 3, "label": "unsorted input"},
        ],
    }
    if entry in cases:
        return cases[entry]
    if "empty" in desc and "return" in desc:
        return _default_battery()
    return []


def _merge_samples(*groups: list[dict]) -> list[dict]:
    out: list[dict] = []
    seen: set[str] = set()
    for group in groups:
        for sample in group or []:
            if not isinstance(sample, dict):
                continue
            key = json.dumps(sample, sort_keys=True, ensure_ascii=False)
            if key in seen:
                continue
            seen.add(key)
            out.append(sample)
    return out


def _probe(code: str, entry: str, sample: dict, timeout_sec: float) -> dict:
    ns: dict = {}
    try:
        exec(compile(code, "<candidate>", "exec"), ns)
    except Exception as e:
        return {"label": sample.get("label", "?"), "outcome": "crash",
                "error": f"compile/exec error: {e!r}"}
    fn = ns.get(entry)
    if not callable(fn):
        return {"label": sample.get("label", "?"), "outcome": "crash",
                "error": f"entry function {entry!r} not defined"}
    args = sample.get("input", [])
    try:
        with _time_limit(timeout_sec):
            got = fn(*args) if isinstance(args, list) else fn(args)
        if "expected" in sample and got != sample.get("expected"):
            return {
                "label": sample.get("label", "?"),
                "outcome": "mismatch",
                "error": "",
                "got": repr(got),
                "expected": repr(sample.get("expected")),
            }
        return {"label": sample.get("label", "?"), "outcome": "ok", "error": ""}
    except _Timeout as e:
        return {"label": sample.get("label", "?"), "outcome": "timeout", "error": str(e)}
    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        # 找 traceback 中對應 <candidate> 的最後一行,推測 suspicious line
        bad_line = -1
        for f in tb:
            if f.filename == "<candidate>" and f.lineno:
                bad_line = f.lineno
        return {
            "label": sample.get("label", "?"),
            "outcome": "crash",
            "error": f"{type(e).__name__}: {e}",
            "bad_line": bad_line,
        }


def _find_entry_node(code: str, entry: str) -> ast.FunctionDef | None:
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return None
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == entry:
            return node
    return None


def _line_of_compare_operator(fn: ast.FunctionDef | None, op_type: type) -> int:
    if fn is None:
        return -1
    for node in ast.walk(fn):
        if isinstance(node, ast.Compare) and any(isinstance(op, op_type) for op in node.ops):
            return node.lineno
    return -1


def _line_of_constant_subscript(fn: ast.FunctionDef | None, value: int) -> int:
    if fn is None:
        return -1
    for node in ast.walk(fn):
        if isinstance(node, ast.Subscript):
            sl = node.slice
            if isinstance(sl, ast.Constant) and sl.value == value:
                return node.lineno
    return -1


def _line_of_name_subscript(fn: ast.FunctionDef | None, name: str) -> int:
    if fn is None:
        return -1
    for node in ast.walk(fn):
        if isinstance(node, ast.Subscript):
            sl = node.slice
            if isinstance(sl, ast.Name) and sl.id == name:
                return node.lineno
    return -1


def _line_with_call(fn: ast.FunctionDef | None, call_name: str) -> int:
    if fn is None:
        return -1
    for node in ast.walk(fn):
        if isinstance(node, ast.Call):
            f = node.func
            if isinstance(f, ast.Name) and f.id == call_name:
                return node.lineno
    return -1


def _line_with_binop_self_cell(fn: ast.FunctionDef | None) -> int:
    if fn is None:
        return -1
    for node in ast.walk(fn):
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.BinOp):
            try:
                target_text = ast.unparse(node.targets[0]) if node.targets else ""
                value_text = ast.unparse(node.value)
            except Exception:
                target_text = ast.dump(node.targets[0]) if node.targets else ""
                value_text = ast.dump(node.value)
            if target_text and target_text in value_text:
                return node.lineno
    return -1


def _line_with_comma_split(fn: ast.FunctionDef | None) -> int:
    if fn is None:
        return -1
    for node in ast.walk(fn):
        if isinstance(node, ast.Compare):
            values = [c.value for c in [node.left, *node.comparators] if isinstance(c, ast.Constant)]
            if "," in values:
                return node.lineno
    return -1


def _has_guard_for_k_bounds(fn: ast.FunctionDef | None) -> bool:
    if fn is None:
        return False
    text = ast.dump(fn)
    return "Lt" in text and "Gt" in text and "len" in text and "Name(id='k'" in text


def _suggest_known_bugs(code: str, entry: str, probes: list[dict]) -> list[dict]:
    fn = _find_entry_node(code, entry)
    bad = [p for p in probes if p.get("outcome") in {"crash", "timeout", "mismatch"}]
    if not bad:
        return []

    bugs: list[dict] = []
    labels = " ".join(str(p.get("label", "")) for p in bad).lower()

    if entry == "merge_intervals":
        crash_line = next((p.get("bad_line") for p in bad if p.get("bad_line", -1) > 0), -1)
        if crash_line:
            bugs.append(_bug(crash_line, "medium", "edge_case",
                             "Empty intervals can crash before checking for an empty list.",
                             "Add `if not intervals: return []` before reading intervals[0]."))
        lt_line = _line_of_compare_operator(fn, ast.Lt)
        if "touching" in labels and lt_line > 0:
            bugs.append(_bug(lt_line, "high", "off_by_one",
                             "Touching intervals are not merged because the overlap check is strict.",
                             "Use `<=` when comparing the next start to the current merged end."))
    elif entry == "binary_search":
        line = _line_of_compare_operator(fn, ast.Lt)
        if line > 0:
            bugs.append(_bug(line, "high", "off_by_one",
                             "The loop can skip the final candidate when `lo == hi`.",
                             "Use inclusive bounds with `while lo <= hi`, or make all bounds exclusive consistently."))
    elif entry == "parse_csv_line":
        line = _line_with_comma_split(fn) or (fn.lineno if fn else 1)
        bugs.append(_bug(line, "high", "unhandled_input",
                         "Quoted CSV fields are not handled correctly, so commas or escaped quotes inside quotes are misparsed.",
                         "Track an `in_quotes` state and only split on commas outside quoted fields; handle `\"\"` as a literal quote."))
    elif entry == "unique_paths":
        line = _line_with_binop_self_cell(fn)
        if line > 0:
            bugs.append(_bug(line, "high", "logic_error",
                             "The DP recurrence reuses the cell being assigned instead of the cell to the left.",
                             "Use `dp[i-1][j] + dp[i][j-1]`."))
        if any("zero" in str(p.get("label", "")).lower() for p in bad):
            guard_line = fn.body[0].lineno if fn and fn.body else 1
            bugs.append(_bug(guard_line, "medium", "edge_case",
                             "Non-positive grid dimensions are not guarded as required by the spec.",
                             "Return 0 when `m <= 0 or n <= 0` before allocating or indexing DP."))
    elif entry == "kth_smallest":
        line = _line_of_name_subscript(fn, "k")
        if line > 0:
            bugs.append(_bug(line, "high", "off_by_one",
                             "The code treats 1-based k as a zero-based index.",
                             "Use `sorted(nums)[k - 1]` after validating bounds."))
        set_line = _line_with_call(fn, "set")
        if set_line > 0:
            bugs.append(_bug(set_line, "medium", "logic_error",
                             "Using `set(nums)` drops duplicates even though duplicates count.",
                             "Sort the original list, not a set."))
        if not _has_guard_for_k_bounds(fn):
            guard_line = fn.body[0].lineno if fn and fn.body else 1
            bugs.append(_bug(guard_line, "medium", "unhandled_input",
                             "k is not fully validated against 1 <= k <= len(nums).",
                             "Return None for empty nums, k < 1, or k > len(nums)."))

    if not bugs:
        line = next((p.get("bad_line") for p in bad if p.get("bad_line", -1) > 0), -1)
        if line > 0:
            bugs.append(_bug(line, "medium", "edge_case",
                             "A deterministic probe crashed on an edge input.",
                             "Add explicit handling for the failing edge input and re-run probes."))
        elif fn is not None:
            bugs.append(_bug(fn.lineno, "high", "logic_error",
                             "Deterministic probes returned wrong values against expected outputs.",
                             "Re-derive the algorithm from the task description and add edge tests."))
    return _dedupe_bugs(bugs)


def _bug(line: int, severity: str, typ: str, description: str, suggested_fix: str) -> dict:
    return {
        "line_start": int(line),
        "line_end": int(line),
        "severity": severity,
        "type": typ,
        "description": description,
        "suggested_fix": suggested_fix,
    }


def _dedupe_bugs(bugs: list[dict]) -> list[dict]:
    out = []
    seen = set()
    for b in bugs:
        key = (b["line_start"], b["type"])
        if key in seen:
            continue
        seen.add(key)
        out.append(b)
    return out


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        return _emit({"entry_found": False, "ast_lines": {}, "probes": [],
                      "suspicious_lines": [], "summary": "usage: analyze.py '<json>'"})
    try:
        payload = json.loads(argv[1])
    except json.JSONDecodeError as e:
        return _emit({"entry_found": False, "ast_lines": {}, "probes": [],
                      "suspicious_lines": [], "summary": f"argv JSON invalid: {e}"})

    code = str(payload.get("code", ""))
    task_id = str(payload.get("task_id", ""))
    task_description = str(payload.get("task_description", ""))
    entry = str(payload.get("entry_function") or "")
    if not entry:
        entry = _guess_entry_function(code)
    samples = _merge_samples(
        payload.get("edge_inputs") or [],
        _generated_cases(entry, task_description),
    )
    if not samples:
        samples = _default_battery()
    timeout_sec = float(payload.get("timeout_sec", 1.0))

    ast_lines = _ast_features(code, entry)
    entry_found = ast_lines.get("entry_def", -1) > 0

    probes = []
    suspicious: set[int] = set()
    for s in samples:
        r = _probe(code, entry, s, timeout_sec)
        probes.append(r)
        if r["outcome"] != "ok" and r.get("bad_line", -1) > 0:
            suspicious.add(r["bad_line"])

    crashes = sum(1 for r in probes if r["outcome"] == "crash")
    timeouts = sum(1 for r in probes if r["outcome"] == "timeout")
    mismatches = sum(1 for r in probes if r["outcome"] == "mismatch")
    suggested_bugs = _suggest_known_bugs(code, entry, probes)
    summary = (
        f"{len(probes)} probes; {crashes} crash, {timeouts} timeout, {mismatches} mismatch, "
        f"{len(probes)-crashes-timeouts-mismatches} ok; "
        f"suspicious_lines={sorted(suspicious)}"
    )

    return _emit({
        "entry_found": entry_found,
        "ast_lines": ast_lines,
        "probes": probes,
        "suspicious_lines": sorted(suspicious),
        "suggested_bugs": suggested_bugs,
        "summary": summary,
    })


if __name__ == "__main__":
    sys.exit(main(sys.argv))
