from __future__ import annotations

import argparse


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Query the local storage-systems RAG knowledge base."
    )
    parser.add_argument("--query", help="Run a single query instead of interactive mode.")
    parser.add_argument("--top-k", type=int, default=5, help="How many chunks to retrieve.")
    parser.add_argument(
        "--model",
        default=None,
        help="Override the configured OpenAI-compatible chat model.",
    )
    parser.add_argument(
        "--history-turns",
        type=int,
        default=3,
        help="How many conversational turns to keep in interactive mode.",
    )
    return parser


def run_single_query(query: str, top_k: int, model: str | None) -> int:
    from storage_rag.config import load_settings
    from storage_rag.pipeline import answer_query, format_sources

    settings = load_settings()
    print(f"Embedding backend: {settings.embedding_provider}")
    result = answer_query(query, settings, top_k=top_k, model=model)
    print(result["answer"])
    print()
    print(format_sources(result["hits"]))
    return 0


def run_interactive(top_k: int, model: str | None, history_turns: int) -> int:
    from storage_rag.config import load_settings
    from storage_rag.pipeline import answer_query, format_sources

    settings = load_settings()
    print(f"Embedding backend: {settings.embedding_provider}")
    history: list[dict[str, str]] = []

    print("Interactive RAG mode. Type `exit` or `quit` to stop.")
    while True:
        query = input("\nQuestion> ").strip()
        if not query:
            continue
        if query.lower() in {"exit", "quit"}:
            return 0

        result = answer_query(
            query,
            settings,
            top_k=top_k,
            model=model,
            history=history,
        )
        print()
        print(result["answer"])
        print()
        print(format_sources(result["hits"]))

        history.append({"role": "user", "content": query})
        history.append({"role": "assistant", "content": str(result["answer"])})
        max_messages = max(history_turns, 1) * 2
        history = history[-max_messages:]


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.query:
        return run_single_query(args.query, args.top_k, args.model)
    return run_interactive(args.top_k, args.model, args.history_turns)


if __name__ == "__main__":
    raise SystemExit(main())
