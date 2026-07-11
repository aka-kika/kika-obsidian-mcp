#!/usr/bin/env python3
"""
Test script for Obsidian MCP server
Verifies the server can connect to the vault and basic operations work
"""

import os
import sys
import tempfile
from obsidian_client import ObsidianVaultClient
from bases import validate_base_schema

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

def _valid_base_data():
    """A representative, schema-valid base used across the Bases tests."""
    return {
        "filters": {"and": ['file.hasTag("task")']},
        "formulas": {
            "days_until_due": 'if(due, (date(due) - today()).days, "")',
        },
        "properties": {"status": {"displayName": "Status"}},
        "views": [
            {
                "type": "table",
                "name": "Active",
                "order": ["file.name", "status", "formula.days_until_due"],
            }
        ],
    }


def test_create_valid_base():
    """Create a valid base -> file exists, parses, and round-trips."""
    try:
        with tempfile.TemporaryDirectory() as temp_vault:
            client = ObsidianVaultClient(temp_vault)
            data = _valid_base_data()

            base = client.create_base("Bases/Tasks.base", data)
            if base["path"] != "Bases/Tasks.base":
                raise AssertionError("Created base path mismatch")
            if base["parse_error"] is not None:
                raise AssertionError(f"Unexpected parse error: {base['parse_error']}")
            if base["views"] != ["Active"]:
                raise AssertionError(f"View names mismatch: {base['views']}")

            base_file = os.path.join(temp_vault, "Bases", "Tasks.base")
            if not os.path.exists(base_file):
                raise AssertionError("Base file was not written")

            reread = client.get_base("Bases/Tasks.base")
            if reread["data"]["views"][0]["name"] != "Active":
                raise AssertionError("Round-trip lost the view name")
            if reread["data"]["formulas"]["days_until_due"] != data["formulas"]["days_until_due"]:
                raise AssertionError("Round-trip lost the formula expression")

        print("✅ Valid base creates, parses, and round-trips")
        return True
    except Exception as e:
        print(f"❌ ERROR: Failed create-valid-base test: {e}")
        return False


def test_create_invalid_base_rejected():
    """Invalid schema -> rejected with a clear error and no file written."""
    try:
        with tempfile.TemporaryDirectory() as temp_vault:
            client = ObsidianVaultClient(temp_vault)

            # View missing required 'type'.
            try:
                client.create_base("Bad.base", {"views": [{"name": "NoType"}]})
            except ValueError as e:
                if "type" not in str(e):
                    raise AssertionError(f"Error message not helpful: {e}")
            else:
                raise AssertionError("Base with a typeless view was not rejected")

            if os.path.exists(os.path.join(temp_vault, "Bad.base")):
                raise AssertionError("Rejected base still wrote a file")

            # Unknown top-level key.
            try:
                client.create_base("Bogus.base", {"views": [{"type": "table"}], "bogus": 1})
            except ValueError:
                pass
            else:
                raise AssertionError("Base with an unknown top-level key was not rejected")

            # groupBy missing property -> path-named, teaching error.
            errors = validate_base_schema(
                {"views": [{"type": "table", "groupBy": {"direction": "ASC"}}]}
            )
            if not any("views[0].groupBy missing 'property'" in msg for msg in errors):
                raise AssertionError(f"Expected a groupBy property error, got: {errors}")

        print("✅ Invalid base schema is rejected without writing a file")
        return True
    except Exception as e:
        print(f"❌ ERROR: Failed invalid-base test: {e}")
        return False


def test_update_view_by_name():
    """Update one view by name -> other views untouched, backup created."""
    try:
        with tempfile.TemporaryDirectory() as temp_vault:
            client = ObsidianVaultClient(temp_vault, backup_on_write=True)
            client.create_base(
                "Board.base",
                {
                    "views": [
                        {"type": "table", "name": "A", "order": ["file.name"]},
                        {"type": "table", "name": "B", "order": ["file.name"]},
                    ]
                },
            )

            updated = client.update_base(
                "Board.base",
                upsert_views=[{"type": "cards", "name": "B", "order": ["file.name", "cover"]}],
            )

            views = {v["name"]: v for v in updated["data"]["views"]}
            if views["A"]["type"] != "table" or views["A"]["order"] != ["file.name"]:
                raise AssertionError("View A was modified but should be untouched")
            if views["B"]["type"] != "cards":
                raise AssertionError("View B was not replaced")
            if views["B"]["order"] != ["file.name", "cover"]:
                raise AssertionError("View B order not updated")

            backup_root = os.path.join(temp_vault, ".obsidian-mcp-backups")
            if not os.path.isdir(backup_root) or not list(os.scandir(backup_root)):
                raise AssertionError("Backup was not created on update")

        print("✅ Update replaces a view by name, leaves others intact, backs up")
        return True
    except Exception as e:
        print(f"❌ ERROR: Failed update-view test: {e}")
        return False


