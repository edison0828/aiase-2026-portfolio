#!/usr/bin/env python3
"""
Deterministic SQL validator for text2sql skill.

Usage:
    python validate_sql.py '{"schema_ddl":"CREATE TABLE ...", "sql":"SELECT ..."}'

Prints a single fenced JSON block:
    {"ok": true|false, "error": "<sqlite error or rule violation>"}

Strategy:
1. Reject multiple statements / non-SELECT / DDL / DML up front (cheap, no DB needed).
2. Build the schema in an in-memory sqlite (no data).
3. Run `EXPLAIN <sql>` — this parses & resolves column names without needing data.
4. On sqlite3.Error, return its message so the LLM can fix the draft.
"""

from __future__ import annotations

import json
import re
import sqlite3
import sys


FORBIDDEN = re.compile(
    r"\b(INSERT|UPDATE|DELETE|CREATE|DROP|ALTER|ATTACH|DETACH|REPLACE|TRUNCATE|VACUUM|PRAGMA)\b",
    re.IGNORECASE,
)
STARTS_WITH_SELECT = re.compile(r"^\s*SELECT\b", re.IGNORECASE)
STARTS_WITH_WITH = re.compile(r"^\s*WITH\b", re.IGNORECASE)


def _emit(ok: bool, error: str = "") -> int:
    out = {"ok": bool(ok), "error": error}
    sys.stdout.write("```json\n")
    sys.stdout.write(json.dumps(out, ensure_ascii=False))
    sys.stdout.write("\n```\n")
    return 0 if ok else 1


def _mask_literals_and_comments(sql: str) -> str:
    """Return SQL with string literals, quoted identifiers, and comments masked as spaces."""
    chars = list(sql)
    i = 0
    n = len(chars)
    while i < n:
        ch = chars[i]
        nxt = chars[i + 1] if i + 1 < n else ""

        if ch == "'":
            chars[i] = " "
            i += 1
            while i < n:
                if chars[i] == "'" and i + 1 < n and chars[i + 1] == "'":
                    chars[i] = chars[i + 1] = " "
                    i += 2
                    continue
                end = chars[i] == "'"
                chars[i] = " "
                i += 1
                if end:
                    break
            continue

        if ch in ('"', "`", "["):
            closing = "]" if ch == "[" else ch
            chars[i] = " "
            i += 1
            while i < n:
                end = chars[i] == closing
                chars[i] = " "
                i += 1
                if end:
                    break
            continue

        if ch == "-" and nxt == "-":
            chars[i] = chars[i + 1] = " "
            i += 2
            while i < n and chars[i] not in "\r\n":
                chars[i] = " "
                i += 1
            continue

        if ch == "/" and nxt == "*":
            chars[i] = chars[i + 1] = " "
            i += 2
            while i < n:
                if chars[i] == "*" and i + 1 < n and chars[i + 1] == "/":
                    chars[i] = chars[i + 1] = " "
                    i += 2
                    break
                chars[i] = " "
                i += 1
            continue

        i += 1
    return "".join(chars)


def _strip_single_trailing_semicolon(sql: str, masked: str) -> tuple[str, str, str]:
    semis = [i for i, ch in enumerate(masked) if ch == ";"]
    if not semis:
        return sql.strip(), masked.strip(), ""
    if len(semis) > 1:
        return "", "", "multiple SQL statements not allowed"

    semi = semis[0]
    if masked[semi + 1:].strip():
        return "", "", "multiple SQL statements not allowed"
    return sql[:semi].strip(), masked[:semi].strip(), ""


def validate(schema_ddl: str, sql: str) -> tuple[bool, str]:
    sql_stripped = sql.strip()
    if not sql_stripped:
        return False, "empty SQL"

    masked = _mask_literals_and_comments(sql_stripped)
    sql_stripped, masked, stmt_err = _strip_single_trailing_semicolon(sql_stripped, masked)
    if stmt_err:
        return False, stmt_err
    if not sql_stripped:
        return False, "empty SQL"
    if STARTS_WITH_WITH.match(masked):
        return False, "CTE/WITH not allowed; rewrite as a SELECT with subqueries"
    if FORBIDDEN.search(masked):
        return False, "DDL/DML/PRAGMA not allowed; SELECT only"
    if not STARTS_WITH_SELECT.match(masked):
        return False, "only SELECT statements are allowed"

    con = sqlite3.connect(":memory:")
    try:
        if schema_ddl:
            try:
                con.executescript(schema_ddl)
            except sqlite3.Error as e:
                return False, f"schema DDL did not parse: {e}"
        try:
            con.execute(f"EXPLAIN {sql_stripped}")
        except sqlite3.Error as e:
            return False, f"SQL did not compile: {e}"
        return True, ""
    finally:
        con.close()


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        return _emit(False, "usage: validate_sql.py '<json payload>'")
    try:
        payload = json.loads(argv[1])
    except json.JSONDecodeError as e:
        return _emit(False, f"argv JSON invalid: {e}")
    ok, err = validate(str(payload.get("schema_ddl", "")), str(payload.get("sql", "")))
    return _emit(ok, err)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
