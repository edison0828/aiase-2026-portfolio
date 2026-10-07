# Source: TAICA AIASE 2026 HW4 Python starter (ktchuang/TAICA_AIASE2026).
# Student-completed scoring/persistence retained; portfolio edits only simplify scaffold comments.
"""BM25-lite：給每筆文件對查詢打相關度分數，回傳排序後的前 K 筆。
tokenize() 來自課程骨架；bm25_search() 為作業完成的計分實作。"""
from __future__ import annotations
import math
import re
from collections import Counter

_TOKEN_RE = re.compile(r"[a-z0-9]+|[\u4e00-\u9fff]")


def tokenize(text: str) -> list[str]:
    """小寫化後，取出英數字詞與單個 CJK 字元。不做 stemming。（已提供）"""
    return _TOKEN_RE.findall(text.lower())


def bm25_search(
    query: str,
    docs: list[dict],
    k: int = 8,
    k1: float = 1.5,
    b: float = 0.75,
) -> list[dict]:
    """Rank documents by BM25; keep input order when scores tie."""
    if not docs or k <= 0:
        return []

    query_terms = tokenize(query)
    tokenized_docs = [tokenize(str(doc.get("text", ""))) for doc in docs]
    doc_lengths = [len(tokens) for tokens in tokenized_docs]
    avgdl = sum(doc_lengths) / len(doc_lengths) if doc_lengths else 0.0

    df: Counter[str] = Counter()
    for tokens in tokenized_docs:
        df.update(set(tokens))

    n_docs = len(docs)
    scored: list[tuple[int, dict]] = []
    for index, (doc, tokens, doc_len) in enumerate(zip(docs, tokenized_docs, doc_lengths)):
        tf = Counter(tokens)
        score = 0.0

        for term in query_terms:
            term_tf = tf.get(term, 0)
            if term_tf == 0:
                continue

            term_df = df[term]
            idf = math.log((n_docs - term_df + 0.5) / (term_df + 0.5) + 1)
            denom = term_tf + k1 * (1 - b + b * doc_len / avgdl) if avgdl else term_tf + k1
            score += idf * (term_tf * (k1 + 1)) / denom

        scored.append((index, {"id": doc.get("id"), "score": score}))

    scored.sort(key=lambda item: (-item[1]["score"], item[0]))
    return [result for _, result in scored[:k]]
