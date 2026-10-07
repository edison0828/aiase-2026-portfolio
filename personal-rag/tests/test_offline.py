"""Portfolio-added integration checks, 2026-10-07; not course grading tests."""
from __future__ import annotations

import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import unittest


PROJECT = Path(__file__).resolve().parents[1]


class OfflineWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.project = Path(self.temp.name)
        for name in ["data_update.py", "rag_query.py", "skill_builder.py"]:
            shutil.copy2(PROJECT / name, self.project / name)
        shutil.copytree(PROJECT / "storage_rag", self.project / "storage_rag",
                        ignore=shutil.ignore_patterns("__pycache__"))
        shutil.copytree(PROJECT / "data/raw", self.project / "data/raw")
        self.env = os.environ.copy()
        for key in ["RAG_API_KEY", "RAG_BASE_URL", "RAG_CHAT_MODEL", "VECTOR_STORE_PATH"]:
            self.env.pop(key, None)
        self.env.update(EMBEDDING_PROVIDER="hashing", HF_HUB_OFFLINE="1",
                        TRANSFORMERS_OFFLINE="1", PYTHONDONTWRITEBYTECODE="1")

    def run_cli(self, *args):
        result = subprocess.run([sys.executable, *args], cwd=self.project,
                                env=self.env, text=True, capture_output=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result.stdout

    def test_index_query_and_visible_offline_mode(self):
        built = self.run_cli("data_update.py", "--rebuild")
        self.assertIn("hashing", built)
        answer = self.run_cli("rag_query.py", "--query", "ambercache evicting persistent copy", "--top-k", "1")
        self.assertIn("未使用生成模型", answer)
        self.assertIn("Sources:", answer)
        self.assertIn("[demo_read_cache.md", answer)
        self.assertRegex(answer, r"\[[^\]\n]+ ¶\d+-\d+\]")
        # This is a pipeline/citation check, not an assertion of relevance.
        # Multiple explicit words make this example inspectable; a single word
        # can still collide with unrelated original reading notes.

    def test_incremental_change_and_deleted_processed_file(self):
        self.run_cli("data_update.py", "--rebuild")
        self.assertIn("No files changed", self.run_cli("data_update.py"))
        raw = self.project / "data/raw/demo_read_cache.md"
        raw.write_text(raw.read_text() + "\n\nThe new lookup marker is saffronrefresh.\n")
        self.assertIn("1 changed source(s)", self.run_cli("data_update.py"))
        # Check the changed stored content directly: hash collisions mean that
        # an arbitrary new word is not guaranteed to retrieve its source first.
        with sqlite3.connect(self.project / "artifacts/vector_store.sqlite3") as conn:
            updated = conn.execute("SELECT text FROM chunks WHERE source_id=?",
                                   ("demo_read_cache",)).fetchall()
        self.assertTrue(any("saffronrefresh" in row[0] for row in updated))
        raw.unlink()
        self.assertIn("removed 1 source(s)", self.run_cli("data_update.py"))
        self.assertFalse((self.project / "data/processed/demo_read_cache.txt").exists())
        with sqlite3.connect(self.project / "artifacts/vector_store.sqlite3") as conn:
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM chunks WHERE source_id=?",
                                          ("demo_read_cache",)).fetchone()[0], 0)

    def test_generated_document_without_model(self):
        self.run_cli("data_update.py", "--rebuild")
        self.run_cli("skill_builder.py")
        result = (self.project / "artifacts/generated_skill.md").read_text()
        self.assertIn("## Source References", result)
        self.assertIn("raw/demo_read_cache.md", result)
        self.assertIn("未使用生成模型", result)


if __name__ == "__main__":
    unittest.main()
