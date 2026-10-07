"""Portfolio-added lexical smoke demo (2026-10-07); not the course benchmark."""
from __future__ import annotations
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from memory.bm25 import bm25_search


def main() -> None:
    observations = json.loads((ROOT / "examples/observations.json").read_text())
    queries = json.loads((ROOT / "examples/queries.json").read_text())
    docs = [{"id": row["id"], "text": row["summary"]} for row in observations]
    matched = 0
    for row in queries:
        first = bm25_search(row["query"], docs, k=1)[0]["id"]
        matched += first == row["expected_id"]
        print(f"{row['query']} -> {first}")
    print(f"Toy lexical matches at rank 1: {matched}/{len(queries)}")
    print("Synthetic exact-word examples only; not evidence of semantic retrieval quality.")


if __name__ == "__main__":
    main()
