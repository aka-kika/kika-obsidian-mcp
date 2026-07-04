import re
import shutil
import yaml
from yaml.parser import ParserError
from yaml.scanner import ScannerError
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
import frontmatter

# Matches [[target]] and [[target|alias]]; group 1 = target, group 2 = alias (may be None)
WIKILINK_RE = re.compile(r'\[\[([^\]|]+)(?:\|([^\]]*))?\]\]')


class ObsidianVaultClient:
    """Client for interacting with Obsidian vault files."""
    
    def __init__(self, vault_path: str, backup_on_write: bool = False):
        self.vault_path = Path(vault_path).expanduser().resolve()
        self.backup_on_write = backup_on_write
        self._ensure_vault_exists()
    
    def _ensure_vault_exists(self):
        """Ensure the vault directory exists."""
        if not self.vault_path.exists():
            raise ValueError(f"Vault path does not exist: {self.vault_path}")
        if not self.vault_path.is_dir():
            raise ValueError(f"Vault path is not a directory: {self.vault_path}")

    def _resolve_vault_path(self, path: str) -> Path:
        """Resolve a vault-relative path and reject paths outside the vault."""
        if not path or not str(path).strip():
            raise ValueError("Path is required")

        relative_path = Path(str(path).strip()).expanduser()
        if relative_path.is_absolute():
            raise ValueError("Use a path relative to the vault root, not an absolute path")

        resolved_path = (self.vault_path / relative_path).resolve()
        try:
            resolved_path.relative_to(self.vault_path)
        except ValueError as exc:
            raise ValueError("Path must stay inside the configured vault") from exc

        return resolved_path

    def _load_markdown(self, note_path: Path) -> tuple[str, Dict[str, Any]]:
        """Load markdown and tolerate broken YAML frontmatter."""
        raw_content = note_path.read_text(encoding='utf-8')

        try:
            # frontmatter.parse instead of .loads: .loads splats metadata into
            # Post(**kwargs) and crashes on notes with a 'content:'/'handler:' key
            metadata, content = frontmatter.parse(raw_content)
            return content, dict(metadata)
        except (ParserError, ScannerError, yaml.YAMLError):
            return raw_content, {}

    @staticmethod
    def _dump_markdown(content: str, metadata: Dict[str, Any]) -> str:
        """Serialize a note, omitting the frontmatter block when metadata is empty."""
        if not metadata:
            return content
        post = frontmatter.Post(content)
        post.metadata = dict(metadata)
        return frontmatter.dumps(post)

    @staticmethod
    def _normalize_tags(value: Any) -> List[str]:
        """Normalize frontmatter or inline tag values to simple tag names."""
        if value is None:
            return []

        if isinstance(value, str):
            values = [value]
        elif isinstance(value, list):
            values = value
        else:
            values = [value]

        normalized = []
        for item in values:
            if item is None:
                continue
            tag = str(item).strip()
            if not tag:
                continue
            normalized.append(tag.lstrip('#'))

        return normalized

    @staticmethod
    def _extract_inline_tags(content: str) -> List[str]:
        """Extract inline #tags from markdown content, ignoring simple punctuation."""
        matches = re.findall(r'(?<!\w)#([A-Za-z0-9_/-]+)', content)
        return [tag for tag in matches if tag]

    def _backup_note(self, note_path: Path) -> Optional[Path]:
        """Copy an existing note into the backup folder when backup mode is enabled."""
        if not self.backup_on_write or not note_path.exists() or not note_path.is_file():
            return None

        relative_path = note_path.relative_to(self.vault_path)
        timestamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
        backup_path = self.vault_path / '.obsidian-mcp-backups' / timestamp / relative_path
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(note_path, backup_path)
        return backup_path
    
    def get_note(self, path: str) -> Optional[Dict[str, Any]]:
        """Get a note by path."""
        note_path = self._resolve_vault_path(path)
        if not note_path.exists() or not note_path.suffix.lower() == '.md':
            return None
        
        try:
            content, metadata = self._load_markdown(note_path)
            tags = sorted(set(self._normalize_tags(metadata.get('tags')) + self._extract_inline_tags(content)))
            
            return {
                'path': str(note_path.relative_to(self.vault_path)),
                'content': content,
                'metadata': metadata,
                'title': metadata.get('title', note_path.stem),
                'tags': tags,
                'created': metadata.get('created'),
                'modified': metadata.get('modified')
            }
        except Exception as e:
            raise RuntimeError(f"Error reading note {path}: {str(e)}") from e
    
    def create_note(self, path: str, content: str, metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """Create a new note."""
        note_path = self._resolve_vault_path(path)
        if note_path.suffix.lower() != '.md':
            raise ValueError("Note path must end with .md")
        
        if note_path.exists():
            raise ValueError(f"Note already exists: {path}")
        
        note_path.parent.mkdir(parents=True, exist_ok=True)

        note_path.write_text(self._dump_markdown(content, metadata or {}), encoding='utf-8')

        return self.get_note(path)
    
    def update_note(self, path: str, content: Optional[str] = None, metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """Update an existing note."""
        note_path = self._resolve_vault_path(path)
        
        if not note_path.exists():
            raise ValueError(f"Note does not exist: {path}")
        
        current_content, current_metadata = self._load_markdown(note_path)

        if content is not None:
            current_content = content

        if metadata is not None:
            current_metadata.update(metadata)

        self._backup_note(note_path)
        note_path.write_text(self._dump_markdown(current_content, current_metadata), encoding='utf-8')

        return self.get_note(path)
    
    def delete_note(self, path: str) -> bool:
        """Delete a note."""
        note_path = self._resolve_vault_path(path)
        
        if not note_path.exists():
            return False
        if note_path.suffix.lower() != '.md':
            raise ValueError("Only markdown notes can be deleted")
        
        self._backup_note(note_path)
        note_path.unlink()
        return True
    
    def list_notes(self, folder: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all notes in the vault or specific folder."""
        search_path = self._resolve_vault_path(folder) if folder else self.vault_path
        
        if not search_path.exists():
            return []
        if not search_path.is_dir():
            raise ValueError(f"Folder is not a directory: {folder}")
        
        notes = []
        for md_file in search_path.rglob("*.md"):
            rel_path = md_file.relative_to(self.vault_path)
            # Skip hidden folders (.obsidian, .trash, .obsidian-mcp-backups, ...)
            if any(part.startswith('.') for part in rel_path.parts):
                continue
            note = self.get_note(str(rel_path))
            if note:
                notes.append(note)

        return notes
    
    def search_notes(self, query: str, folder: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search notes by content or title."""
        notes = self.list_notes(folder)
        results = []
        
        query_lower = query.lower()
        for note in notes:
            if (query_lower in note['title'].lower() or 
                query_lower in note['content'].lower() or
                query_lower in ' '.join(str(tag) for tag in note.get('tags', [])).lower()):
                results.append(note)
        
        return results
    
    def get_tags(self) -> List[str]:
        """Get all unique tags in the vault."""
        notes = self.list_notes()
        tags = set()
        
        for note in notes:
            tags.update(note.get('tags', []))
        
        return sorted(list(tags))
    
    def get_backlinks(self, path: str) -> List[Dict[str, Any]]:
        """Find all notes that link to the specified note."""
        target_name = Path(path).stem
        target_no_ext = str(Path(path).with_suffix(''))
        all_notes = self.list_notes()
        backlinks = []

        for note in all_notes:
            if note['path'] == path:
                continue

            content = note['content']

            for target, alias in WIKILINK_RE.findall(content):
                link_target = target.split('#')[0].strip()  # Remove header references
                if link_target in (target_name, target_no_ext, path):
                    backlinks.append({
                        'note': note,
                        'link_text': alias if alias else target
                    })
                    break

        return backlinks
    
    def get_note_links(self, path: str) -> List[str]:
        """Extract all wikilink targets from a note."""
        note = self.get_note(path)
        if not note:
            return []
        
        content = note['content']

        links = []
        for target, _alias in WIKILINK_RE.findall(content):
            link_target = target.split('#')[0].strip()  # Remove header references
            if link_target:
                links.append(link_target)

        return links
    
    def create_folder(self, folder_path: str) -> bool:
        """Create a new folder in the vault."""
        folder = self._resolve_vault_path(folder_path)
        
        if folder.exists():
            return False
        
        folder.mkdir(parents=True, exist_ok=True)
        return True
    
    def get_folder_structure(self) -> Dict[str, Any]:
        """Get the complete folder structure of the vault."""
        structure = {'name': self.vault_path.name, 'type': 'folder', 'children': []}
        
        def build_structure(current_path: Path, current_node: Dict):
            for item in sorted(current_path.iterdir()):
                if item.name.startswith('.'):
                    continue
                
                if item.is_file() and item.suffix.lower() == '.md':
                    current_node['children'].append({
                        'name': item.name,
                        'type': 'note',
                        'path': str(item.relative_to(self.vault_path))
                    })
                elif item.is_dir():
                    folder_node = {
                        'name': item.name,
                        'type': 'folder',
                        'path': str(item.relative_to(self.vault_path)),
                        'children': []
                    }
                    current_node['children'].append(folder_node)
                    build_structure(item, folder_node)
        
        build_structure(self.vault_path, structure)
        return structure
