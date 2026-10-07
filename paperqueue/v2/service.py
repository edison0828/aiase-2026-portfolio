from __future__ import annotations

from datetime import datetime
from pathlib import Path

from models import (
    DEFAULT_PRIORITY,
    ExportError,
    Note,
    NoteNotFoundError,
    NotFoundError,
    Paper,
    ValidationError,
    VALID_STATUSES,
)
from storage import load_database, save_database


def add_paper(
    db_path: str,
    title: str,
    authors: str,
    year: int | None,
    venue: str | None,
    tags: str | None,
    url: str | None,
    pdf_path: str | None,
    priority: int,
) -> Paper:
    """Create a new paper and persist it to the database."""

    state = load_database(db_path)
    timestamp = current_timestamp()
    paper = Paper(
        id=state["next_paper_id"],
        title=require_text(title, "title"),
        authors=parse_authors(authors),
        year=year,
        venue=optional_text(venue),
        tags=parse_tags(tags),
        url=optional_text(url),
        pdf_path=optional_text(pdf_path),
        status="unread",
        priority=validate_priority(priority),
        created_at=timestamp,
        updated_at=timestamp,
    )
    state["papers"].append(paper)
    state["next_paper_id"] += 1
    save_database(db_path, state)
    return paper


def list_papers(
    db_path: str,
    status: str | None,
    tag: str | None,
    sort_key: str,
) -> list[Paper]:
    """Return papers filtered and sorted according to CLI options."""

    state = load_database(db_path)
    papers = filter_papers(state["papers"], status=status, tag=tag)

    sorters = {
        "id": lambda paper: (paper.id,),
        "year": lambda paper: (paper.year is None, -(paper.year or 0), paper.id),
        "priority": lambda paper: (-paper.priority, paper.id),
        "title": lambda paper: (paper.title.lower(), paper.id),
    }
    papers.sort(key=sorters[sort_key])
    return papers


def show_paper(db_path: str, paper_id: int) -> tuple[Paper, int]:
    """Return a paper and its note count."""

    state = load_database(db_path)
    paper = find_paper(state["papers"], paper_id)
    note_count = sum(1 for note in state["notes"] if note.paper_id == paper_id)
    return paper, note_count


def update_paper(
    db_path: str,
    paper_id: int,
    title: str | None,
    authors: str | None,
    year: int | None,
    venue: str | None,
    tags: str | None,
    url: str | None,
    pdf_path: str | None,
    status: str | None,
    priority: int | None,
) -> Paper:
    """Update fields on an existing paper."""

    if all(
        value is None
        for value in [title, authors, year, venue, tags, url, pdf_path, status, priority]
    ):
        raise ValidationError("Error: no fields to update")

    state = load_database(db_path)
    paper = find_paper(state["papers"], paper_id)

    if title is not None:
        paper.title = require_text(title, "title")
    if authors is not None:
        paper.authors = parse_authors(authors)
    if year is not None:
        paper.year = year
    if venue is not None:
        paper.venue = optional_text(venue)
    if tags is not None:
        paper.tags = parse_tags(tags)
    if url is not None:
        paper.url = optional_text(url)
    if pdf_path is not None:
        paper.pdf_path = optional_text(pdf_path)
    if status is not None:
        paper.status = validate_status(status)
    if priority is not None:
        paper.priority = validate_priority(priority)

    paper.updated_at = current_timestamp()
    save_database(db_path, state)
    return paper


def add_note(db_path: str, paper_id: int, text: str) -> Note:
    """Create a note for a paper."""

    state = load_database(db_path)
    paper = find_paper(state["papers"], paper_id)
    timestamp = current_timestamp()
    note = Note(
        id=state["next_note_id"],
        paper_id=paper_id,
        text=require_text(text, "note text"),
        created_at=timestamp,
    )
    paper.updated_at = timestamp
    state["notes"].append(note)
    state["next_note_id"] += 1
    save_database(db_path, state)
    return note


def list_notes(db_path: str, paper_id: int) -> tuple[Paper, list[Note]]:
    """Return a paper together with its notes in chronological order."""

    state = load_database(db_path)
    paper = find_paper(state["papers"], paper_id)
    notes = sorted(
        [note for note in state["notes"] if note.paper_id == paper_id],
        key=lambda note: (note.created_at, note.id),
    )
    return paper, notes


def delete_note(db_path: str, note_id: int) -> Note:
    """Delete a note by id and update the parent paper timestamp."""

    state = load_database(db_path)
    note = find_note(state["notes"], note_id)
    paper = find_paper(state["papers"], note.paper_id)
    state["notes"] = [item for item in state["notes"] if item.id != note_id]
    paper.updated_at = current_timestamp()
    save_database(db_path, state)
    return note


def get_next_paper(
    db_path: str,
    tag: str | None = None,
    year_min: int | None = None,
) -> Paper | None:
    """Select the next paper to read, optionally within a filtered subset."""

    state = load_database(db_path)
    candidates = [
        paper
        for paper in filter_papers(state["papers"], tag=tag)
        if paper.status in {"unread", "reading"}
    ]
    if year_min is not None:
        candidates = [
            paper for paper in candidates if paper.year is not None and paper.year >= year_min
        ]
    if not candidates:
        return None

    candidates.sort(
        key=lambda paper: (
            -paper.priority,
            0 if paper.status == "reading" else 1,
            paper.year is None,
            -(paper.year or 0),
            paper.id,
        )
    )
    return candidates[0]


def delete_paper(db_path: str, paper_id: int) -> Paper:
    """Delete a paper and all of its notes."""

    state = load_database(db_path)
    paper = find_paper(state["papers"], paper_id)
    state["papers"] = [item for item in state["papers"] if item.id != paper_id]
    state["notes"] = [note for note in state["notes"] if note.paper_id != paper_id]
    save_database(db_path, state)
    return paper


