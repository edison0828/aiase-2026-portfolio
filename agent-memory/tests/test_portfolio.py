"""Portfolio-added tests, 2026-10-07; all examples are newly written and fictional."""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from memory.bm25 import bm25_search
from memory.store import JsonStore
from memory.core import set_memory_path, capture, make_observation, build_injection


PROJECT = Path(__file__).resolve().parents[1]


class MemoryWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "observations.json"

    def test_new_toy_relevance_examples(self):
        rows = json.loads((PROJECT / "examples/observations.json").read_text())
        docs = [{"id": row["id"], "text": row["summary"]} for row in rows]
        queries = json.loads((PROJECT / "examples/queries.json").read_text())
        for row in queries:
            with self.subTest(query=row["query"]):
                self.assertEqual(bm25_search(row["query"], docs, 1)[0]["id"], row["expected_id"])

    def test_empty_input_and_equal_scores(self):
        self.assertEqual(bm25_search("microscope", [], 3), [])
        docs = [{"id": "x", "text": "basil"}, {"id": "y", "text": "basil"}]
        self.assertEqual([r["id"] for r in bm25_search("basil", docs, 2)], ["x", "y"])
        self.assertEqual(bm25_search("basil", docs, 0), [])

    def test_json_survives_reload_and_deduplicates(self):
        original = {"id": "fictional-map", "summary": "地圖以 GeoJSON 匯出。", "tags": ["地圖"]}
        first = JsonStore(str(self.path))
        self.assertTrue(first.add(original))
        loaded = JsonStore(str(self.path))
        self.assertEqual(loaded.all(), [original])
        self.assertFalse(loaded.add(original))
        self.assertEqual(JsonStore(str(self.path)).all(), [original])

    def test_capture_and_retrieve_across_cli_processes(self):
        env = dict(os.environ, PI_MEMORY_PATH=str(self.path), PYTHONDONTWRITEBYTECODE="1")
        def cli(*args):
            result = subprocess.run([sys.executable, "-m", "memory.cli", *args],
                                    cwd=PROJECT, env=env, text=True, capture_output=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            return result.stdout
        cli("capture", "--summary", "The fictional seed vault stores basil seeds.", "--tags", "garden")
        found = json.loads(cli("retrieve", "--query", "basil", "--k", "1"))
        self.assertEqual(found[0]["summary"], "The fictional seed vault stores basil seeds.")
        self.assertIn("basil", cli("inject", "--query", "basil", "--budget", "100"))

    def test_small_injection_budget_omits_large_record(self):
        set_memory_path(str(self.path))
        capture(make_observation("basil " * 100))
        self.assertEqual(build_injection("basil", token_budget=10), "")


if __name__ == "__main__":
    unittest.main()
