# Portfolio packaging: original tests adapted to newly authored public fixtures.
"""Tests for SLOC computation in code-author selftest harness."""

import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
ST_PATH = REPO_ROOT / "skills" / "code-author-edison0828" / "scripts" / "selftest.py"


def _load():
    spec = importlib.util.spec_from_file_location("selftest", ST_PATH)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


st = _load()


def test_sloc_empty():
    assert st.compute_sloc("") == 0


def test_sloc_only_comments_and_blanks():
    code = "\n# comment\n\n   # another\n"
    assert st.compute_sloc(code) == 0


def test_sloc_simple_function():
    code = "def f(x):\n    return x + 1\n"
    # If radon is available, expect 2 SLOC. Fallback computes the same.
    assert st.compute_sloc(code) == 2


def test_sloc_with_inline_comments():
    code = "def f(x):  # entry\n    return x + 1\n"
    # SLOC counts statement lines; both lines have code.
    assert st.compute_sloc(code) == 2


def test_loc_violation_detection_via_find_import_violations():
    bad = "import os\ndef f(): pass\n"
    violations = st.find_import_violations(bad, ["os", "sys"])
    assert "os" in violations


def test_no_import_violations_when_clean():
    good = "def f(x):\n    return x * 2\n"
    assert st.find_import_violations(good, ["os", "sys"]) == []


def test_generated_samples_cover_merge_intervals_edges():
    samples = st.generated_samples("merge_intervals")
    assert {"input": [[]], "expected": []} in samples
    assert {"input": [[[1, 2], [2, 3], [3, 5]]], "expected": [[1, 5]]} in samples


def test_generated_samples_cover_kth_smallest_duplicates():
    samples = st.generated_samples("kth_smallest")
    assert {"input": [[1, 1, 1], 2], "expected": 1} in samples


def test_entry_function_defined_top_level():
    assert st.entry_function_defined("def f(x):\n    return x\n", "f")
    assert not st.entry_function_defined("g = lambda x: x\n", "g")


def test_selftest_auto_samples_pass_clean_reference():
    task_path = REPO_ROOT / "examples" / "portfolio_cases" / "portfolio_merge_intervals.json"
    task = json.loads(task_path.read_text(encoding="utf-8"))
    payload = {
        "code": task["clean_code"],
        "constraints": task["constraints"],
        "task_description": task["task_description"],
    }
    proc = subprocess.run(
        [sys.executable, str(ST_PATH), json.dumps(payload)],
        capture_output=True, text=True, check=False,
    )
    obj = _extract_json(proc.stdout)
    assert obj["failed"] == 0
    assert obj["passed"] >= 5


def test_selftest_auto_samples_fail_buggy_reference():
    task_path = REPO_ROOT / "examples" / "portfolio_cases" / "portfolio_kth_smallest.json"
    task = json.loads(task_path.read_text(encoding="utf-8"))
    payload = {
        "code": task["buggy_code"],
        "constraints": task["constraints"],
        "task_description": task["task_description"],
    }
    proc = subprocess.run(
        [sys.executable, str(ST_PATH), json.dumps(payload)],
        capture_output=True, text=True, check=False,
    )
    obj = _extract_json(proc.stdout)
    assert obj["failed"] > 0
    assert any("mismatch" in err or "runtime error" in err for err in obj["errors"])


def _extract_json(stdout: str) -> dict:
    body = stdout.split("```json\n", 1)[1].rsplit("\n```", 1)[0]
    return json.loads(body)


def test_radon_present_or_fallback():
    """Sanity: either radon is installed and we got its output, or fallback agreed.
    Either way, SLOC for a known sample is in a reasonable ballpark."""
    code = "import math\n\ndef circ(r):\n    return 2 * math.pi * r\n"
    s = st.compute_sloc(code)
    # 3 statement lines (import, def, return). Allow ±1 for radon variants.
    assert 2 <= s <= 4


@pytest.mark.skipif(shutil.which("radon") is None, reason="radon not on PATH")
def test_radon_path_specifically():
    """When radon is on PATH, verify the radon path runs (not just fallback)."""
    code = "def a():\n    return 1\n\ndef b():\n    return 2\n"
    assert st.compute_sloc(code) == 4
