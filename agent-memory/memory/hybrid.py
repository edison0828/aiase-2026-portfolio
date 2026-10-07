"""Optional hybrid retrieval: BM25 plus local sentence embeddings."""
from __future__ import annotations

import math

from .bm25 import bm25_search

DEFAULT_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


def _minmax(scores: list[float]) -> list[float]:
    if not scores:
        return []
    lo, hi = min(scores), max(scores)
    if math.isclose(lo, hi):
        return [0.0 for _ in scores]
    return [(score - lo) / (hi - lo) for score in scores]


def _cosine(a, b) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


class HybridRetriever:
    """Reusable hybrid ranker that loads the model and encodes docs once."""

    def __init__(
        self,
        docs: list[dict],
        *,
        bm25_weight: float = 0.65,
        model_name: str = DEFAULT_MODEL,
    ):
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise RuntimeError(
                "hybrid retrieval requires sentence-transformers; install the optional dependency first"
            ) from exc

        self.docs = docs
        self.bm25_weight = bm25_weight
        self.model = SentenceTransformer(model_name)
        self.texts = [str(doc.get("text", "")) for doc in docs]
        self.doc_embeddings = self.model.encode(self.texts, normalize_embeddings=True)

    def search(self, query: str, k: int = 8) -> list[dict]:
        if not self.docs or k <= 0:
            return []

        query_embedding = self.model.encode(query, normalize_embeddings=True)
        bm25_ranked = bm25_search(query, self.docs, len(self.docs))
        bm25_by_id = {row["id"]: row["score"] for row in bm25_ranked}
        bm25_scores = [bm25_by_id.get(doc.get("id"), 0.0) for doc in self.docs]
        dense_scores = [_cosine(query_embedding, doc_embedding) for doc_embedding in self.doc_embeddings]

        norm_bm25 = _minmax(bm25_scores)
        norm_dense = _minmax(dense_scores)
        dense_weight = 1.0 - self.bm25_weight

        scored = []
        for index, doc in enumerate(self.docs):
            score = self.bm25_weight * norm_bm25[index] + dense_weight * norm_dense[index]
            scored.append((index, {"id": doc.get("id"), "score": score}))

        scored.sort(key=lambda item: (-item[1]["score"], item[0]))
        return [result for _, result in scored[:k]]


def hybrid_search(
    query: str,
    docs: list[dict],
    k: int = 8,
    *,
    bm25_weight: float = 0.65,
    model_name: str = DEFAULT_MODEL,
) -> list[dict]:
    """Rank documents with normalized BM25 and embedding cosine similarity.

    This is intentionally separate from bm25_search() so the deterministic
    implementation used by tests and core retrieval remains unchanged.
    """
    return HybridRetriever(docs, bm25_weight=bm25_weight, model_name=model_name).search(query, k)
