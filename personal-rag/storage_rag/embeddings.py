from __future__ import annotations

import hashlib
import math
import os
import re
from collections import Counter
from pathlib import Path


class HashingFallbackEmbedder:
    def __init__(self, dimensions: int = 384) -> None:
        self.dimensions = dimensions

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [self._embed_single(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._embed_single(text)

    def _embed_single(self, text: str) -> list[float]:
        tokens = re.findall(r"\w+", text.lower())
        counts = Counter(tokens)
        vector = [0.0] * self.dimensions
        for token, weight in counts.items():
            digest = hashlib.sha256(token.encode("utf-8")).hexdigest()
            bucket = int(digest[:8], 16) % self.dimensions
            vector[bucket] += float(weight)
        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / norm for value in vector]


class SentenceTransformersEmbedder:
    def __init__(self, model_name: str) -> None:
        from sentence_transformers import SentenceTransformer

        self.model = SentenceTransformer(self._ensure_local_model_dir(model_name))

    def _ensure_local_model_dir(self, model_name: str) -> str:
        from huggingface_hub import snapshot_download

        hf_home = Path(os.getenv("HF_HOME", ".")).resolve()
        local_models_dir = hf_home / "local_models"
        local_models_dir.mkdir(parents=True, exist_ok=True)
        safe_name = re.sub(r"[^A-Za-z0-9._-]+", "__", model_name)
        target_dir = local_models_dir / safe_name
        repo_id = (
            model_name
            if "/" in model_name
            else f"sentence-transformers/{model_name}"
        )
        if not (target_dir / "modules.json").exists():
            snapshot_download(
                repo_id=repo_id,
                local_dir=str(target_dir),
                cache_dir=str(hf_home / "hub"),
            )
        return str(target_dir)

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        vectors = self.model.encode(
            texts,
            batch_size=16,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return [vector.tolist() for vector in vectors]

    def embed_query(self, text: str) -> list[float]:
        return self.embed_texts([text])[0]


class LiteLLMEmbedder:
    def __init__(self, provider: str, model_name: str) -> None:
        self.provider = provider
        self.model_name = model_name

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        from litellm import embedding

        model_name = self.model_name
        if self.provider == "huggingface" and not model_name.startswith("huggingface/"):
            model_name = f"huggingface/{model_name}"
        if self.provider == "ollama" and not model_name.startswith("ollama/"):
            model_name = f"ollama/{model_name}"

        response = embedding(model=model_name, input=texts)
        return [item["embedding"] for item in response.data]

    def embed_query(self, text: str) -> list[float]:
        return self.embed_texts([text])[0]


def build_embedder(provider: str, model_name: str):
    # Portfolio change: never silently mix hash and semantic vectors in an index.
    if provider == "hashing":
        return HashingFallbackEmbedder()
    if provider == "sentence-transformers":
        return SentenceTransformersEmbedder(model_name)
    if provider in {"huggingface", "ollama"}:
        return LiteLLMEmbedder(provider, model_name)
    raise ValueError(f"Unknown embedding provider: {provider}")
