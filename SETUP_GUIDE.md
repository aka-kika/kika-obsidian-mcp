# Setup Guide

This server is a local stdio MCP server, so it works with any MCP client — Claude Code, Claude Desktop, Cursor, Cline, Codex, and Grok.

## Quick install

```bash
cd /path/to/kika-obsidian-mcp
./install.sh /absolute/path/to/your/obsidian-vault
```

`install.sh`:

- creates `.venv` if needed
- installs Python dependencies locally
- runs the local verification script against your vault
- prints ready-to-paste config for the client you choose

Pick a specific client to print just its config:

```bash
./install.sh --client claude /absolute/path/to/your/obsidian-vault
```

`--client` accepts `claude`, `claude-desktop`, `codex`, `cursor`, `cline`, `grok`, or `all` (default).

## Read-only mode

Use read-only mode when you want agents to search and inspect notes without changing them:

```bash
OBSIDIAN_READ_ONLY=true ./install.sh /absolute/path/to/your/obsidian-vault
```

Read-only mode disables:

- `create_note`
- `update_note`
- `delete_note`
- `create_folder`
- `create_base`
- `update_base`
- `delete_base`

## Backup-on-write mode

Use backup-on-write when you want a local copy before update/delete operations:

```bash
OBSIDIAN_BACKUP_ON_WRITE=true ./install.sh /absolute/path/to/your/obsidian-vault
```

Backups are written inside the vault under `.obsidian-mcp-backups/`.

## Manual config

The server takes the same command/args everywhere — your virtualenv's Python plus `server.py`, with the vault path in env. Then restart or reconnect the client.

### Claude Code

```bash
claude mcp add kika-obsidian \
  --env OBSIDIAN_VAULT_PATH="/absolute/path/to/your/obsidian-vault" \
  --env OBSIDIAN_READ_ONLY="false" \
  --env OBSIDIAN_BACKUP_ON_WRITE="false" \
  -- /path/to/kika-obsidian-mcp/.venv/bin/python \
     /path/to/kika-obsidian-mcp/server.py
```

### Claude Desktop / Cursor / Cline (JSON)

Use `claude_desktop_config.example.json` as a starting point, or add an `mcpServers` block:

```json
{
  "mcpServers": {
    "kika-obsidian": {
      "command": "/path/to/kika-obsidian-mcp/.venv/bin/python",
      "args": ["/path/to/kika-obsidian-mcp/server.py"],
      "env": {
        "OBSIDIAN_VAULT_PATH": "/absolute/path/to/your/obsidian-vault",
        "OBSIDIAN_READ_ONLY": "false",
        "OBSIDIAN_BACKUP_ON_WRITE": "false"
      }
    }
  }
}
```

### Codex / Grok (TOML)

Use `mcp.example.toml` as a starting point, or add this to `~/.codex/config.toml` (or `~/.grok/config.toml`):

```toml
[mcp_servers.kika-obsidian]
command = "/path/to/kika-obsidian-mcp/.venv/bin/python"
args = ["/path/to/kika-obsidian-mcp/server.py"]
enabled = true

[mcp_servers.kika-obsidian.env]
OBSIDIAN_VAULT_PATH = "/absolute/path/to/your/obsidian-vault"
OBSIDIAN_READ_ONLY = "false"
OBSIDIAN_BACKUP_ON_WRITE = "false"
```

## Verify

```bash
OBSIDIAN_VAULT_PATH="/absolute/path/to/your/obsidian-vault" .venv/bin/python test_server.py
```

Expected result:

```text
Results: 12/12 tests passed
```

## Optional daily status report

Preview a report:

```bash
OBSIDIAN_VAULT_PATH="/absolute/path/to/your/obsidian-vault" .venv/bin/python scripts/daily_status_report.py --folder "Projects"
```

Write a report note:

```bash
OBSIDIAN_VAULT_PATH="/absolute/path/to/your/obsidian-vault" .venv/bin/python scripts/daily_status_report.py \
  --folder "Projects" \
  --write "Reports/Daily Project Status.md"
```

## Optional agent skill

The repo ships with:

```text
skills/obsidian-vault-workflow/SKILL.md
```

Copy or reference that file in agent setups that support skills. It gives the agent a safe workflow for reading, searching, summarizing, and editing vault notes.

## Troubleshooting

### The MCP server does not appear

Restart or reconnect your MCP client after editing its MCP config.

### The test says the vault path does not exist

Use an absolute path and check it exists:

```bash
ls -la "/absolute/path/to/your/obsidian-vault"
```

### A note has broken frontmatter

The server tolerates broken YAML frontmatter for read/list/search/tag operations. Updating that note may rewrite frontmatter as normalized YAML.

### I want to publish this

Before release:

```bash
.venv/bin/python -m py_compile server.py obsidian_client.py bases.py test_server.py
OBSIDIAN_VAULT_PATH="/absolute/path/to/test-vault" .venv/bin/python test_server.py
```
