from __future__ import annotations

from models import Note, Paper


def format_added(paper: Paper) -> str:
    """Format the add command success message."""

    return f"Added: [{paper.id}] {paper.title}"


def format_list(papers: list[Paper]) -> str:
    """Format the list command output."""

    if not papers:
        return "No papers found."
    return "\n".join(format_paper_line(paper) for paper in papers)


def format_show(paper: Paper, note_count: int) -> str:
    """Format the show command output with a fixed field order."""

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
    """Format the update command success message."""

    return f"Updated: [{paper.id}]"


def format_note_added(paper_id: int) -> str:
    """Format the note add success message."""

    return f"Added note: [{paper_id}]"


def format_note_list(paper_id: int, notes: list[Note]) -> str:
    """Format the note list output."""

    if not notes:
        return f"No notes found for paper: {paper_id}"
    return "\n".join(f"[{note.id}] {note.created_at} | {note.text}" for note in notes)


def format_note_deleted(note_id: int) -> str:
    """Format the note delete success message."""

    return f"Deleted note: [{note_id}]"


def format_next(paper: Paper | None) -> str:
    """Format the next command output."""

    if paper is None:
        return "No candidate papers found."
    return f"Next: [{paper.id}] {paper.title}"


def format_deleted(paper: Paper) -> str:
    """Format the delete command success message."""

    return f"Deleted: [{paper.id}] {paper.title}"


def format_stats(stats: dict[str, int]) -> str:
    """Format the stats command output in the required order."""

    lines = [
        f"total: {stats['total']}",
        f"unread: {stats['unread']}",
        f"reading: {stats['reading']}",
        f"read: {stats['read']}",
        f"notes: {stats['notes']}",
    ]
    return "\n".join(lines)


def format_tag_result(paper: Paper, missing_tags: list[str] | None = None) -> str:
    """Format tag operation results, including any missing tags warning."""

    lines: list[str] = []
    if missing_tags:
        lines.append(f"Missing tags: {','.join(missing_tags)}")
    lines.append(f"Tags: {','.join(paper.tags) if paper.tags else '-'}")
    return "\n".join(lines)


def format_export(records: list[tuple[Paper, list[Note]]]) -> str:
    """Format exported papers as deterministic Markdown."""

    lines = ["# PaperQueue Export", ""]
    if not records:
        lines.append("(No papers found.)")
        return "\n".join(lines)

    for index, (paper, notes) in enumerate(records):
        lines.append(f"## [{paper.id}] {paper.title}")
        lines.append(f"- Authors: {'; '.join(paper.authors)}")
        lines.append(f"- Year: {paper.year if paper.year is not None else '-'}")
        lines.append(f"- Venue: {paper.venue or '-'}")
        lines.append(f"- Status: {paper.status}")
        lines.append(f"- Tags: {', '.join(paper.tags) if paper.tags else '-'}")
        lines.append(f"- URL: {paper.url or '-'}")
        lines.append("- Notes:")
        if notes:
            for note in notes:
                lines.append(f"  - [{note.id}] {note.created_at} | {note.text}")
        else:
            lines.append("  - (none)")
        if index != len(records) - 1:
            lines.append("")
    return "\n".join(lines)


def format_export_written(count: int, output_path: str) -> str:
    """Format the export-to-file success message."""

    return f"Exported: {count} papers to {output_path}"


def format_paper_line(paper: Paper) -> str:
    """Format a paper as a single line for list output."""

    year = paper.year if paper.year is not None else "-"
    return f"[{paper.id}] {paper.status} | p={paper.priority} | {year} | {paper.title}"
