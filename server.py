#!/usr/bin/env python3
"""
Obsidian MCP Server
Enables LLMs to interact with Obsidian vaults.
"""

import os
import logging
from typing import Optional
from mcp.server.fastmcp import FastMCP
from obsidian_client import ObsidianVaultClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("obsidian")

# Global vault client (initialized when needed)
_vault_client = None
_vault_path = None


def is_read_only() -> bool:
    """Return true when mutating tools should refuse writes."""
    value = os.getenv("OBSIDIAN_READ_ONLY", "").strip().lower()
    return value in {"1", "true", "yes", "on"}


def backup_on_write_enabled() -> bool:
    """Return true when existing notes should be backed up before writes."""
    value = os.getenv("OBSIDIAN_BACKUP_ON_WRITE", "").strip().lower()
    return value in {"1", "true", "yes", "on"}


def read_only_error() -> dict:
    """Shared response for disabled write operations."""
    return {
        "success": False,
        "error": "This server is running in read-only mode. Set OBSIDIAN_READ_ONLY=false to allow writes.",
    }


def get_vault_client() -> ObsidianVaultClient:
    """Get or create the vault client."""
    global _vault_client, _vault_path
    
    if _vault_client is None:
        if _vault_path is None:
            # Try to get from environment variable
            _vault_path = os.getenv("OBSIDIAN_VAULT_PATH")
            if not _vault_path:
                raise ValueError("Obsidian vault path not configured. Set OBSIDIAN_VAULT_PATH environment variable.")
        
        _vault_client = ObsidianVaultClient(_vault_path, backup_on_write=backup_on_write_enabled())
        logger.info(f"Connected to vault: {_vault_path}")
    
    return _vault_client


@mcp.tool()
def configure_vault(vault_path: str) -> dict:
    """Configure the Obsidian vault path.
    
    Args:
        vault_path: Absolute path to your Obsidian vault
    """
    global _vault_client, _vault_path
    
    _vault_path = vault_path
    _vault_client = None  # Reset client
    
    try:
        client = get_vault_client()
        return {
            "success": True,
            "message": f"Vault configured successfully: {vault_path}",
            "note_count": len(client.list_notes())
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@mcp.tool()
def get_note(path: str) -> dict:
    """Get a note by its path.
    
    Args:
        path: Path to the note relative to vault root (e.g., "notes/my-note.md")
    """
    try:
        client = get_vault_client()
        note = client.get_note(path)
        
        if note is None:
            return {"error": f"Note not found: {path}"}
        
        return note
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def create_note(path: str, content: str, title: Optional[str] = None, tags: Optional[list] = None) -> dict:
    """Create a new note.
    
    Args:
        path: Path for the new note (e.g., "notes/new-note.md")
        content: Note content in Markdown
        title: Optional title (defaults to filename)
        tags: Optional list of tags
    """
    try:
        if is_read_only():
            return read_only_error()

        client = get_vault_client()
        
        metadata = {}
        if title:
            metadata['title'] = title
        if tags:
            metadata['tags'] = tags
        
        note = client.create_note(path, content, metadata)
        return note
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def update_note(path: str, content: Optional[str] = None, metadata: Optional[dict] = None) -> dict:
    """Update an existing note.
    
    Args:
        path: Path to the note
        content: New content (optional)
        metadata: Metadata updates (optional)
    """
    try:
        if is_read_only():
            return read_only_error()

        client = get_vault_client()
        note = client.update_note(path, content, metadata)
        return note
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def delete_note(path: str) -> dict:
    """Delete a note permanently.
    
    Args:
        path: Path to the note to delete
    """
    try:
        if is_read_only():
            return read_only_error()

        client = get_vault_client()
        success = client.delete_note(path)
        
        if success:
            return {"success": True, "message": f"Note deleted: {path}"}
        else:
            return {"error": f"Note not found: {path}"}
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def list_notes(folder: Optional[str] = None) -> list:
    """List all notes in the vault or a specific folder.
    
    Args:
        folder: Optional folder path (e.g., "notes/" or "projects/")
    """
    try:
        client = get_vault_client()
        notes = client.list_notes(folder)
        
        # Return simplified version for list
        return [
            {
                "path": note['path'],
                "title": note['title'],
                "tags": note.get('tags', [])
            }
            for note in notes
        ]
    except Exception as e:
        return [{"error": str(e)}]


@mcp.tool()
def search_notes(query: str, folder: Optional[str] = None) -> list:
    """Search notes by content, title, or tags.
    
    Args:
        query: Search query string
        folder: Optional folder to search within
    """
    try:
        client = get_vault_client()
        results = client.search_notes(query, folder)
        
        return [
            {
                "path": note['path'],
                "title": note['title'],
                "excerpt": note['content'][:200] + "..." if len(note['content']) > 200 else note['content']
            }
            for note in results
        ]
    except Exception as e:
        return [{"error": str(e)}]


@mcp.tool()
def get_all_tags() -> list:
    """Get all unique tags used in the vault."""
    try:
        client = get_vault_client()
        return client.get_tags()
    except Exception as e:
        return [{"error": str(e)}]


@mcp.tool()
def get_backlinks(path: str) -> list:
    """Find all notes that link to the specified note.
    
    Args:
        path: Path to the target note
    """
    try:
        client = get_vault_client()
        backlinks = client.get_backlinks(path)
        
        return [
            {
                "note_path": link['note']['path'],
                "note_title": link['note']['title'],
                "link_text": link['link_text']
            }
            for link in backlinks
        ]
    except Exception as e:
        return [{"error": str(e)}]


@mcp.tool()
def get_note_links(path: str) -> list:
    """Get all wikilinks from a note.
    
    Args:
        path: Path to the note
    """
    try:
        client = get_vault_client()
        return client.get_note_links(path)
    except Exception as e:
        return [{"error": str(e)}]


@mcp.tool()
def create_folder(folder_path: str) -> dict:
    """Create a new folder in the vault.
    
    Args:
        folder_path: Path to the new folder (e.g., "projects/new-project/")
    """
    try:
        if is_read_only():
            return read_only_error()

        client = get_vault_client()
        success = client.create_folder(folder_path)
        
        if success:
            return {"success": True, "message": f"Folder created: {folder_path}"}
        else:
            return {"error": f"Folder already exists: {folder_path}"}
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def get_folder_structure() -> dict:
    """Get the complete folder structure of the vault."""
    try:
        client = get_vault_client()
        return client.get_folder_structure()
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    # For local testing
    mcp.run()
