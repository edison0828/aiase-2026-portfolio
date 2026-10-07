#!/usr/bin/env python3
"""Offline portfolio demonstration, added during packaging on 2026-10-07.

Runs only the small trusted examples shipped here. No model/provider is called.
This is not a runner for untrusted user code.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"
CASES = ROOT / "examples" / "portfolio_cases"


def invoke(skill: str, script: str, payload: dict) -> dict:
    with tempfile.TemporaryDirectory(prefix="portfolio-demo-") as temp:
        result = Path(temp) / "result.json"
        env = dict(os.environ, AIASE_RESULT_PATH=str(result))
        process = subprocess.run(
            [sys.executable, str(SKILLS / skill / "scripts" / script), json.dumps(payload)],
            env=env, capture_output=True, text=True, timeout=20, check=False,
        )
        if result.exists():
            return json.loads(result.read_text(encoding="utf-8"))
        matches = re.findall(r"```json\s*\n(.*?)\n```", process.stdout, re.DOTALL)
        if not matches:
            raise RuntimeError(f"No JSON returned by {skill}/{script}: {process.stderr}")
        return json.loads(matches[-1])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="Optionally save the demonstration JSON.")
    args = parser.parse_args()
    case = json.loads((CASES / "portfolio_binary_search.json").read_text(encoding="utf-8"))
    results = {}
    sql_payload = {"schema_ddl": "CREATE TABLE books(id INTEGER, title TEXT);"}
    valid = invoke("text2sql-edison0828", "validate_sql.py", dict(sql_payload, sql="SELECT title FROM books"))
    invalid = invoke("text2sql-edison0828", "validate_sql.py", dict(sql_payload, sql="SELECT missing FROM books"))
    results["sql_schema_validation"] = {"valid_query": valid, "unknown_column": invalid}
    checks = {"valid_sql_accepted": valid["ok"] is True, "unknown_column_rejected": invalid["ok"] is False}

    for variant in ("clean", "buggy"):
        payload = {
            "task_id": case["task_id"], "code": case[f"{variant}_code"],
            "task_description": case["task_description"],
            "constraints": case["constraints"], "entry_function": "binary_search",
        }
        author = invoke("code-author-edison0828", "selftest.py", payload)
        hunter = invoke("bug-hunter-edison0828", "run.py", payload)
        reproducer = invoke("open-reproducer-edison0828", "run.py", payload)
        results[variant] = {"selftest": author, "bug_report": hunter, "reproducer": reproducer}
        if variant == "clean":
            checks["clean_samples_pass"] = author["passed"] > 0 and author["failed"] == 0
            checks["clean_has_no_bug_report"] = hunter["verdict"] == "clean" and hunter["bugs"] == []
            checks["clean_has_no_reproducer"] = reproducer["bug_triggered"] is False
        else:
            checks["buggy_sample_fails"] = author["failed"] > 0
            checks["buggy_has_bug_report"] = hunter["verdict"] == "buggy" and bool(hunter["bugs"])
            checks["buggy_has_reproducer"] = reproducer["bug_triggered"] is True

    report = {
        "scope": "Offline helpers with newly authored portfolio fixtures; no LLM or course hidden tests.",
        "checks": checks, "passed": sum(checks.values()), "total": len(checks),
        "results": results,
    }
    text = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
