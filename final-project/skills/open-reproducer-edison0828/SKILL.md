---
name: open-reproducer-edison0828
description: Generate a minimal executable reproducer for a Python bug by running deterministic edge probes. AIASE 2026 Open Track.
version: 0.1.0
metadata:
  hermes:
    tags: [python, testing, debugging, repro, aiase-2026]
    category: code
---

# Buggy Code Minimal Reproducer Generator

## When to Use

Use this skill when the user provides Python source code plus a task description or bug hint, and wants the smallest concrete input that demonstrates the code is wrong.

Trigger example:

```
/open-reproducer-edison0828 {"task_id":"open_repro_001","entry_function":"kth_smallest","code":"def kth_smallest(nums, k): ...","task_description":"Return the k-th smallest element using 1-based k.","bug_hint":"k may be treated as zero-based"}
```

## Procedure

1. Parse `task_id`, `code`, `task_description`, optional `entry_function`, optional `bug_hint`, and optional `candidate_inputs`.
2. Run the deterministic harness:

   ```bash
   python scripts/run.py '{"task_id":"<task_id>","code":"<code>","task_description":"<task_description>","entry_function":"<entry_function>","bug_hint":"<bug_hint>","candidate_inputs":[...]}'
   ```

3. The harness infers the entry function when possible, generates known edge probes for common Pairwise-style tasks, executes the code in a restricted namespace, and returns the smallest probe where `actual != expected` or the function raises unexpectedly.
4. The harness writes the result JSON to `AIASE_RESULT_PATH`, falling back to `./aiase_result.json` when unset. Do not emit another JSON object in the conversation.

## Verification

The result file is a JSON object with:

- `task_id`: copied from input
- `entry_function`: function that was executed
- `bug_triggered`: boolean
- `reproducer`: object with `input`, `expected`, `actual`, `error`, `kind`, and `label`; `null` if no failure is found
- `tried`: number of probes executed
- `strategy`: short string describing the deterministic search strategy
- `confidence`: number in `[0.0, 1.0]`

The result is verifiable because the grader can execute the submitted `code` on `reproducer.input` and independently check that the observed output or exception differs from `expected`.
