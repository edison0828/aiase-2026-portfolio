# Portfolio packaging: original tests adapted to newly authored public fixtures.
"""Tests for the student bug-hunter deterministic analyzer."""

import json
import re
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
ANALYZE = REPO_ROOT / "skills" / "bug-hunter-edison0828" / "scripts" / "analyze.py"
TASK_DIR = REPO_ROOT / "examples" / "portfolio_cases"


def _invoke(payload: dict) -> dict:
    proc = subprocess.run(
        [sys.executable, str(ANALYZE), json.dumps(payload, ensure_ascii=False)],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    matches = re.findall(r"```json\s*\n(.*?)\n```", proc.stdout, re.DOTALL | re.IGNORECASE)
    assert matches, proc.stdout
    return json.loads(matches[-1])


def _task(task_id: str) -> dict:
    return json.loads((TASK_DIR / f"{task_id}.json").read_text(encoding="utf-8"))


def test_analyzer_has_no_suggested_bugs_for_clean_references():
    for path in sorted(TASK_DIR.glob("portfolio_*.json")):
        task = _task(path.stem)
        out = _invoke({
            "task_id": task["task_id"],
            "task_description": task["task_description"],
            "code": task["clean_code"],
        })
        assert out["suggested_bugs"] == [], f"false positive on {task['task_id']}: {out}"


def test_analyzer_suggested_bugs_overlap_buggy_ground_truth():
    for path in sorted(TASK_DIR.glob("portfolio_*.json")):
        task = _task(path.stem)
        out = _invoke({
            "task_id": task["task_id"],
            "task_description": task["task_description"],
            "code": task["buggy_code"],
        })
        suggested = {(b["line_start"], b["type"]) for b in out["suggested_bugs"]}
        expected = {(b["line_start"], b["type"]) for b in task["bugs_in_buggy"]}
        assert suggested & expected, f"no overlap for {task['task_id']}: {out}"


def test_analyzer_reports_mismatch_outcomes():
    task = _task("portfolio_binary_search")
    out = _invoke({
        "task_id": task["task_id"],
        "task_description": task["task_description"],
        "code": task["buggy_code"],
    })
    outcomes = {p["outcome"] for p in out["probes"]}
    assert "mismatch" in outcomes
    assert any(b["type"] == "off_by_one" for b in out["suggested_bugs"])
