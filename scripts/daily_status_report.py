#!/usr/bin/env python3
"""Generate a lightweight daily project status report from an Obsidian vault."""

from __future__ import annotations

import argparse
import os
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
import sys

sys.path.insert(0, str(ROOT))

from obsidian_client import ObsidianVaultClient


TODO_PATTERN = re.compile(r'^\s*[-*]\s+\[( |x|X)\]\s+(.+)$', re.MULTILINE)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a daily Obsidian project status report.",
    )
    parser.add_argument(
        "--vault",
        default=os.getenv("OBSIDIAN_VAULT_PATH"),
        help="Absolute path to the Obsidian vault. Defaults to OBSIDIAN_VAULT_PATH.",
    )
    parser.add_argument(
        "--folder",
        default="",
        help="Optional vault-relative folder to summarize, for example 'Projects'.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Maximum number of recent notes and open tasks to include.",
    )
    parser.add_argument(
        "--write",
        metavar="PATH",
        help="Optional vault-relative note path to write the report to.",
    )
    return parser.parse_args()


def note_mtime(vault_path: Path, note: dict[str, Any]) -> float:
    return (vault_path / note["path"]).stat().st_mtime


def extract_tasks(notes: list[dict[str, Any]], limit: int) -> tuple[list[str], int, int]:
    open_tasks: list[str] = []
    complete_count = 0

    for note in notes:
        for done_marker, text in TODO_PATTERN.findall(note.get("content", "")):
            if done_marker.lower() == "x":
                complete_count += 1
            else:
                open_tasks.append(f"- [ ] {text.strip()} ({note['path']})")

    return open_tasks[:limit], len(open_tasks), complete_count


def build_report(client: ObsidianVaultClient, folder: str, limit: int) -> str:
    vault_path = client.vault_path
    notes = client.list_notes(folder or None)
    recent_notes = sorted(notes, key=lambda note: note_mtime(vault_path, note), reverse=True)[:limit]
    open_tasks, open_count, complete_count = extract_tasks(notes, limit)

    tag_counts = Counter(tag for note in notes for tag in note.get("tags", []))
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    scope = folder or "whole vault"

    lines = [
        f"# Daily Obsidian Status - {datetime.now().strftime('%Y-%m-%d')}",
        "",
        f"Generated: {generated_at}",
        f"Scope: {scope}",
        "",
        "## Snapshot",
        "",
        f"- Notes scanned: {len(notes)}",
        f"- Open tasks found: {open_count}",
        f"- Completed tasks found: {complete_count}",
        f"- Unique tags in scope: {len(tag_counts)}",
        "",
        "## Recently touched notes",
        "",
    ]

    if recent_notes:
        for note in recent_notes:
            modified = datetime.fromtimestamp(note_mtime(vault_path, note)).strftime("%Y-%m-%d %H:%M")
            lines.append(f"- {note['path']} - {modified}")
    else:
        lines.append("- No notes found.")

    lines.extend(["", "## Open tasks", ""])
    lines.extend(open_tasks or ["- No open markdown checkboxes found."])

    lines.extend(["", "## Top tags", ""])
    for tag, count in tag_counts.most_common(limit):
        lines.append(f"- #{tag} ({count})")
    if not tag_counts:
        lines.append("- No tags found.")

    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    if not args.vault:
        raise SystemExit("Set OBSIDIAN_VAULT_PATH or pass --vault.")

    client = ObsidianVaultClient(args.vault, backup_on_write=True)
    report = build_report(client, args.folder, args.limit)

    if args.write:
        existing_note = client.get_note(args.write)
        if existing_note:
            client.update_note(args.write, content=report, metadata={"generated": datetime.now(timezone.utc).isoformat()})
        else:
            client.create_note(args.write, report, {"generated": datetime.now(timezone.utc).isoformat(), "tags": ["obsidian-mcp", "status-report"]})
        print(f"Wrote report to {args.write}")
    else:
        print(report)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

