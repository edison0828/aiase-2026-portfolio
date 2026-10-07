from __future__ import annotations

from datetime import date
from typing import Any

from storage_rag.config import Settings
from storage_rag.embeddings import build_embedder
from storage_rag.models import SearchHit
from storage_rag.vector_store import SQLiteVectorStore


SYSTEM_PROMPT = """You are a research assistant for emerging storage systems.
Answer only from the retrieved context. If the context is insufficient, say so explicitly.
Every substantive claim must cite one or more of the provided citation tags exactly as given."""


def llm_available(settings: Settings) -> bool:
    return bool(settings.chat_api_key and settings.chat_base_url and settings.default_chat_model)


def proxy_chat_completion(
    *,
    settings: Settings,
    model: str,
    messages: list[dict[str, str]],
) -> Any:
    from openai import OpenAI

    client = OpenAI(
        api_key=settings.chat_api_key,
        base_url=settings.chat_base_url,
    )
    return client.chat.completions.create(
        model=model,
        messages=messages,
    )


def retrieve_hits(
    query: str,
    settings: Settings,
    *,
    top_k: int = 5,
) -> list[SearchHit]:
    embedder = build_embedder(settings.embedding_provider, settings.embedding_model)
    query_embedding = embedder.embed_query(query)
    store = SQLiteVectorStore(settings.vector_store_path)
    return store.search(query_embedding, top_k=top_k)


def build_context_block(hits: list[SearchHit]) -> str:
    sections: list[str] = []
    for position, hit in enumerate(hits, start=1):
        sections.append(
            "\n".join(
                [
                    f"Context {position}: {hit.citation}",
                    f"Title: {hit.title}",
                    hit.text,
                ]
            )
        )
    return "\n\n".join(sections)


def build_messages(
    query: str,
    hits: list[SearchHit],
    history: list[dict[str, str]] | None = None,
) -> list[dict[str, str]]:
    history = history or []
    user_prompt = (
        "Use the retrieved notes below to answer the question.\n\n"
        f"Question: {query}\n\n"
        "Retrieved context:\n"
        f"{build_context_block(hits)}\n\n"
        "Answer in Traditional Chinese when the question is in Chinese; otherwise mirror the user's language."
    )
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(history)
    messages.append({"role": "user", "content": user_prompt})
    return messages


def fallback_answer(query: str, hits: list[SearchHit]) -> str:
    if not hits:
        return "找不到可用內容；請先執行 `python data_update.py --rebuild` 建立索引。"

    lines = [
        "擷取式輸出：列出檢索片段，未使用生成模型；片段不等於已驗證的答案。",
        f"問題：{query}",
        "",
        "重點整理：",
    ]
    for hit in hits[:3]:
        excerpt = hit.text.replace("\n", " ").strip()
        if len(excerpt) > 220:
            excerpt = excerpt[:217] + "..."
        lines.append(f"- {excerpt} {hit.citation}")
    return "\n".join(lines)


def answer_query(
    query: str,
    settings: Settings,
    *,
    top_k: int = 5,
    model: str | None = None,
    history: list[dict[str, str]] | None = None,
) -> dict[str, object]:
    hits = retrieve_hits(query, settings, top_k=top_k)
    if not hits:
        return {
            "answer": "索引中沒有任何資料。請先執行 `python data_update.py --rebuild`。",
            "hits": [],
            "used_fallback": True,
        }

    if not llm_available(settings):
        return {"answer": fallback_answer(query, hits), "hits": hits, "used_fallback": True}

    try:
        response = proxy_chat_completion(
            settings=settings,
            model=model or settings.default_chat_model,
            messages=build_messages(query, hits, history=history),
        )
        return {
            "answer": response.choices[0].message.content,
            "hits": hits,
            "used_fallback": False,
        }
    except Exception as error:
        fallback = fallback_answer(query, hits)
        warning = (
            "Chat endpoint call failed; falling back to extractive mode.\n"
            f"LLM error type: {type(error).__name__}\n\n"
        )
        return {
            "answer": warning + fallback,
            "hits": hits,
            "used_fallback": True,
        }


def format_sources(hits: list[SearchHit]) -> str:
    lines = ["Sources:"]
    for hit in hits:
        lines.append(
            f"- {hit.citation} score={hit.score:.4f} chunk={hit.chunk_index} source={hit.title}"
        )
    return "\n".join(lines)


def build_skill_markdown_fallback(
    *,
    topic_name: str,
    answers: list[tuple[str, str]],
    sources: list[dict[str, str | int]],
) -> str:
    today = date.today().isoformat()
    source_count = len(sources)
    example_pairs = answers[:4]
    overview = answers[0][1] if answers else "This knowledge base focuses on emerging storage systems."
    methodology = answers[3][1] if len(answers) > 3 else "The corpus emphasizes cross-layer analysis."
    trends = answers[1][1] if len(answers) > 1 else "Device-aware design and cross-layer optimization remain central."
    limitations = answers[4][1] if len(answers) > 4 else "The corpus is limited by the current note set."

    source_lines = [
        f"- `{item['raw_path']}` | chunk_count={item['chunk_count']} | updated={item['updated_at']}"
        for item in sources
    ]
    qa_lines: list[str] = []
    for question, answer in example_pairs:
        qa_lines.append(f"### Q: {question}\n{answer}\n")

    return f"""# Skill: {topic_name}

## Metadata
- **知識領域**：Storage Systems / Device-aware System Design
- **資料來源數量**：{source_count} 份文件
- **最後更新時間**：{today}
- **適用 Agent 類型**：研究助手 / 技術顧問 / 論文導讀助手

## Overview
{overview}

## Core Concepts
- Device-aware system design：讓上層軟體理解介質限制與裝置背景任務。
- Write Amplification：衡量邏輯寫入與實體寫入差距的重要指標。
- Garbage Collection：影響 SSD 尾延遲與效能穩定度的背景任務。
- Zoned storage：把寫入規則顯式暴露給 host 軟體的一類裝置介面。
- NVM-aware design：利用新介質持久性與延遲特性的資料結構與一致性策略。
- LSM-tree trade-offs：以高寫入吞吐換取 compaction、讀放大與尾延遲成本。
- Cross-layer optimization：應用、資料結構、檔案系統與裝置韌體一起設計。

## Key Trends
{trends}

## Key Entities
- **Devices**：NAND Flash SSD, Zoned Storage, NVM, Magnetic Recording Variants
- **Software Layers**：File System, KV Store, LSM-tree, Block Layer, Page Cache
- **Evaluation Metrics**：Throughput, Average Latency, P99 Latency, Write Amplification, GC Overhead
- **Research Venues**：FAST, ATC, SOSP, OSDI, storage-related kernel documentation

## Methodology & Best Practices
{methodology}

## Knowledge Gaps & Limitations
{limitations}

## Example Q&A
{chr(10).join(qa_lines).strip()}

## Source References
{chr(10).join(source_lines)}
"""
