---
name: code-author-edison0828
description: Implement a Python function from a natural-language task description, self-test, and emit the AIASE 2026 Pairwise Code Author contract.
version: 0.1.0
metadata:
  hermes:
    tags: [code, python, aiase-2026]
    category: code
---

# Code Author Skill (Pairwise Track)

## When to Use

When the user sends a JSON payload with `task_description`, `constraints` (entry_function, max_loc, imports_forbidden), and `task_id`. The skill must produce a Python implementation that:

- defines exactly the entry function named in `constraints.entry_function`,
- does not exceed `constraints.max_loc` source lines (measured by `radon raw`),
- does not import anything in `constraints.imports_forbidden`,
- handles realistic edge cases (empty input, single element, extremes — see Pitfalls).

Trigger example:

```
/code-author-edison0828 {"task_id":"task_042",
  "task_description":"Implement merge_intervals(intervals): merge overlapping intervals, empty input returns [].",
  "constraints":{"entry_function":"merge_intervals","max_loc":500,"imports_forbidden":["os","sys"]}}
```

## Procedure

1. **Parse the payload exactly.** Extract `task_id`, `task_description`, and `constraints.entry_function`, `constraints.max_loc`, `constraints.imports_forbidden`.
2. **Write down the function contract before coding.**
   - Inputs, output type, invalid-input behavior, and boundary cases explicitly mentioned in `task_description`.
   - Complexity requirement such as `O(log n)` for binary search.
   - Whether duplicates count, touching intervals merge, empty strings/lists are valid, or zero dimensions are valid.
3. **Draft one self-contained Python function.**
   - Define the top-level function named exactly `constraints.entry_function`.
   - Do not print, read files, call network APIs, use randomness, or import forbidden modules.
   - Prefer simple deterministic code over clever one-liners.
4. **Create sample tests for the exact task.** Always include empty input, single-element input, boundary endpoints, duplicate/tie cases, and the examples implied by the task. Use the format:

   ```json
   {"input": [[1, 2, 3], 2], "expected": 1}
   ```

   The harness also adds deterministic edge cases for known project task shapes, but you should still provide your own samples.
5. **Run the deterministic selftest harness.** Pass candidate code, constraints, task description, and sample inputs:

   ```bash
   python scripts/selftest.py '{"code":"<candidate code>","constraints":{...},"task_description":"<task_description>","sample_inputs":[...]}'
   ```

   The script checks syntax, top-level entry function, forbidden imports, SLOC, and sample behavior. It returns `{passed, failed, errors, sloc, loc_violation, import_violations, sample_count}`.
6. **Retry up to three times when selftest fails.**
   - `entry function ... not defined`: rename the function exactly.
   - `mismatch`: re-check indexing, boundary behavior, duplicate handling, and sorting.
   - `runtime error`: add missing empty-input or invalid-input guard.
   - `forbidden imports`: remove the import and use built-ins.
   - `loc_violation`: simplify the implementation.
7. **Write the final contract by running `scripts/run.py`; this step is mandatory.** Use the terminal tool from the skill directory. Do not put raw JSON inside shell quotes, because Python code often contains single quotes and newlines. Use this Python `json.dumps` pattern:

   ```bash
python3 - <<'PY'
import json, subprocess
payload = {
    "task_id": "<same task_id>",
    "code": """<final code>""",
    "loc": <sloc>,
    "self_test_results": <selftest object>,
    "rationale": "<short reason>",
    "confidence": 0.8,
}
subprocess.run(["python3", "scripts/run.py", json.dumps(payload)], check=True)
PY
   ```

   Do not handwrite the JSON result file yourself, do not create `result.json`, do not create files under `references/`, and do not stop after selftest. The script writes the result JSON to `AIASE_RESULT_PATH`; `./aiase_result.json` is only a fallback for direct local script execution when the variable is absent.

## Implementation Patterns

Use the simplest correct implementation for common task families:

- `merge_intervals(intervals)`: return `[]` for empty input, sort by start, merge when `cur[0] <= last[1]` so touching intervals merge. Preserve the original interval value shape expected by the task: if examples use lists, return lists such as `[[1, 4]]`, not tuples.
- `binary_search(arr, target)`: use inclusive bounds `lo = 0`, `hi = len(arr) - 1`, loop while `lo <= hi`, return `-1` if absent.
- `parse_csv_line(line)`: manually track `in_quotes`; inside quotes, `""` means a literal `"`. Do not import `csv` when forbidden.
- `unique_paths(m, n)`: return `0` for non-positive dimensions; use a 1-D DP row or standard combinational DP; `1 x 1` returns `1`.
- `kth_smallest(nums, k)`: validate `nums` and `1 <= k <= len(nums)`; duplicates count, so use `sorted(nums)[k - 1]`, not `set`.

## Pitfalls

- **Missing empty-input handling** — the most common Pairwise failure. Always test `[]` / `""` / `0`.
- **merge_intervals shape** — for empty input return `[]`; for touching intervals `[[1,2],[2,3]]` return `[[1,3]]`; for unsorted intervals sort first; return list-of-lists when inputs/examples are lists.
- **Off-by-one** in loops / slicing — test both endpoints (first, last) explicitly.
- **Mutating caller inputs unintentionally** — use `sorted(intervals)` rather than `intervals.sort()` unless mutation is explicitly allowed.
- **Dropping duplicates** — do not use `set()` when the spec says duplicates count.
- **Clean-code false confidence** — passing one happy-path test is not enough; include adversarial edge cases.
- **Forbidden imports** — `os`, `sys`, `subprocess` etc. The harness will flag them; don't import anything not strictly needed.
- **LoC limit** — `radon raw` counts source lines (excludes blank + pure-comment). The grader re-runs `radon` independently of your reported `loc`. Keep code lean.
- **No network / no filesystem outside cwd** in sandbox (see spec §2.3). Don't read files, don't call APIs.

## Verification

The result file written by `scripts/run.py` is a JSON object with:

- `task_id` (must equal input)
- `code` (string, valid Python defining `entry_function`)
- `loc` (integer — what your harness measured)
- `self_test_results` (object with `passed` and `failed` counts at minimum)
- `rationale` (string)
- `confidence` (number in `[0.0, 1.0]`)

The grader reads the file path from `AIASE_RESULT_PATH`; it does not grade JSON printed in the conversation. If `AIASE_RESULT_PATH` exists, that path is authoritative and must receive the final JSON object.
