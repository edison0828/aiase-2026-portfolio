from __future__ import annotations

from models import Paper


def format_added(paper: Paper) -> str:

    return f"Added: [{paper.id}] {paper.title}"


def format_list(papers: list[Paper]) -> str:

    if not papers:
        return "No papers found."
    return "\n".join(format_paper_line(paper) for paper in papers)


def format_show(paper: Paper, note_count: int) -> str:

    lines = [
        f"id: {paper.id}",
        f"title: {paper.title}",
        f"authors: {'; '.join(paper.authors)}",
        f"year: {paper.year if paper.year is not None else '-'}",
        f"venue: {paper.venue or '-'}",
        f"status: {paper.status}",
        f"priority: {paper.priority}",
        f"tags: {','.join(paper.tags) if paper.tags else '-'}",
        f"url: {paper.url or '-'}",
        f"pdf_path: {paper.pdf_path or '-'}",
        f"notes: {note_count}",
    ]
    return "\n".join(lines)


def format_updated(paper: Paper) -> str:

    return f"Updated: [{paper.id}]"


def format_note_added(paper_id: int) -> str:

    return f"Added note: [{paper_id}]"


def format_next(paper: Paper | None) -> str:

    if paper is None:
        return "No candidate papers found."
    return f"Next: [{paper.id}] {paper.title}"


def format_deleted(paper: Paper) -> str:

    return f"Deleted: [{paper.id}] {paper.title}"


def format_stats(stats: dict[str, int]) -> str:

    lines = [
        f"total: {stats['total']}",
        f"unread: {stats['unread']}",
        f"reading: {stats['reading']}",
        f"read: {stats['read']}",
        f"notes: {stats['notes']}",
    ]
    return "\n".join(lines)


def format_paper_line(paper: Paper) -> str:

    year = paper.year if paper.year is not None else "-"
    return f"[{paper.id}] {paper.status} | p={paper.priority} | {year} | {paper.title}"

