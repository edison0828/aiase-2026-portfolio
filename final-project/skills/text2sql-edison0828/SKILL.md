---
name: text2sql-edison0828
description: Convert natural-language questions and SQLite schemas into verified read-only SQL, then use terminal to run scripts/run.py and write AIASE_RESULT_PATH; never answer with SQL text only.
version: 0.1.0
metadata:
  hermes:
    tags: [sql, text2sql, data, aiase-2026]
    category: data
---

# Text2SQL Skill (Basic Track)

## Critical Output Rule

Do not finish by printing SQL in the conversation. A direct SQL answer is a failed submission because the grader only reads the result file. You must call the terminal and run `scripts/run.py` so the JSON contract is written to `AIASE_RESULT_PATH`.

If you are in the repository root, either set `workdir` to `skills/text2sql-edison0828` before running `python3 scripts/run.py`, or run the repo-root fallback `python3 scripts/run.py`. In all cases, verify the terminal output says it wrote the result file.

## When to Use

When the user sends a JSON payload with `question`, `db_schema` (SQLite DDL), and optional `task_id` + `dialect`. The skill must produce a single read-only SQLite query whose result on the hidden DB matches the gold answer under bag equality.

Trigger example:

```
/text2sql-edison0828 {"task_id":"task_nl2sql_017",
  "question":"List the names of all students who scored above 90 ...",
  "db_schema":"CREATE TABLE Students(...); ...", "dialect":"sqlite"}
```

## Procedure

1. **Parse the payload exactly.** Extract `task_id`, `question`, `db_schema`, and `dialect`. Copy `task_id` unchanged into the final output.
2. **Ground yourself in the schema before writing SQL.**
   - List the tables and their columns from `db_schema`.
   - Identify likely key columns from primary keys and shared suffixes such as `sid`, `cid`, `pid`, `doc_id`, `did`, `tid`, `gid`, `oid`.
   - Decide the minimum table path needed to answer the question; do not select from unrelated tables.
3. **Translate the question into a compact SQL plan.**
   - "for each" means `GROUP BY` the entity id and display column.
   - "include zero / no ..." means `LEFT JOIN` and count a nullable child key, for example `COUNT(child.id)`.
   - "not placed any / no outstanding ..." usually means `LEFT JOIN ... IS NULL`, `NOT IN`, or `NOT EXISTS`.
   - "all / every" usually means double-negative `NOT EXISTS`.
   - "distinct names/titles" means `SELECT DISTINCT`.
   - "plus / OR from two populations" can use `UNION`.
   - "top N / oldest N" requires `ORDER BY ... DESC LIMIT N`.
4. **Draft exactly one SQLite `SELECT` statement.**
   - No CTE / `WITH`, no DDL/DML, no PRAGMA, no comments, no markdown fences.
   - Subqueries are allowed up to the project scope, including nested `IN` and `NOT EXISTS`.
   - Prefer table aliases (`s`, `c`, `e`, etc.) and qualify columns whenever more than one table is used.
   - Every text literal from the question must be quoted with single quotes, for example `dept.name = 'Cardiology'`, `t.name = 'Tigers'`, and `s.dept = 'CS'`. Bare words like `Cardiology`, `Tigers`, or `CS` are column names in SQLite and will fail.
5. **Validate the SQL deterministically.** Run:

   ```bash
   python scripts/validate_sql.py '{"schema_ddl":"<db_schema>","sql":"<candidate SQL>"}'
   ```

   It checks single-statement, read-only SQLite syntax and resolves table/column names with `EXPLAIN`.
6. **Retry up to three times when validation fails.**
   - `no such column/table`: re-read the DDL and fix the identifier or join path.
   - `near ... syntax error`: simplify the query and remove non-SQLite syntax.
   - `CTE/WITH not allowed`: rewrite as a subquery.
   - If all retries fail, emit the best SQL with lower confidence.
