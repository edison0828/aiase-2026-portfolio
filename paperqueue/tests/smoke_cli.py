"""Portfolio-added CLI regression checks (2026-10-07), with Codex assistance.

This is not the course grader. All data lives in a temporary directory.
Only the Python standard library is required; original application code is intact.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CALLS = 0


def run(version: str, db: Path, args: list[str], *, code: int = 0,
        stdout: str | None = None, stderr: str = "") -> str:
    global CALLS
    result = subprocess.run(
        [sys.executable, "-B", str(ROOT / version / "main.py"), "--db", str(db), *args],
        cwd=db.parent, capture_output=True, text=True, encoding="utf-8", timeout=10,
    )
    CALLS += 1
    actual = (result.returncode, result.stdout, result.stderr)
    if result.returncode != code or result.stderr != (stderr + "\n" if stderr else ""):
        raise AssertionError(f"{version} {args}: unexpected result {actual!r}")
    if stdout is not None and result.stdout != stdout + "\n":
        raise AssertionError(f"{version} {args}: expected stdout {stdout!r}, got {result.stdout!r}")
    return result.stdout


def regression(version: str, db: Path) -> None:
    """The nine sequential examples specified in the original v1 SDD."""
    cases = [
        (["add", "--title", "Spec-Driven Development for AI Systems", "--authors", "Alice Chen;Bob Lin",
          "--year", "2024", "--venue", "AIASE", "--tags", "sdd,ai", "--url", "https://example.org/sdd",
          "--priority", "5"], "Added: [1] Spec-Driven Development for AI Systems"),
        (["add", "--title", "Retrieval-Augmented Generation in Practice", "--authors", "Carol Wu",
          "--year", "2023", "--venue", "NLPConf", "--tags", "rag,nlp", "--priority", "3"],
         "Added: [2] Retrieval-Augmented Generation in Practice"),
        (["list", "--sort", "priority"],
         "[1] unread | p=5 | 2024 | Spec-Driven Development for AI Systems\n"
         "[2] unread | p=3 | 2023 | Retrieval-Augmented Generation in Practice"),
        (["show", "--id", "1"],
         "id: 1\ntitle: Spec-Driven Development for AI Systems\nauthors: Alice Chen; Bob Lin\nyear: 2024\n"
         "venue: AIASE\nstatus: unread\npriority: 5\ntags: sdd,ai\nurl: https://example.org/sdd\npdf_path: -\nnotes: 0"),
        (["update", "--id", "1", "--status", "reading", "--priority", "4"], "Updated: [1]"),
        (["note", "--id", "1", "--text", "Focus on the compatibility section."], "Added note: [1]"),
        (["next"], "Next: [1] Spec-Driven Development for AI Systems"),
        (["delete", "--id", "2"], "Deleted: [2] Retrieval-Augmented Generation in Practice"),
        (["stats"], "total: 1\nunread: 0\nreading: 1\nread: 0\nnotes: 1"),
    ]
    for args, expected in cases:
        run(version, db, args, stdout=expected)
    invalid = [
        (["show", "--id", "999"], 1, "Error: paper not found: 999"),
        (["update", "--id", "1"], 2, "Error: no fields to update"),
        (["update", "--id", "1", "--priority", "0"], 2, "Error: invalid priority: 0"),
        (["note", "--id", "1", "--text", "   "], 2, "Error: note text must not be empty"),
    ]
    for args, code, error in invalid:
        if run(version, db, args, code=code, stderr=error):
            raise AssertionError("An error unexpectedly wrote to stdout")
    broken = db.with_name(version + "-broken.json")
    broken.write_text("{ invalid JSON", encoding="utf-8")
    run(version, broken, ["list"], code=3, stderr="Error: failed to read database")


def without_timestamps(db: Path) -> dict:
    data = json.loads(db.read_text(encoding="utf-8"))
    for record in data["papers"] + data["notes"]:
        record.pop("created_at", None)
        record.pop("updated_at", None)
    return data


def extensions(db: Path) -> None:
    def v2(args: list[str], **kwargs) -> str:
        return run("v2", db, args, **kwargs)

    v2(["add", "--title", "Paper A", "--authors", "Alice", "--year", "2024", "--tags", "ai,nlp",
        "--priority", "5"], stdout="Added: [1] Paper A")
    v2(["add", "--title", "Paper B", "--authors", "Bob", "--year", "2022", "--tags", "systems"],
       stdout="Added: [2] Paper B")
    v2(["note", "--id", "1", "--text", "保留的閱讀筆記"], stdout="Added note: [1]")
    v2(["note", "--id", "1", "--text", "delete this note"], stdout="Added note: [1]")
    notes = v2(["note", "--id", "1", "--list"])
    if not re.search(r"\[1\] .+ \| 保留的閱讀筆記", notes) or "delete this note" not in notes:
        raise AssertionError("Notes were not listed with identifiers and contents")
    v2(["note", "--delete-note", "2"], stdout="Deleted note: [2]")
    v2(["note", "--delete-note", "999"], code=1, stderr="Error: note not found: 999")
    v2(["tag", "--id", "1", "--add", "rag,nlp"], stdout="Tags: ai,nlp,rag")
    v2(["tag", "--id", "1", "--remove", "missing,rag"], stdout="Missing tags: missing\nTags: ai,nlp")
    v2(["next", "--tag", "nlp", "--year-min", "2024"], stdout="Next: [1] Paper A")
    v2(["next", "--tag", "nlp", "--year-min", "2025"], stdout="No candidate papers found.")
    filtered = v2(["export", "--tag", "nlp"])
    if not filtered.startswith("# PaperQueue Export\n") or "## [1] Paper A" not in filtered:
        raise AssertionError("Export is missing its heading or selected paper")
    if "保留的閱讀筆記" not in filtered or "Paper B" in filtered or "delete this note" in filtered:
        raise AssertionError("Export did not respect filtering or persisted note deletion")
    output = db.parent / "export.md"
    v2(["export", "--output", str(output)], stdout=f"Exported: 2 papers to {output}")
    original = output.read_bytes()
    v2(["export", "--tag", "nlp", "--output", str(output)], code=2,
       stderr=f"Error: output file already exists: {output}")
    if output.read_bytes() != original:
        raise AssertionError("Protected output was modified")
    v2(["export", "--tag", "nlp", "--output", str(output), "--force"],
       stdout=f"Exported: 1 papers to {output}")
    if output.read_text(encoding="utf-8") != filtered:
        raise AssertionError("Forced export differs from stdout export")
    state = json.loads(db.read_text(encoding="utf-8"))
    if state["papers"][0]["tags"] != ["ai", "nlp"] or [n["id"] for n in state["notes"]] != [1]:
        raise AssertionError("Persisted tags or notes differ from the requested changes")


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="paperqueue-smoke-") as directory:
        tmp = Path(directory)
        for version in ("v1", "v2"):
            regression(version, tmp / f"{version}.json")
        if without_timestamps(tmp / "v1.json") != without_timestamps(tmp / "v2.json"):
            raise AssertionError("Shared workflow produced different persisted data")
        run("v2", tmp / "v1.json", ["stats"], stdout="total: 1\nunread: 0\nreading: 1\nread: 0\nnotes: 1")
        extensions(tmp / "extended.json")
    print(f"PASS: {CALLS} CLI invocations; v1/v2 regression, persisted data, v2 extensions and error cases.")


if __name__ == "__main__":
    main()
