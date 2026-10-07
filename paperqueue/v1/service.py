from __future__ import annotations

from datetime import datetime

from models import DEFAULT_PRIORITY, Note, NotFoundError, Paper, ValidationError, VALID_STATUSES
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

    state = load_database(db_path)
    papers = list(state["papers"])

    if status is not None:
        wanted_status = validate_status(status)
        papers = [paper for paper in papers if paper.status == wanted_status]

    if tag is not None:
        wanted_tag = tag.strip()
        papers = [paper for paper in papers if wanted_tag in paper.tags]

    sorters = {
        "id": lambda paper: (paper.id,),
        "year": lambda paper: (paper.year is None, -(paper.year or 0), paper.id),
        "priority": lambda paper: (-paper.priority, paper.id),
        "title": lambda paper: (paper.title.lower(), paper.id),
    }
    papers.sort(key=sorters[sort_key])
    return papers


def show_paper(db_path: str, paper_id: int) -> tuple[Paper, int]:

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

    state = load_database(db_path)
    paper = find_paper(state["papers"], paper_id)
    note = Note(
        id=state["next_note_id"],
        paper_id=paper_id,
        text=require_text(text, "note text"),
        created_at=current_timestamp(),
    )
    paper.updated_at = current_timestamp()
    state["notes"].append(note)
    state["next_note_id"] += 1
    save_database(db_path, state)
    return note


def get_next_paper(db_path: str) -> Paper | None:

    state = load_database(db_path)
    candidates = [paper for paper in state["papers"] if paper.status in {"unread", "reading"}]
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

    state = load_database(db_path)
    paper = find_paper(state["papers"], paper_id)
    state["papers"] = [item for item in state["papers"] if item.id != paper_id]
    state["notes"] = [note for note in state["notes"] if note.paper_id != paper_id]
    save_database(db_path, state)
    return paper


def get_stats(db_path: str) -> dict[str, int]:

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


def current_timestamp() -> str:

    return datetime.now().replace(microsecond=0).isoformat()


def find_paper(papers: list[Paper], paper_id: int) -> Paper:

    for paper in papers:
        if paper.id == paper_id:
            return paper
    raise NotFoundError(paper_id)


def require_text(value: str, field_name: str) -> str:

    cleaned = value.strip()
    if not cleaned:
        raise ValidationError(f"Error: {field_name} must not be empty")
    return cleaned


def optional_text(value: str | None) -> str | None:

    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


def parse_authors(raw_authors: str) -> list[str]:

    authors = [part.strip() for part in raw_authors.split(";") if part.strip()]
    if not authors:
        raise ValidationError("Error: authors must not be empty")
    return authors


def parse_tags(raw_tags: str | None) -> list[str]:

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


def validate_status(status: str) -> str:

    normalized = status.strip().lower()
    if normalized not in VALID_STATUSES:
        raise ValidationError(f"Error: invalid status: {status}")
    return normalized


def validate_priority(priority: int | None) -> int:

    value = DEFAULT_PRIORITY if priority is None else priority
    if value < 1 or value > 5:
        raise ValidationError(f"Error: invalid priority: {value}")
    return value