def get_stats(db_path: str) -> dict[str, int]:
    """Return aggregate counts for the current database state."""

    state = load_database(db_path)
    papers = state["papers"]
    notes = state["notes"]
    return {
        "total": len(papers),
        "unread": sum(1 for paper in papers if paper.status == "unread"),
        "reading": sum(1 for paper in papers if paper.status == "reading"),
        "read": sum(1 for paper in papers if paper.status == "read"),
        "notes": len(notes),
    }


def add_tags(db_path: str, paper_id: int, tags: str) -> Paper:
    """Append one or more tags without duplicating existing values."""

    state = load_database(db_path)
    paper = find_paper(state["papers"], paper_id)
    parsed_tags = parse_required_tags(tags)
    changed = False
    for tag in parsed_tags:
        if tag not in paper.tags:
            paper.tags.append(tag)
            changed = True
    if changed:
        paper.updated_at = current_timestamp()
        save_database(db_path, state)
    return paper


def remove_tags(db_path: str, paper_id: int, tags: str) -> tuple[Paper, list[str]]:
    """Remove one or more tags and report tags that were not present."""

    state = load_database(db_path)
    paper = find_paper(state["papers"], paper_id)
    parsed_tags = parse_required_tags(tags)
    existing = set(paper.tags)
    missing = [tag for tag in parsed_tags if tag not in existing]
    remaining = [tag for tag in paper.tags if tag not in set(parsed_tags)]
    if remaining != paper.tags:
        paper.tags = remaining
        paper.updated_at = current_timestamp()
        save_database(db_path, state)
    return paper, missing


def export_papers(
    db_path: str,
    status: str | None,
    tag: str | None,
) -> list[tuple[Paper, list[Note]]]:
    """Collect papers and their notes for export, using deterministic ordering."""

    state = load_database(db_path)
    papers = filter_papers(state["papers"], status=status, tag=tag)
    papers.sort(key=lambda paper: paper.id)

    notes_by_paper: dict[int, list[Note]] = {}
    for note in state["notes"]:
        notes_by_paper.setdefault(note.paper_id, []).append(note)

    exported: list[tuple[Paper, list[Note]]] = []
    for paper in papers:
        notes = sorted(notes_by_paper.get(paper.id, []), key=lambda note: (note.created_at, note.id))
        exported.append((paper, notes))
    return exported


def write_export_file(output_path: str, content: str, force: bool) -> None:
    """Write export content to disk, protecting existing files by default."""

    path = Path(output_path)
    if path.exists() and not force:
        raise ValidationError(f"Error: output file already exists: {output_path}")

    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    except OSError as exc:
        raise ExportError("Error: failed to write export file") from exc


def current_timestamp() -> str:
    """Return a stable ISO 8601 timestamp without microseconds."""

    return datetime.now().replace(microsecond=0).isoformat()


def find_paper(papers: list[Paper], paper_id: int) -> Paper:
    """Find a paper by id or raise a domain error."""

    for paper in papers:
        if paper.id == paper_id:
            return paper
    raise NotFoundError(paper_id)


def find_note(notes: list[Note], note_id: int) -> Note:
    """Find a note by id or raise a domain error."""

    for note in notes:
        if note.id == note_id:
            return note
    raise NoteNotFoundError(note_id)


def filter_papers(
    papers: list[Paper],
    status: str | None = None,
    tag: str | None = None,
) -> list[Paper]:
    """Filter papers by status and tag using the shared v1 semantics."""

    filtered = list(papers)
    if status is not None:
        wanted_status = validate_status(status)
        filtered = [paper for paper in filtered if paper.status == wanted_status]
    if tag is not None:
        wanted_tag = tag.strip()
        filtered = [paper for paper in filtered if wanted_tag in paper.tags]
    return filtered


def require_text(value: str, field_name: str) -> str:
    """Require a non-empty text field after trimming whitespace."""

    cleaned = value.strip()
    if not cleaned:
        raise ValidationError(f"Error: {field_name} must not be empty")
    return cleaned


def optional_text(value: str | None) -> str | None:
    """Normalize optional text values, converting blank strings to None."""

    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


def parse_authors(raw_authors: str) -> list[str]:
    """Parse and validate the semicolon-separated authors input."""

    authors = [part.strip() for part in raw_authors.split(";") if part.strip()]
    if not authors:
        raise ValidationError("Error: authors must not be empty")
    return authors


def parse_tags(raw_tags: str | None) -> list[str]:
    """Parse comma-separated tags, removing duplicates while preserving order."""

    if raw_tags is None:
        return []

    seen: set[str] = set()
    tags: list[str] = []
    for part in raw_tags.split(","):
        tag = part.strip()
        if tag and tag not in seen:
            seen.add(tag)
            tags.append(tag)
    return tags


def parse_required_tags(raw_tags: str) -> list[str]:
    """Parse a tag input that must contain at least one effective tag."""

    tags = parse_tags(raw_tags)
    if not tags:
        raise ValidationError("Error: tags must not be empty")
    return tags


def validate_status(status: str) -> str:
    """Validate and normalize a status value."""

    normalized = status.strip().lower()
    if normalized not in VALID_STATUSES:
        raise ValidationError(f"Error: invalid status: {status}")
    return normalized


def validate_priority(priority: int | None) -> int:
    """Validate and normalize a priority value."""

    value = DEFAULT_PRIORITY if priority is None else priority
    if value < 1 or value > 5:
        raise ValidationError(f"Error: invalid priority: {value}")
    return value
