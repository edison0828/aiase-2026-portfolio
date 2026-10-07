from __future__ import annotations

import json
import os
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from storage_rag.models import SearchHit


class SQLiteVectorStore:
    def __init__(self, db_path: Path) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def reset(self) -> None:
        if self.db_path.exists():
            try:
                with self._connect() as conn:
                    conn.execute("DROP TABLE IF EXISTS chunks")
                    conn.execute("DROP TABLE IF EXISTS source_manifest")
            except sqlite3.Error:
                last_error: OSError | None = None
                for _ in range(10):
                    try:
                        os.remove(self.db_path)
                        last_error = None
                        break
                    except PermissionError as error:
                        last_error = error
                        time.sleep(0.2)
                if last_error is not None:
                    raise last_error
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS chunks (
                    chunk_id TEXT PRIMARY KEY,
                    source_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    raw_path TEXT NOT NULL,
                    processed_path TEXT NOT NULL,
                    chunk_index INTEGER NOT NULL,
                    paragraph_start INTEGER NOT NULL,
                    paragraph_end INTEGER NOT NULL,
                    text TEXT NOT NULL,
                    metadata_json TEXT NOT NULL,
                    embedding_json TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS source_manifest (
                    source_id TEXT PRIMARY KEY,
                    raw_path TEXT NOT NULL,
                    processed_path TEXT NOT NULL,
                    sha256 TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_chunks_source_id ON chunks(source_id)"
            )

    def get_manifest(self) -> dict[str, dict[str, str]]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM source_manifest").fetchall()
        return {
            row["source_id"]: {
                "raw_path": row["raw_path"],
                "processed_path": row["processed_path"],
                "sha256": row["sha256"],
                "updated_at": row["updated_at"],
            }
            for row in rows
        }

    def delete_source(self, source_id: str) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM chunks WHERE source_id = ?", (source_id,))
            conn.execute("DELETE FROM source_manifest WHERE source_id = ?", (source_id,))

    def replace_source(
        self,
        source_id: str,
        raw_path: str,
        processed_path: str,
        sha256: str,
        chunk_payloads: list[dict],
    ) -> None:
        timestamp = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            conn.execute("DELETE FROM chunks WHERE source_id = ?", (source_id,))
            conn.executemany(
                """
                INSERT INTO chunks (
                    chunk_id, source_id, title, raw_path, processed_path,
                    chunk_index, paragraph_start, paragraph_end, text,
                    metadata_json, embedding_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        payload["chunk_id"],
                        payload["source_id"],
                        payload["title"],
                        payload["raw_path"],
                        payload["processed_path"],
                        payload["chunk_index"],
                        payload["paragraph_start"],
                        payload["paragraph_end"],
                        payload["text"],
                        json.dumps(payload["metadata"], ensure_ascii=False),
                        json.dumps(payload["embedding"]),
                    )
                    for payload in chunk_payloads
                ],
            )
            conn.execute(
                """
                INSERT INTO source_manifest (source_id, raw_path, processed_path, sha256, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(source_id) DO UPDATE SET
                    raw_path=excluded.raw_path,
                    processed_path=excluded.processed_path,
                    sha256=excluded.sha256,
                    updated_at=excluded.updated_at
                """,
                (source_id, raw_path, processed_path, sha256, timestamp),
            )

    def search(self, query_embedding: list[float], top_k: int = 5) -> list[SearchHit]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM chunks").fetchall()

        if not rows:
            return []

        vectors = np.asarray(
            [json.loads(row["embedding_json"]) for row in rows],
            dtype=np.float32,
        )
        query = np.asarray(query_embedding, dtype=np.float32)
        if query.ndim != 1:
            query = query.reshape(-1)

        vector_norms = np.linalg.norm(vectors, axis=1)
        query_norm = np.linalg.norm(query)
        denom = np.maximum(vector_norms * max(query_norm, 1e-8), 1e-8)
        scores = (vectors @ query) / denom
        ranked_indices = np.argsort(scores)[::-1][:top_k]

        hits: list[SearchHit] = []
        for index in ranked_indices:
            row = rows[int(index)]
            hits.append(
                SearchHit(
                    chunk_id=row["chunk_id"],
                    source_id=row["source_id"],
                    title=row["title"],
                    raw_path=row["raw_path"],
                    processed_path=row["processed_path"],
                    chunk_index=row["chunk_index"],
                    paragraph_start=row["paragraph_start"],
                    paragraph_end=row["paragraph_end"],
                    text=row["text"],
                    metadata=json.loads(row["metadata_json"]),
                    score=float(scores[int(index)]),
                )
            )
        return hits

    def source_summaries(self) -> list[dict[str, str | int]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT
                    m.source_id,
                    m.raw_path,
                    m.processed_path,
                    m.sha256,
                    m.updated_at,
                    COUNT(c.chunk_id) AS chunk_count
                FROM source_manifest m
                LEFT JOIN chunks c ON c.source_id = m.source_id
                GROUP BY m.source_id, m.raw_path, m.processed_path, m.sha256, m.updated_at
                ORDER BY m.raw_path
                """
            ).fetchall()
        return [
            {
                "source_id": row["source_id"],
                "raw_path": row["raw_path"],
                "processed_path": row["processed_path"],
                "sha256": row["sha256"],
                "updated_at": row["updated_at"],
                "chunk_count": int(row["chunk_count"]),
            }
            for row in rows
        ]
