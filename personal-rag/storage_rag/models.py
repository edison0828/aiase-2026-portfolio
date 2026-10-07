from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class ProcessedSource:
    source_id: str
    title: str
    raw_path: str
    processed_path: str
    sha256: str
    text: str
    paragraph_count: int
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ChunkRecord:
    chunk_id: str
    source_id: str
    title: str
    raw_path: str
    processed_path: str
    chunk_index: int
    paragraph_start: int
    paragraph_end: int
    text: str
    metadata: dict[str, Any]

    def to_store_payload(self, embedding: list[float]) -> dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "source_id": self.source_id,
            "title": self.title,
            "raw_path": self.raw_path,
            "processed_path": self.processed_path,
            "chunk_index": self.chunk_index,
            "paragraph_start": self.paragraph_start,
            "paragraph_end": self.paragraph_end,
            "text": self.text,
            "metadata": self.metadata,
            "embedding": embedding,
        }


@dataclass(slots=True)
class SearchHit:
    chunk_id: str
    source_id: str
    title: str
    raw_path: str
    processed_path: str
    chunk_index: int
    paragraph_start: int
    paragraph_end: int
    text: str
    metadata: dict[str, Any]
    score: float

    @property
    def citation(self) -> str:
        filename = self.raw_path.replace("\\", "/").split("/")[-1]
        return f"[{filename} ¶{self.paragraph_start}-{self.paragraph_end}]"

