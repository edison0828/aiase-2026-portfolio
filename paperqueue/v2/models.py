from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

VALID_STATUSES = ("unread", "reading", "read")
DEFAULT_PRIORITY = 3


class PaperQueueError(Exception):
    """Base application error with an attached exit code."""

    def __init__(self, message: str, exit_code: int) -> None:
        super().__init__(message)
        self.message = message
        self.exit_code = exit_code


class NotFoundError(PaperQueueError):
    """Raised when a paper id cannot be found."""

    def __init__(self, paper_id: int) -> None:
        super().__init__(f"Error: paper not found: {paper_id}", 1)


class NoteNotFoundError(PaperQueueError):
    """Raised when a note id cannot be found."""

    def __init__(self, note_id: int) -> None:
        super().__init__(f"Error: note not found: {note_id}", 1)


class ValidationError(PaperQueueError):
    """Raised when user input violates the CLI contract."""

    def __init__(self, message: str) -> None:
        super().__init__(message, 2)


class DatabaseError(PaperQueueError):
    """Raised when the JSON database cannot be read or written."""

    def __init__(self, message: str) -> None:
        super().__init__(message, 3)


class ExportError(PaperQueueError):
    """Raised when export output cannot be written."""

    def __init__(self, message: str) -> None:
        super().__init__(message, 3)


@dataclass
class Paper:
    """A paper record stored in the local database."""

    id: int
    title: str
    authors: list[str]
    year: int | None
    venue: str | None
    tags: list[str]
    url: str | None
    pdf_path: str | None
    status: str
    priority: int
    created_at: str
    updated_at: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Paper":
        return cls(
            id=int(data["id"]),
            title=str(data["title"]),
            authors=[str(item) for item in data["authors"]],
            year=int(data["year"]) if data.get("year") is not None else None,
            venue=str(data["venue"]) if data.get("venue") is not None else None,
            tags=[str(item) for item in data.get("tags", [])],
            url=str(data["url"]) if data.get("url") is not None else None,
            pdf_path=str(data["pdf_path"]) if data.get("pdf_path") is not None else None,
            status=str(data["status"]),
            priority=int(data["priority"]),
            created_at=str(data["created_at"]),
            updated_at=str(data["updated_at"]),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Note:
    """A note attached to a paper."""

    id: int
    paper_id: int
    text: str
    created_at: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Note":
        return cls(
            id=int(data["id"]),
            paper_id=int(data["paper_id"]),
            text=str(data["text"]),
            created_at=str(data["created_at"]),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
