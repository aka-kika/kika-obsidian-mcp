# Common Workflows

Practical ways to use Obsidian Codex MCP with Codex, Claude Desktop, Cline, Cursor, and other local MCP clients.

## 1. Explore a Vault Safely

Use this when connecting a vault for the first time.

Recommended setup:

```toml
OBSIDIAN_READ_ONLY = "true"
```

Agent prompt:

```text
Show me the top-level structure of my Obsidian vault. Do not edit anything.
Then suggest the 5 most useful folders to inspect next.
```

Useful tools:

- `get_folder_structure`
- `list_notes`
- `search_notes`
- `get_note`

## 2. Project Catch-Up

Use this when returning to a project after a break.

Agent prompt:

```text
Search my Obsidian vault for notes about PROJECT_NAME.
Summarize the current status, open tasks, important links, and next likely actions.
Do not edit anything.
```

Useful tools:

- `search_notes`
- `get_note`
- `get_note_links`
- `get_backlinks`

Suggested output:

- Project status
- Recent or important notes
- Open questions
- Next actions
- Related notes

## 3. Daily Project Status Report

Use the included automation script to summarize a folder.

Preview only:

```bash
OBSIDIAN_VAULT_PATH="/absolute/path/to/your/vault" \
  .venv/bin/python scripts/daily_status_report.py \
  --folder "Projects" \
  --limit 10
```

Write the report into Obsidian:

```bash
OBSIDIAN_VAULT_PATH="/absolute/path/to/your/vault" \
  .venv/bin/python scripts/daily_status_report.py \
  --folder "Projects" \
  --write "Codex/Daily Project Status.md"
```

The report includes:

- recently touched notes
- open markdown checkbox tasks
- completed checkbox count
- top tags

## 4. Release Notes After Shipping

Use this after publishing a website, pushing a public repo, shipping a macOS app, or deploying a web app.

Agent prompt:

```text
Create or update a release note for PROJECT_NAME.
Include the repo URL, live URL, what shipped, verification, SEO/GEO notes, and follow-ups.
Save it under Codex/Release Notes/.
```

Suggested note path:

```text
Codex/Release Notes/YYYY-MM-DD — Project Name.md
```

Use the bundled skill:

```text
skills/release-note-captain/SKILL.md
```

## 5. Vault Triage

Use this when a vault starts feeling cluttered.

Agent prompt:

```text
Review my vault structure and suggest cleanup actions.
Do not move, delete, or edit notes yet.
Group suggestions by low-risk, medium-risk, and needs-confirmation.
```

Recommended setup:

```toml
OBSIDIAN_READ_ONLY = "true"
```

Suggested output:

- likely duplicate folders
- stale indexes
- notes missing tags
- folders that need an `_index.md`
- safe cleanup plan

## 6. Create or Update an Index Note

Use this to make a folder easier to navigate.

Agent prompt:

```text
Create an _index.md note for FOLDER_NAME.
List key notes, explain what belongs here, and include next actions.
Read existing notes first. Do not delete anything.
```

Recommended settings:

```toml
OBSIDIAN_BACKUP_ON_WRITE = "true"
```

Useful tools:

- `list_notes`
- `get_note`
- `create_note`
- `update_note`

## 7. Find Orphaned or Underlinked Notes

Use this to improve knowledge graph quality.

Agent prompt:

```text
Look through FOLDER_NAME and identify notes with few or no backlinks.
Suggest links they should have, but do not edit anything yet.
```

Useful tools:

- `list_notes`
- `get_backlinks`
- `get_note_links`
- `search_notes`

## 8. Safe Editing Checklist

Before editing an existing note:

1. Confirm the vault-relative path.
2. Read the note with `get_note`.
3. Make the smallest useful change.
4. Preserve frontmatter unless asked to change it.
5. Use `OBSIDIAN_BACKUP_ON_WRITE=true` for important notes.
6. Read or summarize the final note after writing.

Avoid:

- deleting notes unless explicitly asked
- using absolute paths
- broad rewrites without a plan
- editing generated/imported archives unless the user confirms

