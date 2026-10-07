from __future__ import annotations

import argparse
import sys

from formatter import (
    format_added,
    format_deleted,
    format_list,
    format_next,
    format_note_added,
    format_show,
    format_stats,
    format_updated,
)
from models import PaperQueueError
from service import add_note, add_paper, delete_paper, get_next_paper, get_stats, list_papers, show_paper, update_paper


def build_parser() -> argparse.ArgumentParser:

    parser = argparse.ArgumentParser(prog="python v1/main.py", description="Manage a local paper reading queue.")
    parser.add_argument("--db", default="./paperqueue_data.json", help="Path to the JSON database file.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    add_parser = subparsers.add_parser("add", help="Add a new paper.")
    add_parser.add_argument("--title", required=True)
    add_parser.add_argument("--authors", required=True)
    add_parser.add_argument("--year", type=int)
    add_parser.add_argument("--venue")
    add_parser.add_argument("--tags")
    add_parser.add_argument("--url")
    add_parser.add_argument("--pdf-path")
    add_parser.add_argument("--priority", type=int, default=3)

    list_parser = subparsers.add_parser("list", help="List papers.")
    list_parser.add_argument("--status")
    list_parser.add_argument("--tag")
    list_parser.add_argument("--sort", choices=["id", "year", "priority", "title"], default="id")

    show_parser = subparsers.add_parser("show", help="Show paper details.")
    show_parser.add_argument("--id", type=int, required=True)

    update_parser = subparsers.add_parser("update", help="Update a paper.")
    update_parser.add_argument("--id", type=int, required=True)
    update_parser.add_argument("--title")
    update_parser.add_argument("--authors")
    update_parser.add_argument("--year", type=int)
    update_parser.add_argument("--venue")
    update_parser.add_argument("--tags")
    update_parser.add_argument("--url")
    update_parser.add_argument("--pdf-path")
    update_parser.add_argument("--status")
    update_parser.add_argument("--priority", type=int)

    note_parser = subparsers.add_parser("note", help="Add a note to a paper.")
    note_parser.add_argument("--id", type=int, required=True)
    note_parser.add_argument("--text", required=True)

    subparsers.add_parser("next", help="Show the next paper to read.")

    delete_parser = subparsers.add_parser("delete", help="Delete a paper.")
    delete_parser.add_argument("--id", type=int, required=True)

    subparsers.add_parser("stats", help="Show summary statistics.")
    return parser


def dispatch(args: argparse.Namespace) -> str:

    if args.command == "add":
        paper = add_paper(
            args.db,
            title=args.title,
            authors=args.authors,
            year=args.year,
            venue=args.venue,
            tags=args.tags,
            url=args.url,
            pdf_path=args.pdf_path,
            priority=args.priority,
        )
        return format_added(paper)

    if args.command == "list":
        papers = list_papers(args.db, status=args.status, tag=args.tag, sort_key=args.sort)
        return format_list(papers)

    if args.command == "show":
        paper, note_count = show_paper(args.db, args.id)
        return format_show(paper, note_count)

    if args.command == "update":
        paper = update_paper(
            args.db,
            paper_id=args.id,
            title=args.title,
            authors=args.authors,
            year=args.year,
            venue=args.venue,
            tags=args.tags,
            url=args.url,
            pdf_path=args.pdf_path,
            status=args.status,
            priority=args.priority,
        )
        return format_updated(paper)

    if args.command == "note":
        note = add_note(args.db, paper_id=args.id, text=args.text)
        return format_note_added(note.paper_id)

    if args.command == "next":
        paper = get_next_paper(args.db)
        return format_next(paper)

    if args.command == "delete":
        paper = delete_paper(args.db, args.id)
        return format_deleted(paper)

    if args.command == "stats":
        stats = get_stats(args.db)
        return format_stats(stats)

    raise RuntimeError(f"Unsupported command: {args.command}")


def main(argv: list[str] | None = None) -> int:

    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        output = dispatch(args)
    except PaperQueueError as exc:
        print(exc.message, file=sys.stderr)
        return exc.exit_code

    if output:
        print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

