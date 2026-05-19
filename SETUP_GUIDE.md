# Setup Guide

## Quick install for Codex

```bash
cd /path/to/obsidian-mcp
./install_for_codex.sh /absolute/path/to/your/obsidian-vault
```

Then restart Codex.

The installer:

- creates `.venv` if needed
- installs Python dependencies locally
- appends a Codex MCP config when no `obsidian` server is already present
- prints the config block when an `obsidian` server already exists
- runs the local verification script

## Read-only mode

Use read-only mode when you want agents to search and inspect notes without changing them:

```bash
OBSIDIAN_READ_ONLY=true ./install_for_codex.sh /absolute/path/to/your/obsidian-vault
```

Read-only mode disables:

- `create_note`
- `update_note`
- `delete_note`
- `create_folder`

## Backup-on-write mode

Use backup-on-write when you want a local copy before update/delete operations:

```bash
OBSIDIAN_BACKUP_ON_WRITE=true ./install_for_codex.sh /absolute/path/to/your/obsidian-vault
```

Backups are written inside the vault under `.obsidian-mcp-backups/`.

## Manual Codex config

Add this to `~/.codex/config.toml`:

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

## Manual Claude Desktop config

Use `claude_desktop_config.example.json` as a starting point and replace the placeholder paths.

## Verify

```bash
OBSIDIAN_VAULT_PATH="/absolute/path/to/your/obsidian-vault" .venv/bin/python test_server.py
```

Expected result:

```text
Results: 6/6 tests passed
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
  --write "Codex/Daily Project Status.md"
```

## Optional agent skill

The repo ships with:

```text
skills/obsidian-vault-workflow/SKILL.md
```

Copy or reference that file in agent setups that support skills. It gives the agent a safe workflow for reading, searching, summarizing, and editing vault notes.

## Troubleshooting

### The MCP server does not appear

Restart Codex or Claude Desktop after editing MCP config.

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
.venv/bin/python -m py_compile server.py obsidian_client.py test_server.py
OBSIDIAN_VAULT_PATH="/absolute/path/to/test-vault" .venv/bin/python test_server.py
```
