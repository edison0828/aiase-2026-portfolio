from __future__ import annotations

import hashlib
import re
from pathlib import Path

from storage_rag.models import ChunkRecord, ProcessedSource


SUPPORTED_EXTENSIONS = {".md", ".txt", ".pdf"}


def iter_raw_files(raw_dir: Path) -> list[Path]:
    return sorted(
        path
        for path in raw_dir.rglob("*")
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS
    )


def source_id_from_path(raw_path: Path, raw_dir: Path) -> str:
    relative = raw_path.relative_to(raw_dir)
    return relative.with_suffix("").as_posix()


def processed_path_from_raw(raw_path: Path, raw_dir: Path, processed_dir: Path) -> Path:
    relative = raw_path.relative_to(raw_dir).with_suffix(".txt")
    return processed_dir / relative


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def humanize_title(raw_path: Path) -> str:
    return raw_path.stem.replace("_", " ").replace("-", " ").strip().title()


def read_raw_text(raw_path: Path) -> str:
    suffix = raw_path.suffix.lower()
    if suffix == ".pdf":
        return read_pdf_text(raw_path)
    if suffix == ".md":
        return markdown_to_text(raw_path.read_text(encoding="utf-8"))
    if suffix == ".txt":
        return raw_path.read_text(encoding="utf-8")
    raise ValueError(f"Unsupported file type: {raw_path.suffix}")


def read_pdf_text(raw_path: Path) -> str:
    import fitz

    pages: list[str] = []
    with fitz.open(raw_path) as pdf:
        for page in pdf:
            pages.append(page.get_text("text"))
    return "\n\n".join(pages)


def markdown_to_text(markdown: str) -> str:
    text = re.sub(r"```.*?```", "\n", markdown, flags=re.DOTALL)
    text = re.sub(r"`([^`]*)`", r"\1", text)
    text = re.sub(r"!\[.*?\]\(.*?\)", "", text)
    text = re.sub(r"\[(.*?)\]\(.*?\)", r"\1", text)
    text = re.sub(r"^\s{0,3}#{1,6}\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*>\s?", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*[-*+]\s+", "- ", text, flags=re.MULTILINE)
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    text = re.sub(r"\*(.*?)\*", r"\1", text)
    return text


def clean_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    lines = [line.strip() for line in text.split("\n")]
    compact = "\n".join(lines)
    compact = re.sub(r"\n{3,}", "\n\n", compact)
    return compact.strip()


def split_paragraphs(text: str) -> list[str]:
    paragraphs = [part.strip() for part in text.split("\n\n")]
    return [paragraph for paragraph in paragraphs if paragraph]


def process_raw_file(raw_path: Path, raw_dir: Path, processed_dir: Path) -> ProcessedSource:
    raw_text = read_raw_text(raw_path)
    cleaned = clean_text(raw_text)
    processed_path = processed_path_from_raw(raw_path, raw_dir, processed_dir)
    processed_path.parent.mkdir(parents=True, exist_ok=True)
    processed_path.write_text(cleaned + "\n", encoding="utf-8")
    paragraphs = split_paragraphs(cleaned)
    return ProcessedSource(
        source_id=source_id_from_path(raw_path, raw_dir),
        title=humanize_title(raw_path),
        raw_path=raw_path.relative_to(raw_dir.parent).as_posix(),
        processed_path=processed_path.relative_to(processed_dir.parent).as_posix(),
        sha256=sha256_file(raw_path),
        text=cleaned,
        paragraph_count=len(paragraphs),
        metadata={
            "file_type": raw_path.suffix.lower().lstrip("."),
            "raw_filename": raw_path.name,
            "processed_filename": processed_path.name,
        },
    )


def chunk_source(
    source: ProcessedSource,
    *,
    max_chars: int = 1400,
    overlap_paragraphs: int = 1,
) -> list[ChunkRecord]:
    paragraphs = split_paragraphs(source.text)
    if not paragraphs:
        return []

    chunks: list[ChunkRecord] = []
    start = 0
    chunk_index = 0

    while start < len(paragraphs):
        current: list[str] = []
        current_len = 0
        end = start
        while end < len(paragraphs):
            candidate = paragraphs[end]
            projected = current_len + len(candidate) + (2 if current else 0)
            if current and projected > max_chars:
                break
            current.append(candidate)
            current_len = projected
            end += 1

        if not current:
            current = [paragraphs[start]]
            end = start + 1

        chunk_index += 1
        para_start = start + 1
        para_end = end
        chunk_text = "\n\n".join(current)
        chunks.append(
            ChunkRecord(
                chunk_id=f"{source.source_id}::chunk-{chunk_index:03d}",
                source_id=source.source_id,
                title=source.title,
                raw_path=source.raw_path,
                processed_path=source.processed_path,
                chunk_index=chunk_index,
                paragraph_start=para_start,
                paragraph_end=para_end,
                text=chunk_text,
                metadata={
                    **source.metadata,
                    "paragraph_count": source.paragraph_count,
                    "chunk_char_count": len(chunk_text),
                },
            )
        )

        if end >= len(paragraphs):
            break
        start = max(end - overlap_paragraphs, start + 1)

    return chunks
