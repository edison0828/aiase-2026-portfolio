from __future__ import annotations

import argparse
from pathlib import Path


GLOBAL_QUESTIONS = [
    "這個知識庫的核心研究主題與知識邊界是什麼？",
    "目前新興儲存裝置系統研究最重要的趨勢有哪些？",
    "這個領域常見的效能瓶頸、評估指標與系統 trade-off 是什麼？",
    "設計 device-aware 或 flash-aware 系統時，常見的方法論與最佳實踐有哪些？",
    "目前這份知識庫還有哪些明顯缺口或後續應補的論文子題？",
]


def strip_markdown_fence(text: str) -> str:
    stripped = text.strip()
    if not stripped.startswith("```"):
        return stripped

    lines = stripped.splitlines()
    if lines and lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]
    return "\n".join(lines).strip()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate skill.md from the indexed storage-systems knowledge base."
    )
    parser.add_argument("--output", default="artifacts/generated_skill.md", help="Where to write the generated skill markdown.")
    parser.add_argument("--top-k", type=int, default=6, help="How many chunks to retrieve per synthesis question.")
    parser.add_argument("--model", default=None, help="Override the configured chat model.")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    from storage_rag.config import load_settings
    from storage_rag.pipeline import (
        answer_query,
        build_skill_markdown_fallback,
        llm_available,
        proxy_chat_completion,
    )
    from storage_rag.vector_store import SQLiteVectorStore

    settings = load_settings()
    store = SQLiteVectorStore(settings.vector_store_path)
    sources = store.source_summaries()
    if not sources:
        parser.error("The vector store is empty. Run `python data_update.py --rebuild` first.")

    answers: list[tuple[str, str]] = []
    for question in GLOBAL_QUESTIONS:
        result = answer_query(question, settings, top_k=args.top_k, model=args.model)
        answers.append((question, str(result["answer"])))

    markdown = None
    if llm_available(settings):
        try:
            qa_block = "\n\n".join(
                f"Question: {question}\nAnswer: {answer}" for question, answer in answers
            )
            source_block = "\n".join(
                f"- {item['raw_path']} | chunk_count={item['chunk_count']} | updated={item['updated_at']}"
                for item in sources
            )
            response = proxy_chat_completion(
                settings=settings,
                model=args.model or settings.default_chat_model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Generate a Skill markdown document for an agent. "
                            "Use the exact section titles Metadata, Overview, Core Concepts, "
                            "Key Trends, Key Entities, Methodology & Best Practices, "
                            "Knowledge Gaps & Limitations, Example Q&A, and Source References."
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            "Topic: Cross-Layer System Support for Emerging Storage Devices\n\n"
                            f"Question/Answer synthesis:\n{qa_block}\n\n"
                            f"Sources:\n{source_block}\n"
                        ),
                    },
                ],
            )
            markdown = strip_markdown_fence(response.choices[0].message.content)
        except Exception:
            markdown = None

    if markdown is None:
        markdown = build_skill_markdown_fallback(
            topic_name="Cross-Layer System Support for Emerging Storage Devices",
            answers=answers,
            sources=sources,
        )

    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = settings.root_dir / output_path
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(markdown.strip() + "\n", encoding="utf-8")

    print(f"Wrote skill markdown to {output_path.relative_to(settings.root_dir)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
