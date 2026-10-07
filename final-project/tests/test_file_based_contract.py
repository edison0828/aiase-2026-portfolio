# Portfolio packaging: classroom hello-aiase smoke test omitted.
"""Tests for the updated file-based AIASE result contract."""

import json
import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def _invoke(script: Path, payload: dict, tmp_path: Path) -> dict:
    result_path = tmp_path / f"{script.parents[1].name}.json"
    env = os.environ.copy()
    env["AIASE_RESULT_PATH"] = str(result_path)
    proc = subprocess.run(
        [sys.executable, str(script), json.dumps(payload, ensure_ascii=False)],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
        env=env,
    )
    assert proc.returncode == 0, proc.stderr
    assert result_path.exists(), proc.stdout
    return json.loads(result_path.read_text(encoding="utf-8"))


def test_text2sql_writes_result_file_and_strips_sql_fence(tmp_path):
    out = _invoke(
        REPO_ROOT / "skills" / "text2sql-edison0828" / "scripts" / "run.py",
        {
            "task_id": "t",
            "sql": "```sql\nSELECT 1\n```",
            "rationale": "unit test",
            "confidence": 2,
        },
        tmp_path,
    )
    assert out["task_id"] == "t"
    assert out["sql"] == "SELECT 1"
    assert out["confidence"] == 1.0


def test_code_author_writes_result_file_and_strips_python_fence(tmp_path):
    out = _invoke(
        REPO_ROOT / "skills" / "code-author-edison0828" / "scripts" / "run.py",
        {
            "task_id": "t",
            "code": "```python\ndef f():\n    return 1\n```",
            "loc": "2",
            "self_test_results": {"passed": 1, "failed": 0},
            "rationale": "unit test",
            "confidence": 0.5,
        },
        tmp_path,
    )
    assert out["code"] == "def f():\n    return 1"
    assert out["loc"] == 2


def test_bug_hunter_writes_result_file_and_cleans_clean_verdict(tmp_path):
    out = _invoke(
        REPO_ROOT / "skills" / "bug-hunter-edison0828" / "scripts" / "run.py",
        {
            "task_id": "t",
            "verdict": "clean",
            "bugs": [
                {
                    "line_start": 1,
                    "line_end": 1,
                    "severity": "high",
                    "type": "logic_error",
                    "description": "x",
                    "suggested_fix": "y",
                }
            ],
            "confidence": 0.7,
        },
        tmp_path,
    )
    assert out["verdict"] == "clean"
    assert out["bugs"] == []
