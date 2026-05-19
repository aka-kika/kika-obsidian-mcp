# Obsidian Vault Workflow

Use this skill when a user asks an agent to inspect, organize, summarize, or update an Obsidian vault through this MCP server.

## Principles

- Treat the vault as the user's source of truth.
- Prefer read-only exploration before editing.
- Use vault-relative paths only.
- Never delete notes unless the user explicitly asks for deletion.
- For broad edits, make a short plan and name the affected folder or note set.
- When writing existing notes, recommend `OBSIDIAN_BACKUP_ON_WRITE=true`.
- Keep generated notes concise and link-friendly.

## Discovery Flow

1. Use `get_folder_structure` to understand the top-level vault layout.
2. Use `list_notes` for the relevant folder rather than scanning the whole vault when the user gives a scope.
3. Use `search_notes` for terms, tags, and project names.
4. Use `get_note` before modifying any existing note.
5. Use `get_note_links` and `get_backlinks` when the task depends on relationships between notes.

## Safe Editing Flow

1. Confirm the exact target path.
2. Read the current note with `get_note`.
3. Make the smallest useful update.
4. Preserve frontmatter unless the user asks to change it.
5. After writing, read the note again or summarize the changed path and content.

## Useful Prompts

### Daily Project Status

Ask the agent:

> Generate a daily status report for my `Projects` folder. Include recently touched notes, open checkbox tasks, completed checkbox count, and top tags. Preview it first.

If approved, write it to:

```text
Codex/Daily Project Status.md
```

### Vault Triage

Ask the agent:

> Review the top-level vault structure and suggest 5 cleanup actions. Do not edit anything yet.

### Project Catch-Up

Ask the agent:

> Search the vault for notes about `<project name>`, then summarize the current status, open tasks, and important linked notes.

## Output Style

- Use note paths in backticks.
- Separate findings from proposed edits.
- Keep status reports skimmable.
- Mention when no edit was made.

