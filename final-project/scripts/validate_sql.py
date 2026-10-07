#!/usr/bin/env python3
"""Repo-root compatibility wrapper for the Text2SQL validator."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main(argv: list[str]) -> int:
    target = (
        Path(__file__).resolve().parents[1]
        / "skills"
        / "text2sql-edison0828"
        / "scripts"
        / "validate_sql.py"
    )
    proc = subprocess.run([sys.executable, str(target), *argv[1:]])
    return proc.returncode


if __name__ == "__main__":
    sys.exit(main(sys.argv))
