#!/usr/bin/env python3
"""
Test script for Obsidian MCP server
Verifies the server can connect to the vault and basic operations work
"""

import os
import sys
import tempfile
from obsidian_client import ObsidianVaultClient

def test_vault_connection():
    """Test connection to the vault."""
    vault_path = os.getenv("OBSIDIAN_VAULT_PATH")
    
    if not vault_path:
        print("❌ ERROR: OBSIDIAN_VAULT_PATH environment variable not set")
        print("   Set it with: export OBSIDIAN_VAULT_PATH='/path/to/vault'")
        return False
    
    print(f"📂 Testing vault path: {vault_path}")
    
    if not os.path.exists(vault_path):
        print(f"❌ ERROR: Vault path does not exist: {vault_path}")
        return False
    
    try:
        client = ObsidianVaultClient(vault_path)
        print("✅ Successfully connected to vault")
        return True
    except Exception as e:
        print(f"❌ ERROR: Failed to connect to vault: {e}")
        return False

def test_list_notes():
    """Test listing notes."""
    try:
        vault_path = os.getenv("OBSIDIAN_VAULT_PATH")
        client = ObsidianVaultClient(vault_path)
        
        notes = client.list_notes()
        print(f"✅ Found {len(notes)} notes in vault")
        
        if notes:
            print("\n📄 First 5 notes:")
            for i, note in enumerate(notes[:5]):
                print(f"   {i+1}. {note['title']} ({note['path']})")
        
        return True
    except Exception as e:
        print(f"❌ ERROR: Failed to list notes: {e}")
        return False

def test_get_tags():
    """Test getting tags."""
    try:
        vault_path = os.getenv("OBSIDIAN_VAULT_PATH")
        client = ObsidianVaultClient(vault_path)
        
        tags = client.get_tags()
        print(f"✅ Found {len(tags)} unique tags")
        
        if tags:
            print("\n🏷️  First 10 tags:")
            for i, tag in enumerate(tags[:10]):
                print(f"   {i+1}. #{tag}")
        
        return True
    except Exception as e:
        print(f"❌ ERROR: Failed to get tags: {e}")
        return False

def test_folder_structure():
    """Test getting folder structure."""
    try:
        vault_path = os.getenv("OBSIDIAN_VAULT_PATH")
        client = ObsidianVaultClient(vault_path)
        
        structure = client.get_folder_structure()
        print("✅ Successfully retrieved folder structure")
        print(f"📁 Root: {structure['name']} ({len(structure.get('children', []))} top-level items)")
        
        return True
    except Exception as e:
        print(f"❌ ERROR: Failed to get folder structure: {e}")
        return False

def test_path_safety():
    """Test that vault-relative paths cannot escape the vault."""
    try:
        vault_path = os.getenv("OBSIDIAN_VAULT_PATH")
        client = ObsidianVaultClient(vault_path)

        try:
            client.get_note("../outside.md")
        except (RuntimeError, ValueError) as e:
            if "Path must stay inside" not in str(e):
                raise
        else:
            print("❌ ERROR: Path traversal was not rejected")
            return False

        print("✅ Path traversal is rejected")
        return True
    except Exception as e:
        print(f"❌ ERROR: Failed path safety test: {e}")
        return False

def test_write_operations():
    """Test creating, updating, and deleting a note in a temporary vault."""
    try:
        with tempfile.TemporaryDirectory() as temp_vault:
            client = ObsidianVaultClient(temp_vault, backup_on_write=True)
            note = client.create_note(
                "Sandbox/Test Note.md",
                "# Test Note\n\nHello from the MCP test.",
                {"tags": ["mcp-test"]},
            )
            if note["path"] != "Sandbox/Test Note.md":
                raise AssertionError("Created note path mismatch")

            updated = client.update_note("Sandbox/Test Note.md", metadata={"status": "ok"})
            if updated["metadata"].get("status") != "ok":
                raise AssertionError("Metadata update did not persist")

            if not client.delete_note("Sandbox/Test Note.md"):
                raise AssertionError("Delete returned false")

            backup_files = list(os.scandir(os.path.join(temp_vault, ".obsidian-mcp-backups")))
            if not backup_files:
                raise AssertionError("Backup folder was not created")

        print("✅ Write operations work in a temporary vault")
        return True
    except Exception as e:
        print(f"❌ ERROR: Failed write operation test: {e}")
        return False

def run_all_tests():
    """Run all tests."""
    print("🔍 Testing Obsidian MCP Server")
    print("=" * 40)
    
    tests = [
        ("Vault Connection", test_vault_connection),
        ("List Notes", test_list_notes),
        ("Get Tags", test_get_tags),
        ("Folder Structure", test_folder_structure),
        ("Path Safety", test_path_safety),
        ("Write Operations", test_write_operations),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n▶️  {test_name}:")
        print("-" * 40)
        if test_func():
            passed += 1
        else:
            print("\n💡 Tip: Make sure your vault path is correct and accessible")
    
    print("\n" + "=" * 40)
    print(f"📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The server is ready to use.")
        print("\n🔧 Next steps:")
        print("   For Codex: Run ./install_for_codex.sh <vault_path>")
        return 0
    else:
        print("❌ Some tests failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(run_all_tests())
