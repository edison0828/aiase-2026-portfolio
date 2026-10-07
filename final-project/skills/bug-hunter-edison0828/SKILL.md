---
name: bug-hunter-edison0828
description: Audit a Python function for bugs against its task description, emit a structured bug report per the AIASE 2026 Pairwise Bug Hunter contract.
version: 0.1.0
metadata:
  hermes:
    tags: [code, audit, aiase-2026]
    category: code
---

# Bug Hunter Skill (Pairwise Track)

## When to Use

When the user sends a JSON payload with `code` (Python source), `task_description`, and `task_id`. The skill must produce a structured bug report whose `bugs[]` matches actual bugs (Jaccard-ish line+type overlap), with low false-positive rate on clean code.

Trigger example:

```
/bug-hunter-edison0828 {"task_id":"task_042",
  "code":"def merge_intervals(intervals): ...",
  "task_description":"Merge overlapping intervals, empty input returns []."}
```

## Procedure

1. **Parse the payload.** Extract `task_id`, `code`, `task_description`, and, when present, `entry_function`. Read `code` line-by-line using 1-indexed line numbers.
2. **Probe the code deterministically.** Run:

   ```bash
   python scripts/analyze.py '{"task_id":"<task_id>","code":"<code>","task_description":"<task_description>","entry_function":"<optional entry>"}'
   ```

   The analyzer parses AST structure, runs expected-output edge probes for known task shapes, detects crash/mismatch outcomes, and returns `suggested_bugs` when there is concrete evidence.
3. **Use evidence first.**
   - If `suggested_bugs` is non-empty, use those bug objects as the primary report. Prefer copying them directly into `bugs` instead of inventing new line numbers or types.
   - If probes show `mismatch` but no `suggested_bugs`, report one `logic_error` on the entry function line.
   - If probes show `crash` with `bad_line`, report an `edge_case` or `unhandled_input` bug at that `bad_line`.
   - If all probes are OK and `suggested_bugs` is empty, return `verdict: "clean"` and `bugs: []`.
4. **Calibrate type and severity.**
   - `off_by_one`: loop bounds, `k` indexing, strict `<` vs `<=`.
   - `logic_error`: wrong recurrence, wrong algorithm, duplicate-dropping when duplicates count.
   - `edge_case`: empty input, zero dimensions, single-element cases.
   - `unhandled_input`: missing validation for invalid `k`, quoted CSV not supported, required input shape not handled.
   - `high`: common valid input returns wrong output. `medium`: boundary or invalid input only. `low`: minor maintainability risk.
5. **Avoid false positives.** Do not report style, performance, mutation, or alternate valid implementation choices unless a probe or task requirement shows an actual failure.
6. **Write the contract by running `scripts/run.py`; this step is mandatory.** Prefer passing the original code and task description so `run.py` can re-use the deterministic analyzer and preserve exact line numbers. Use the terminal tool from the skill directory. Do not put raw JSON inside shell quotes, because code and task descriptions often contain `'` or `""`. Use this Python `json.dumps` pattern:

   ```bash
python3 - <<'PY'
import json, subprocess
payload = {
    "task_id": "<same task_id>",
    "code": """<original code>""",
    "task_description": """<task_description>""",
    "entry_function": "<optional entry>",
    "confidence": 0.8,
}
subprocess.run(["python3", "scripts/run.py", json.dumps(payload)], check=True)
PY
   ```

   Do not handwrite the final bug JSON yourself, do not create `result.json`, do not create files under `references/`, and do not stop after analyzer evidence. The script writes the result JSON to `AIASE_RESULT_PATH`; `./aiase_result.json` is only a fallback for direct local script execution when the variable is absent. If you include manual `bugs`, their `line_start`, `line_end`, and `type` must exactly match `suggested_bugs` from `scripts/analyze.py`.

## Known Task Cues

- `merge_intervals`: empty input must return `[]`; touching intervals merge, so strict `<` is suspicious when touching probes fail.
- `binary_search`: a sorted array may be empty; inclusive `lo <= hi` is the safest pattern for this spec.
- `parse_csv_line`: quoted commas and escaped quotes `""` must work; a plain comma split is buggy.
- `unique_paths`: `m <= 0` or `n <= 0` returns `0`; recurrence should use top plus left neighbor.
- `kth_smallest`: `k` is 1-based and duplicates count; `sorted(nums)[k]` and `set(nums)` are suspicious when probes fail.

## Pitfalls

- **Over-reporting** (always reporting many bugs) destroys score — clean code FP rate is 25% of your grade.
- **Under-reporting** (always `verdict=clean`) also destroys score — F1 on buggy code is 50%.
- **Reporting without evidence** — if analyzer probes all pass and there is no clear spec violation, prefer `clean`.
- **Wrong severity calibration**: empty-input crash = `medium` (edge), wrong-answer-on-common-input = `high`/`critical`. See spec §2.3.
- **Wrong line numbers**: 1-indexed, point at the smallest line range that contains the bug. Don't point at the function signature line for an off-by-one in the loop.

## Verification

The result file written by `scripts/run.py` is a JSON object with:

- `task_id` (must equal input)
- `verdict` (`"buggy"` or `"clean"`)
- `bugs` (array of bug objects with `line_start`, `line_end`, `severity`, `type`, `description`, `suggested_fix`; **must be `[]` when verdict=clean**)
- `confidence` (number in `[0.0, 1.0]`)

The grader reads the file path from `AIASE_RESULT_PATH`; it does not grade JSON printed in the conversation. If `AIASE_RESULT_PATH` exists, that path is authoritative and must receive the final JSON object.
