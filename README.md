# Obsidian Codex MCP

[![CI](https://github.com/aka-kika/obsidian-codex-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/aka-kika/obsidian-codex-mcp/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![MCP](https://img.shields.io/badge/MCP-Model%20Context%20Protocol-111827)](https://modelcontextprotocol.io/)
[![Obsidian](https://img.shields.io/badge/Obsidian-vaults-7C3AED?logo=obsidian&logoColor=white)](https://obsidian.md/)
[![Codex](https://img.shields.io/badge/Codex-ready-111827?logo=openai&logoColor=white)](https://openai.com/codex/)
[![Local first](https://img.shields.io/badge/local--first-markdown-10B981)](#safety-features)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

Local-first MCP server for working with an Obsidian vault.

- No Obsidian plugin required
- No API key required
- No cloud service required
- No Obsidian running in the background

This is for people who want MCP clients to work directly with markdown files on disk.

> Independent open-source project. Not affiliated with Obsidian, Anthropic, OpenAI, or any MCP client.

## What it does

It lets MCP clients work with your vault to:

- read and search notes
- create and update notes
- generate summaries, status reports, and release notes
- automate local knowledge workflows

All directly against your local markdown files.

## Best for

- Codex users who want safe local access to an Obsidian vault
- Claude Desktop, Cline, Cursor, and other MCP clients that can run a local Python server
- Developers who prefer filesystem-based Obsidian automation over the Local REST API plugin
- Personal knowledge bases, project logs, daily notes, task notes, and markdown-first workflows

## Why this exists

There are already a handful of Obsidian MCP servers. Many depend on the Obsidian Local REST API plugin or run as an Obsidian plugin. This project is intentionally simpler:

- direct filesystem access to a local vault
- no network calls
- no Obsidian API token
- Codex-friendly TOML configuration
- tolerant of real-world vaults with imperfect frontmatter
- path traversal protection so tools cannot escape the configured vault
- optional read-only mode for safer review/search workflows
- optional backup-on-write before updates and deletes

## How it compares

| Need | This project |
| --- | --- |
| Use Obsidian with Codex | Yes, with `~/.codex/config.toml` examples |
| Use Obsidian with Claude Desktop | Yes, with JSON config examples |
| Require an Obsidian plugin | No |
| Require an API key | No |
| Require Obsidian to be open | No |
| Read/write markdown files directly | Yes |
| Work over a remote HTTP API | No, local stdio MCP only |

## Safety features

Designed to be useful without being reckless:

- read-only mode, which refuses writes
- backup-on-write mode before updates and deletes
- vault path isolation
- path traversal protection
- no external network calls

## Tools

- `configure_vault` - set or change the vault path
- `get_note` - read one markdown note by vault-relative path
- `create_note` - create a new markdown note with optional metadata
- `update_note` - update note content and/or frontmatter
- `delete_note` - delete a markdown note
- `list_notes` - list notes in the vault or a folder
- `search_notes` - search note title, content, and tags
- `get_all_tags` - list unique tags from frontmatter and inline tags
- `get_backlinks` - find notes that link to a note
- `get_note_links` - extract wikilinks from a note
- `create_folder` - create a folder inside the vault
- `get_folder_structure` - return the vault folder tree

## Demo

Short launch clip:

[Obsidian + MCP + Codex demo](assets/obsidian-mcp-codex-demo.mp4)

Useful follow-up demos to record:

- AI edits a note in the vault, then Obsidian shows the result
- read-only and backup-on-write behavior

## Quick start

### Install

Requirements:

- Python 3.10 or newer recommended
- An Obsidian vault stored as local markdown files

```bash
git clone https://github.com/aka-kika/obsidian-codex-mcp.git
cd obsidian-codex-mcp
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
```

Verify against your vault:

```bash
OBSIDIAN_VAULT_PATH="/absolute/path/to/your/vault" .venv/bin/python test_server.py
```

## Codex configuration

Add this to `~/.codex/config.toml` and restart Codex:

```toml
[mcp_servers.obsidian]
command = "/absolute/path/to/obsidian-codex-mcp/.venv/bin/python"
args = ["/absolute/path/to/obsidian-codex-mcp/server.py"]
enabled = true

[mcp_servers.obsidian.env]
OBSIDIAN_VAULT_PATH = "/absolute/path/to/your/obsidian-vault"
OBSIDIAN_READ_ONLY = "false"
OBSIDIAN_BACKUP_ON_WRITE = "true"
```

For a safer read/search-only setup:

```toml
OBSIDIAN_READ_ONLY = "true"
```

## Claude Desktop configuration

Add this to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "obsidian": {
      "command": "/absolute/path/to/obsidian-codex-mcp/.venv/bin/python",
      "args": ["/absolute/path/to/obsidian-codex-mcp/server.py"],
      "env": {
        "OBSIDIAN_VAULT_PATH": "/absolute/path/to/your/obsidian-vault",
        "OBSIDIAN_READ_ONLY": "false",
        "OBSIDIAN_BACKUP_ON_WRITE": "true"
      }
    }
  }
}
```

## Environment

| Variable | Required | Default | Description |
| --- | --- | --- | --- |
| `OBSIDIAN_VAULT_PATH` | yes | none | Absolute path to the vault folder. |
| `OBSIDIAN_READ_ONLY` | no | `false` | When true, create/update/delete/folder creation tools refuse writes. |
| `OBSIDIAN_BACKUP_ON_WRITE` | no | `false` | When true, copies existing notes into `.obsidian-mcp-backups/` before update/delete. |

## Safety model

- All note paths are resolved relative to `OBSIDIAN_VAULT_PATH`.
- Absolute paths and `../` path traversal are rejected.
- Writes can be disabled with `OBSIDIAN_READ_ONLY=true`.
- Existing notes can be copied to `.obsidian-mcp-backups/` before update/delete with `OBSIDIAN_BACKUP_ON_WRITE=true`.
- Only markdown notes can be deleted.
- The server makes no external network calls.
- Broken YAML frontmatter does not break listing/search; the note is still readable with empty metadata.

## Development

Run the local test script:

```bash
OBSIDIAN_VAULT_PATH="/absolute/path/to/your/vault" .venv/bin/python test_server.py
```

Start the MCP server:

```bash
OBSIDIAN_VAULT_PATH="/absolute/path/to/your/vault" .venv/bin/python server.py
```

## Optional automation

Generate a daily project status report from your vault:

```bash
OBSIDIAN_VAULT_PATH="/absolute/path/to/your/vault" .venv/bin/python scripts/daily_status_report.py --folder "Projects"
```

Write the report back into Obsidian:

```bash
OBSIDIAN_VAULT_PATH="/absolute/path/to/your/vault" .venv/bin/python scripts/daily_status_report.py \
  --folder "Projects" \
  --write "Codex/Daily Project Status.md"
```

The script reports recent notes, markdown checkbox tasks, and top tags. It uses backup-on-write when updating an existing report note.

## Common workflows

See [docs/common-workflows.md](docs/common-workflows.md) for practical examples:

- safe vault exploration
- project catch-up
- daily status reports
- release notes after shipping
- vault triage
- index note creation
- finding underlinked notes
- safe editing checklist

## Templates

Copyable Obsidian note templates live in [docs/templates](docs/templates):

- [Codex work log](docs/templates/codex-work-log.md) for daily project status and workstream summaries
- [Project session log](docs/templates/project-session-log.md) for per-project session notes, decisions, links, and next moves
- [Weekly review](docs/templates/weekly-review.md) for accomplishments, open loops, and next-week priorities

## Optional skill

This repo includes lightweight agent workflow skills:

```text
skills/obsidian-vault-workflow/SKILL.md
skills/release-note-captain/SKILL.md
```

Use them as guidance for agents that work with this MCP server. They cover safe vault exploration, editing discipline, daily status reports, vault triage, project catch-up prompts, and release-note capture after a project ships.

## FAQ

### Is this an Obsidian MCP server?

Yes. It is a local MCP server for Obsidian vaults. It exposes tools for notes, tags, backlinks, wikilinks, folders, search, and optional writes.

### Does it work with Codex?

Yes. The main setup path is Codex-first and uses `~/.codex/config.toml`.

### Does it need the Obsidian Local REST API plugin?

No. It reads and writes markdown files directly from the vault folder.

### Does Obsidian need to be running?

No. Because this server works on local files, Obsidian does not need to be open.

### Can I make it read-only?

Yes. Set `OBSIDIAN_READ_ONLY=true` to allow search and inspection while refusing create, update, delete, and folder creation tools.

## Current limitations

- Search is simple substring search, not semantic or indexed search.
- No Obsidian command palette or plugin API access.
- No conflict resolution for simultaneous edits.
- No template expansion.
- No sync-provider awareness.

## License

MIT