def test_base_read_only():
    """Read-only mode -> create/update/delete_base all refuse."""
    try:
        try:
            import server
        except ImportError as e:
            print(f"⏭️  SKIP read-only base test (mcp not importable: {e})")
            return True

        saved = {
            "ro": os.environ.get("OBSIDIAN_READ_ONLY"),
            "vp": os.environ.get("OBSIDIAN_VAULT_PATH"),
        }
        with tempfile.TemporaryDirectory() as temp_vault:
            os.environ["OBSIDIAN_READ_ONLY"] = "true"
            os.environ["OBSIDIAN_VAULT_PATH"] = temp_vault
            server._vault_client = None
            server._vault_path = None
            try:
                results = [
                    server.create_base("R/One.base", [{"type": "table", "name": "V"}]),
                    server.update_base("R/One.base", remove_views=["V"]),
                    server.delete_base("R/One.base"),
                ]
                for result in results:
                    if not isinstance(result, dict) or result.get("success") is not False:
                        raise AssertionError(f"Write was not refused: {result}")
                    if "read-only" not in result.get("error", "").lower():
                        raise AssertionError(f"Unexpected refusal message: {result}")

                if os.path.exists(os.path.join(temp_vault, "R", "One.base")):
                    raise AssertionError("Read-only create still wrote a file")
            finally:
                server._vault_client = None
                server._vault_path = None
                for key, env in (("OBSIDIAN_READ_ONLY", saved["ro"]), ("OBSIDIAN_VAULT_PATH", saved["vp"])):
                    if env is None:
                        os.environ.pop(key, None)
                    else:
                        os.environ[key] = env

        print("✅ Read-only mode refuses create/update/delete_base")
        return True
    except Exception as e:
        print(f"❌ ERROR: Failed read-only base test: {e}")
        return False


def test_base_path_traversal():
    """Path traversal and absolute paths are rejected; extension is enforced."""
    try:
        with tempfile.TemporaryDirectory() as temp_vault:
            client = ObsidianVaultClient(temp_vault)
            data = _valid_base_data()

            for bad_path in ("../outside.base", "/tmp/evil.base"):
                try:
                    client.create_base(bad_path, data)
                except ValueError:
                    pass
                else:
                    raise AssertionError(f"Path was not rejected: {bad_path}")

            # Reading outside the vault must also be rejected (not silently None).
            try:
                client.get_base("../outside.base")
            except ValueError:
                pass
            else:
                raise AssertionError("get_base did not reject a traversal path")

            # Non-.base extension is rejected.
            try:
                client.create_base("Notes/note.md", data)
            except ValueError as e:
                if ".base" not in str(e):
                    raise AssertionError(f"Extension error not helpful: {e}")
            else:
                raise AssertionError("A non-.base path was accepted")

        print("✅ Base path traversal and extension rules are enforced")
        return True
    except Exception as e:
        print(f"❌ ERROR: Failed base path-safety test: {e}")
        return False


def test_get_corrupted_base():
    """get_base on a corrupted file returns raw + error flag, no crash."""
    try:
        with tempfile.TemporaryDirectory() as temp_vault:
            client = ObsidianVaultClient(temp_vault)
            broken = os.path.join(temp_vault, "Broken.base")
            raw = 'views:\n  - type: table\n    name: "Unterminated\n'
            with open(broken, "w", encoding="utf-8") as fh:
                fh.write(raw)

            base = client.get_base("Broken.base")
            if base is None:
                raise AssertionError("get_base returned None for an existing file")
            if base.get("parse_error") is None:
                raise AssertionError("Corrupted base did not set parse_error")
            if base.get("data") is not None:
                raise AssertionError("Corrupted base should have data=None")
            if base.get("raw") != raw:
                raise AssertionError("Raw content was not returned verbatim")
            if base.get("views") != []:
                raise AssertionError("Corrupted base should report no views")

        print("✅ Corrupted base returns raw + parse_error without crashing")
        return True
    except Exception as e:
        print(f"❌ ERROR: Failed corrupted-base test: {e}")
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
        ("Bases: Create Valid", test_create_valid_base),
        ("Bases: Reject Invalid", test_create_invalid_base_rejected),
        ("Bases: Update View By Name", test_update_view_by_name),
        ("Bases: Read-Only Refuses", test_base_read_only),
        ("Bases: Path Safety", test_base_path_traversal),
        ("Bases: Corrupted File", test_get_corrupted_base),
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