7. **Write the final contract by running `scripts/run.py`; this step is mandatory.** Use the terminal tool from the skill directory. Do not put raw JSON inside shell quotes, because SQL text literals such as `'CS'` can break the shell command. Use this Python `json.dumps` pattern:

   ```bash
python3 - <<'PY'
import json, subprocess
payload = {
    "task_id": "<same task_id>",
    "sql": "<validated SQL>",
    "rationale": "<short reason>",
    "confidence": 0.8,
}
subprocess.run(["python3", "scripts/run.py", json.dumps(payload)], check=True)
PY
   ```

   Do not handwrite the JSON result file yourself, do not create `result.json`, do not create files under `references/`, and do not stop after validation. The script writes the result JSON to `AIASE_RESULT_PATH`; `./aiase_result.json` is only a fallback for direct local script execution when the variable is absent.

## Query Patterns

Use these patterns as templates; adapt table and column names from the actual `db_schema`.

```sql
-- 3-table enrollment join
SELECT s.name
FROM Students s
JOIN Enrollments e ON s.sid = e.sid
JOIN Courses c ON e.cid = c.cid
WHERE c.title = 'AI Foundations'
```

```sql
-- Per-entity aggregate, sorted
SELECT c.title, AVG(e.score)
FROM Courses c
JOIN Enrollments e ON c.cid = e.cid
GROUP BY c.cid, c.title
ORDER BY AVG(e.score) DESC
```

```sql
-- Include parent rows with zero children
SELECT a.name, COUNT(child.id)
FROM Parent a
LEFT JOIN Child child ON a.id = child.parent_id
GROUP BY a.id, a.name
```

```sql
-- Every / all condition by double-negative NOT EXISTS
SELECT p.name
FROM Players p
WHERE NOT EXISTS (
  SELECT 1
  FROM Games g
  WHERE g.home_tid = p.tid
    AND NOT EXISTS (
      SELECT 1
      FROM Goals go
      WHERE go.gid = g.gid AND go.pid = p.pid
    )
)
```

## Pitfalls

- **Many-to-many JOINs without DISTINCT** → duplicate rows. The grader uses bag (multiset) equality, so duplicate rows fail. If the question semantically asks for a set ("list the students who ..."), use `DISTINCT`.
- **Wrong grouping key** → unstable duplicates. When returning a name/title after aggregation, group by both the entity primary key and the displayed text, e.g. `GROUP BY s.sid, s.name`.
- **Counting zero rows with `COUNT(*)` after a `LEFT JOIN`** → false 1s. Use `COUNT(child.id)` or another nullable child-side key.
- **Tie handling**: if the question says "if multiple tie, return all", do not use `LIMIT 1`; compare the count/score against a subquery maximum.
- **Column / table names** must exist in the given schema. `validate_sql.py` uses `EXPLAIN` against an in-memory DB built from the DDL; references to nonexistent columns will fail there.
- **Text constants** must be quoted. `WHERE dep.name = Cardiology` and `WHERE dept = CS` are invalid because SQLite treats bare words as columns; write `WHERE dep.name = 'Cardiology'` and `WHERE dept = 'CS'`.
- **Dialect**: always SQLite. No window functions, no CTE / `WITH`, no recursive queries (regardless of what dialect the LLM "feels like" using). See spec §2.2.
- **Single statement**: exactly one query, no semicolon-separated multiples.
- **Read-only**: no `INSERT` / `UPDATE` / `DELETE` / DDL.
- **task_id** in your output must equal the input `task_id`. The grader rejects mismatches.

## Verification

The result file written by `scripts/run.py` is a JSON object with:

- `task_id` (must equal input)
- `sql` (single read-only SQLite query)
- `rationale` (string)
- `confidence` (number in `[0.0, 1.0]`)

The grader reads the file path from `AIASE_RESULT_PATH`; it does not grade JSON printed in the conversation. If `AIASE_RESULT_PATH` exists, that path is authoritative and must receive the final JSON object.
