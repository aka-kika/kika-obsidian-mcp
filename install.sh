#!/usr/bin/env bash
set -euo pipefail

# Multi-client installer for the Kika Obsidian MCP server.
# Sets up a local virtualenv, installs dependencies, verifies against your
# vault, then prints ready-to-paste config for the MCP client you choose.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

CLIENT="all"
VAULT_PATH=""
READ_ONLY="${OBSIDIAN_READ_ONLY:-false}"
BACKUP_ON_WRITE="${OBSIDIAN_BACKUP_ON_WRITE:-false}"

usage() {
  cat <<'USAGE'
Usage: ./install.sh [--client <name>] /absolute/path/to/your/obsidian-vault

  --client   claude | claude-desktop | codex | cursor | cline | grok | all
             (default: all — prints config for every supported client)

Environment (optional):
  OBSIDIAN_READ_ONLY=true         install in read-only mode
  OBSIDIAN_BACKUP_ON_WRITE=true   back up notes/bases before update/delete

Examples:
  ./install.sh --client claude ~/Vaults/Notes
  OBSIDIAN_READ_ONLY=true ./install.sh --client codex ~/Vaults/Notes
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --client) CLIENT="${2:-}"; shift 2 ;;
    --client=*) CLIENT="${1#*=}"; shift ;;
    -h|--help) usage; exit 0 ;;
    -*) echo "Unknown option: $1"; usage; exit 1 ;;
    *) VAULT_PATH="$1"; shift ;;
  esac
done

if [[ -z "$VAULT_PATH" ]]; then
  usage
  exit 1
fi

if [[ "$VAULT_PATH" != /* ]]; then
  echo "Vault path must be absolute: $VAULT_PATH"
  exit 1
fi

if [[ ! -d "$VAULT_PATH" ]]; then
  echo "Vault path does not exist: $VAULT_PATH"
  exit 1
fi

case "$CLIENT" in
  claude|claude-desktop|codex|cursor|cline|grok|all) ;;
  *) echo "Unknown client: $CLIENT"; usage; exit 1 ;;
esac

cd "$SCRIPT_DIR"

if [[ ! -d ".venv" ]]; then
  python3 -m venv .venv
fi

.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt

echo
echo "Verifying against your vault..."
OBSIDIAN_VAULT_PATH="$VAULT_PATH" .venv/bin/python test_server.py

PY="$SCRIPT_DIR/.venv/bin/python"
SRV="$SCRIPT_DIR/server.py"

print_claude() {
  cat <<EOF
--- Claude Code (CLI) -----------------------------------------------
Run this command:

  claude mcp add kika-obsidian \\
    --env OBSIDIAN_VAULT_PATH="$VAULT_PATH" \\
    --env OBSIDIAN_READ_ONLY="$READ_ONLY" \\
    --env OBSIDIAN_BACKUP_ON_WRITE="$BACKUP_ON_WRITE" \\
    -- "$PY" "$SRV"
EOF
}

print_claude_desktop() {
  cat <<EOF
--- Claude Desktop (claude_desktop_config.json) ---------------------
{
  "mcpServers": {
    "kika-obsidian": {
      "command": "$PY",
      "args": ["$SRV"],
      "env": {
        "OBSIDIAN_VAULT_PATH": "$VAULT_PATH",
        "OBSIDIAN_READ_ONLY": "$READ_ONLY",
        "OBSIDIAN_BACKUP_ON_WRITE": "$BACKUP_ON_WRITE"
      }
    }
  }
}
EOF
}

print_codex() {
  cat <<EOF
--- Codex (~/.codex/config.toml) ------------------------------------
[mcp_servers.kika-obsidian]
command = "$PY"
args = ["$SRV"]
enabled = true

[mcp_servers.kika-obsidian.env]
OBSIDIAN_VAULT_PATH = "$VAULT_PATH"
OBSIDIAN_READ_ONLY = "$READ_ONLY"
OBSIDIAN_BACKUP_ON_WRITE = "$BACKUP_ON_WRITE"
EOF
}

print_cursor_cline() {
  cat <<EOF
--- Cursor / Cline (mcpServers JSON) --------------------------------
{
  "mcpServers": {
    "kika-obsidian": {
      "command": "$PY",
      "args": ["$SRV"],
      "env": {
        "OBSIDIAN_VAULT_PATH": "$VAULT_PATH",
        "OBSIDIAN_READ_ONLY": "$READ_ONLY",
        "OBSIDIAN_BACKUP_ON_WRITE": "$BACKUP_ON_WRITE"
      }
    }
  }
}
EOF
}

print_grok() {
  cat <<EOF
--- Grok (~/.grok/config.toml) --------------------------------------
[mcp_servers.kika-obsidian]
command = "$PY"
args = ["$SRV"]
enabled = true

[mcp_servers.kika-obsidian.env]
OBSIDIAN_VAULT_PATH = "$VAULT_PATH"
OBSIDIAN_READ_ONLY = "$READ_ONLY"
OBSIDIAN_BACKUP_ON_WRITE = "$BACKUP_ON_WRITE"
EOF
}

echo
echo "===================================================================="
echo "Setup verified. Add the server to your MCP client's config:"
echo "===================================================================="
echo

case "$CLIENT" in
  claude) print_claude ;;
  claude-desktop) print_claude_desktop ;;
  codex) print_codex ;;
  cursor|cline) print_cursor_cline ;;
  grok) print_grok ;;
  all)
    print_claude; echo
    print_claude_desktop; echo
    print_codex; echo
    print_cursor_cline; echo
    print_grok
    ;;
esac

echo
echo "Then restart (or reconnect) your MCP client to load the server."
