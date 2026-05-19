# Obsidian MCP for Codex

A local-first Model Context Protocol server for Obsidian vaults.

This server gives MCP clients such as Codex, Claude Desktop, Cline, and other agent tools structured access to markdown notes on disk. It does not require an Obsidian plugin, an API key, or a running Obsidian app. Point it at a vault folder and it reads/writes markdown files directly.

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

## Install

Requirements:

- Python 3.10 or newer recommended
- An Obsidian vault stored as local markdown files

```bash
git clone https://github.com/dot-RealityTest/obsidian-codex-mcp.git
cd obsidian-mcp
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
command = "/absolute/path/to/obsidian-mcp/.venv/bin/python"
args = ["/absolute/path/to/obsidian-mcp/server.py"]
enabled = true

[mcp_servers.obsidian.env]
OBSIDIAN_VAULT_PATH = "/absolute/path/to/your/obsidian-vault"
OBSIDIAN_READ_ONLY = "false"
OBSIDIAN_BACKUP_ON_WRITE = "false"
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
      "command": "/absolute/path/to/obsidian-mcp/.venv/bin/python",
      "args": ["/absolute/path/to/obsidian-mcp/server.py"],
      "env": {
        "OBSIDIAN_VAULT_PATH": "/absolute/path/to/your/obsidian-vault",
        "OBSIDIAN_READ_ONLY": "false",
        "OBSIDIAN_BACKUP_ON_WRITE": "false"
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

## Optional skill

This repo includes a lightweight agent workflow skill:

```text
skills/obsidian-vault-workflow/SKILL.md
```

Use it as guidance for agents that work with this MCP server. It covers safe vault exploration, editing discipline, daily status reports, vault triage, and project catch-up prompts.

## Current limitations

- Search is simple substring search, not semantic or indexed search.
- No Obsidian command palette or plugin API access.
- No conflict resolution for simultaneous edits.
- No template expansion.
- No sync-provider awareness.

## License

MIT
