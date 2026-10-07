from __future__ import annotations

import argparse
import shutil


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Process raw documents, chunk them, generate embeddings, and update the vector store."
    )
    parser.add_argument("--rebuild", action="store_true", help="Delete processed text and rebuild the full index.")
    parser.add_argument("--chunk-size", type=int, default=1400, help="Maximum characters per chunk.")
    parser.add_argument(
        "--chunk-overlap",
        type=int,
        default=1,
        help="Number of overlapping paragraphs between adjacent chunks.",
    )
    parser.add_argument("--verbose", action="store_true", help="Print per-file progress.")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    from storage_rag.config import load_settings
    from storage_rag.corpus import chunk_source, iter_raw_files, process_raw_file
    from storage_rag.embeddings import build_embedder
    from storage_rag.vector_store import SQLiteVectorStore

    settings = load_settings()
    store = SQLiteVectorStore(settings.vector_store_path)

    if args.rebuild:
        if settings.processed_dir.exists():
            shutil.rmtree(settings.processed_dir)
        settings.processed_dir.mkdir(parents=True, exist_ok=True)
        store.reset()

    raw_files = iter_raw_files(settings.raw_dir)
    if not raw_files:
        parser.error("No raw files found under data/raw/. Add .md, .txt, or .pdf files first.")

    manifest = store.get_manifest()
    current_source_ids: set[str] = set()
    changed_sources = []

    for raw_file in raw_files:
        source = process_raw_file(raw_file, settings.raw_dir, settings.processed_dir)
        current_source_ids.add(source.source_id)
        previous = manifest.get(source.source_id)
        changed = args.rebuild or previous is None or previous["sha256"] != source.sha256
        if changed:
            changed_sources.append(source)
        elif args.verbose:
            print(f"[skip] {source.raw_path}")

    removed_sources = sorted(set(manifest) - current_source_ids)
    for source_id in removed_sources:
        previous = manifest[source_id]
        processed_path = settings.raw_dir.parent / previous["processed_path"]
        if processed_path.exists():
            processed_path.unlink()
        store.delete_source(source_id)
        if args.verbose:
            print(f"[delete] {previous['raw_path']}")

    if not changed_sources and not removed_sources:
        print("Index already up to date. No files changed.")
        return 0

    embedder = build_embedder(settings.embedding_provider, settings.embedding_model)
    print(f"Embedding backend: {settings.embedding_provider} ({type(embedder).__name__})")
    total_chunks = 0

    for source in changed_sources:
        chunks = chunk_source(
            source,
            max_chars=args.chunk_size,
            overlap_paragraphs=args.chunk_overlap,
        )
        embeddings = embedder.embed_texts([chunk.text for chunk in chunks]) if chunks else []
        payloads = [
            chunk.to_store_payload(embedding)
            for chunk, embedding in zip(chunks, embeddings, strict=True)
        ]
        store.replace_source(
            source.source_id,
            source.raw_path,
            source.processed_path,
            source.sha256,
            payloads,
        )
        total_chunks += len(payloads)
        if args.verbose:
            print(f"[update] {source.raw_path} -> {len(payloads)} chunks")

    print(
        "Indexed "
        f"{len(changed_sources)} changed source(s), removed {len(removed_sources)} source(s), "
        f"and wrote {total_chunks} chunk(s) into {settings.vector_store_path.relative_to(settings.root_dir)}."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
