# Portfolio packaging: original tests adapted to newly authored public fixtures.
"""Tests for the Open Track minimal reproducer skill."""

import json
import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
RUNNER = REPO_ROOT / "skills" / "open-reproducer-edison0828" / "scripts" / "run.py"
TASK_DIR = REPO_ROOT / "examples" / "portfolio_cases"


def _invoke(payload: dict, tmp_path: Path) -> dict:
    result_path = tmp_path / "aiase_result.json"
    env = os.environ.copy()
    env["AIASE_RESULT_PATH"] = str(result_path)
    proc = subprocess.run(
        [sys.executable, str(RUNNER), json.dumps(payload, ensure_ascii=False)],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
        env=env,
    )
    assert proc.returncode == 0, proc.stderr
    assert result_path.exists(), proc.stdout
    return json.loads(result_path.read_text(encoding="utf-8"))


def _task(task_id: str) -> dict:
    return json.loads((TASK_DIR / f"{task_id}.json").read_text(encoding="utf-8"))


def test_finds_reproducer_for_kth_smallest_off_by_one(tmp_path):
    task = _task("portfolio_kth_smallest")
    out = _invoke({
        "task_id": "open_repro_kth",
        "entry_function": "kth_smallest",
        "task_description": task["task_description"],
        "code": task["buggy_code"],
    }, tmp_path)
    assert out["task_id"] == "open_repro_kth"
    assert out["entry_function"] == "kth_smallest"
    assert out["bug_triggered"] is True
    assert out["reproducer"]["kind"] in {"mismatch", "exception"}
    assert out["reproducer"]["expected"] != out["reproducer"]["actual"] or out["reproducer"]["error"]


def test_clean_reference_has_no_reproducer(tmp_path):
    task = _task("portfolio_binary_search")
    out = _invoke({
        "task_id": "open_repro_clean",
        "entry_function": "binary_search",
        "task_description": task["task_description"],
        "code": task["clean_code"],
    }, tmp_path)
    assert out["bug_triggered"] is False
    assert out["reproducer"] is None
    assert out["tried"] > 0


def test_candidate_inputs_are_used_for_unknown_function(tmp_path):
    code = "def double(x):\n    return x + x + 1\n"
    out = _invoke({
        "task_id": "open_repro_custom",
        "entry_function": "double",
        "code": code,
        "candidate_inputs": [
            {"input": [2], "expected": 4, "label": "simple double"}
        ],
    }, tmp_path)
    assert out["bug_triggered"] is True
    assert out["reproducer"]["input"] == [2]
    assert out["reproducer"]["expected"] == 4
    assert out["reproducer"]["actual"] == 5
