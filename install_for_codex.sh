#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VAULT_PATH="${1:-}"
READ_ONLY="${OBSIDIAN_READ_ONLY:-false}"
BACKUP_ON_WRITE="${OBSIDIAN_BACKUP_ON_WRITE:-false}"
CONFIG_FILE="$HOME/.codex/config.toml"

if [[ -z "$VAULT_PATH" ]]; then
  echo "Usage: ./install_for_codex.sh /absolute/path/to/your/obsidian-vault"
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

cd "$SCRIPT_DIR"

if [[ ! -d ".venv" ]]; then
  python3 -m venv .venv
fi

.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt

mkdir -p "$(dirname "$CONFIG_FILE")"
touch "$CONFIG_FILE"

if grep -q '^\[mcp_servers\.obsidian\]' "$CONFIG_FILE"; then
  echo "Codex already has an [mcp_servers.kika-obsidian] entry:"
  echo "$CONFIG_FILE"
  echo
  echo "Update it to:"
  cat <<EOF
[mcp_servers.kika-obsidian]
command = "$SCRIPT_DIR/.venv/bin/python"
args = ["$SCRIPT_DIR/server.py"]
enabled = true

[mcp_servers.kika-obsidian.env]
OBSIDIAN_VAULT_PATH = "$VAULT_PATH"
OBSIDIAN_READ_ONLY = "$READ_ONLY"
OBSIDIAN_BACKUP_ON_WRITE = "$BACKUP_ON_WRITE"
EOF
else
  cat >> "$CONFIG_FILE" <<EOF

[mcp_servers.kika-obsidian]
command = "$SCRIPT_DIR/.venv/bin/python"
args = ["$SCRIPT_DIR/server.py"]
enabled = true

[mcp_servers.kika-obsidian.env]
OBSIDIAN_VAULT_PATH = "$VAULT_PATH"
OBSIDIAN_READ_ONLY = "$READ_ONLY"
OBSIDIAN_BACKUP_ON_WRITE = "$BACKUP_ON_WRITE"
EOF
fi

OBSIDIAN_VAULT_PATH="$VAULT_PATH" .venv/bin/python test_server.py

echo
echo "Installed Obsidian MCP for Codex."
echo "Restart Codex to load the server."
