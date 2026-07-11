# Kika Obsidian MCP

[![CI](https://github.com/aka-kika/kika-obsidian-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/aka-kika/kika-obsidian-mcp/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![MCP](https://img.shields.io/badge/MCP-Model%20Context%20Protocol-111827)](https://modelcontextprotocol.io/)
[![Obsidian](https://img.shields.io/badge/Obsidian-vaults-7C3AED?logo=obsidian&logoColor=white)](https://obsidian.md/)
[![Works with](https://img.shields.io/badge/works%20with-any%20MCP%20client-111827)](#configure-your-mcp-client)
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
- create and edit Obsidian Bases (`.base` files) with schema validation
- generate summaries, status reports, and release notes
- automate local knowledge workflows

All directly against your local markdown files.

## Best for

- Anyone using an MCP client — Claude Code, Claude Desktop, Cursor, Cline, Codex, Grok — who wants safe local access to an Obsidian vault
- Developers who prefer filesystem-based Obsidian automation over the Local REST API plugin
- People who want to create and edit Obsidian Bases (`.base`) from an agent
- Personal knowledge bases, project logs, daily notes, task notes, and markdown-first workflows

## Why this exists

There are already a handful of Obsidian MCP servers. Many depend on the Obsidian Local REST API plugin or run as an Obsidian plugin. This project is intentionally simpler:

- direct filesystem access to a local vault
- no network calls
- no Obsidian API token
- works with any MCP client — simple JSON or TOML config for Claude Code, Claude Desktop, Cursor, Cline, Codex, and Grok
- tolerant of real-world vaults with imperfect frontmatter
- path traversal protection so tools cannot escape the configured vault
- optional read-only mode for safer review/search workflows
- optional backup-on-write before updates and deletes
- **first-class Obsidian Bases (`.base`) support with schema validation** — a differentiator: almost no other Obsidian MCP server can create or edit Bases, and this one validates them against the official schema so it never writes a file Obsidian would silently reject

## How it compares

| Need | This project |
| --- | --- |
| Use Obsidian with any MCP client | Yes — Claude Code, Claude Desktop, Cursor, Cline, Codex, Grok |
| Config format | JSON or TOML, per client (examples for each) |
| Require an Obsidian plugin | No |
| Require an API key | No |
| Require Obsidian to be open | No |
| Read/write markdown files directly | Yes |
| Create and edit Obsidian Bases (`.base`) | Yes, with schema validation |
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

### Bases (`.base` files)

First-class, schema-validated support for [Obsidian Bases](https://help.obsidian.md/bases) — database-like views over your notes. Very few Obsidian MCP servers support these.

- `create_base` - create a `.base` file, validated against the Bases schema before writing
- `update_base` - merge changes into a base (update a view by name, add/remove views, change filters/formulas/properties)
- `get_base` - read a `.base` as parsed structure + raw YAML; tolerant of imperfect files
- `list_bases` - list `.base` files in the vault or a folder, with their view names
- `delete_base` - delete a `.base` file

All four Obsidian view modes are supported — **table**, **list**, **cards**, and **map** — and any of them can be mixed in a single base. Map views (from the [Maps community plugin](https://obsidian.md/plugins?id=maps)) round-trip cleanly too: their marker and zoom settings are preserved on read and re-write.

See [docs/bases-examples.md](docs/bases-examples.md) for copyable examples of each view mode.

## Demo

Short launch clip:

[Obsidian + MCP demo](assets/obsidian-mcp-codex-demo.mp4)

Useful follow-up demos to record:

- AI edits a note in the vault, then Obsidian shows the result
- read-only and backup-on-write behavior

## Quick start

### Install

Requirements:

- Python 3.10 or newer recommended
- An Obsidian vault stored as local markdown files

```bash
git clone https://github.com/aka-kika/kika-obsidian-mcp.git
cd kika-obsidian-mcp
./install.sh /absolute/path/to/your/obsidian-vault
```

`install.sh` creates a local virtualenv, installs dependencies, verifies against your vault, then prints ready-to-paste config for the client you choose (`--client claude|claude-desktop|codex|cursor|cline|grok`, default: all).

Prefer to do it by hand? The manual steps are:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
OBSIDIAN_VAULT_PATH="/absolute/path/to/your/vault" .venv/bin/python test_server.py
```

## Configure your MCP client

The server is a local stdio MCP server, so any MCP-capable client can run it. Point the client at your virtualenv's Python and `server.py`, and set the vault path via env. Then restart or reconnect the client.

### Claude Code

```bash
claude mcp add kika-obsidian \
  --env OBSIDIAN_VAULT_PATH="/absolute/path/to/your/obsidian-vault" \
  --env OBSIDIAN_READ_ONLY="false" \
  --env OBSIDIAN_BACKUP_ON_WRITE="true" \
  -- /absolute/path/to/kika-obsidian-mcp/.venv/bin/python \
     /absolute/path/to/kika-obsidian-mcp/server.py
```

### Claude Desktop / Cursor / Cline

Add this to the client's MCP config (`claude_desktop_config.json`, or the equivalent `mcpServers` block):

```json
{
  "mcpServers": {
    "kika-obsidian": {
      "command": "/absolute/path/to/kika-obsidian-mcp/.venv/bin/python",
      "args": ["/absolute/path/to/kika-obsidian-mcp/server.py"],
      "env": {
        "OBSIDIAN_VAULT_PATH": "/absolute/path/to/your/obsidian-vault",
        "OBSIDIAN_READ_ONLY": "false",
        "OBSIDIAN_BACKUP_ON_WRITE": "true"
      }
    }
  }
}
```

### Codex / Grok

Add this to `~/.codex/config.toml` (or `~/.grok/config.toml`):

```toml
[mcp_servers.kika-obsidian]
command = "/absolute/path/to/kika-obsidian-mcp/.venv/bin/python"
args = ["/absolute/path/to/kika-obsidian-mcp/server.py"]
enabled = true

[mcp_servers.kika-obsidian.env]
OBSIDIAN_VAULT_PATH = "/absolute/path/to/your/obsidian-vault"
OBSIDIAN_READ_ONLY = "false"
OBSIDIAN_BACKUP_ON_WRITE = "true"
```

For a safer read/search-only setup, set `OBSIDIAN_READ_ONLY="true"` (TOML: `OBSIDIAN_READ_ONLY = "true"`).

## Environment

| Variable | Required | Default | Description |
| --- | --- | --- | --- |
| `OBSIDIAN_VAULT_PATH` | yes | none | Absolute path to the vault folder. |
| `OBSIDIAN_READ_ONLY` | no | `false` | When true, create/update/delete/folder creation tools refuse writes. |
| `OBSIDIAN_BACKUP_ON_WRITE` | no | `false` | When true, copies existing notes into `.obsidian-mcp-backups/` before update/delete. |

## Safety model

- All note paths are resolved relative to `OBSIDIAN_VAULT_PATH`.
- Absolute paths and `../` path traversal are rejected.
- Writes can be disabled with `OBSIDIAN_READ_ONLY=true` (this also blocks `create_base`, `update_base`, and `delete_base`).
- Existing notes and `.base` files can be copied to `.obsidian-mcp-backups/` before update/delete with `OBSIDIAN_BACKUP_ON_WRITE=true`.
- Deletes are extension-scoped: `delete_note` only removes markdown (`.md`) notes and `delete_base` only removes Bases (`.base`) files. Neither can touch other file types.
- Base tools accept only `.base` paths and note tools only `.md` paths, so the two never cross-contaminate.
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
  --write "Reports/Daily Project Status.md"
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

- [Work log](docs/templates/work-log.md) for daily project status and workstream summaries
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

### Which MCP clients does it work with?

Any client that can run a local stdio MCP server — Claude Code, Claude Desktop, Cursor, Cline, Codex, and Grok are all covered with copy-paste config above. It is just a local Python process, so anything that speaks MCP over stdio can use it. Run `./install.sh --client <name> /path/to/vault` to print the exact config for your client.

### Does it support Obsidian Bases?

Yes, with dedicated schema-validated tools. `create_base`, `update_base`, `get_base`, `list_bases`, and `delete_base` let MCP clients build and edit `.base` files directly on disk. Every write is validated against the [official Bases schema](https://help.obsidian.md/bases/syntax) first, so it never writes a file Obsidian would silently reject, and errors name the exact offending path (for example, `views[0].groupBy missing 'property' key`). `get_base` is tolerant of imperfect files: if the YAML cannot be parsed it returns the raw content with a `parse_error` flag instead of failing. All four view modes — table, list, cards, and map — are supported, and map bases from the Maps community plugin round-trip without losing their marker/zoom settings. This is a differentiator — almost no other Obsidian MCP server can create or edit Bases. See [docs/bases-examples.md](docs/bases-examples.md).

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
