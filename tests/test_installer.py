import json
import tempfile
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from lbrain_agents.installer import (  # noqa: E402
    merge_json_mcp,
    merge_toml_mcp,
    _toml_remove_table,
    _toml_has_table,
)
from lbrain_agents.mcp_entry import main as mcp_main  # noqa: E402
from lbrain_agents import IDENTITY_LINE  # noqa: E402


class JsonMergeTests(unittest.TestCase):
    def test_adds_lbrain_without_touching_other_servers(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "mcp.json"
            path.write_text(
                json.dumps({"mcpServers": {"reddit": {"command": "uvx"}}}),
                encoding="utf-8",
            )
            spec = {"type": "stdio", "command": "/usr/bin/lbrain", "args": ["mcp"], "env": {}}
            action = merge_json_mcp(path, spec, dry_run=False, force=False, harness="cursor")
            self.assertTrue(action.changed)
            data = json.loads(path.read_text(encoding="utf-8"))
            self.assertIn("reddit", data["mcpServers"])
            self.assertEqual(data["mcpServers"]["lbrain"]["command"], "/usr/bin/lbrain")

    def test_idempotent_without_force(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "mcp.json"
            path.write_text(
                json.dumps(
                    {
                        "mcpServers": {
                            "lbrain": {"command": "/old/lbrain", "args": ["mcp"]}
                        }
                    }
                ),
                encoding="utf-8",
            )
            spec = {"command": "/new/lbrain", "args": ["mcp"]}
            action = merge_json_mcp(path, spec, dry_run=False, force=False, harness="x")
            self.assertFalse(action.changed)
            data = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(data["mcpServers"]["lbrain"]["command"], "/old/lbrain")


class TomlMergeTests(unittest.TestCase):
    def test_appends_table(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "config.toml"
            path.write_text('[cli]\ninstaller = "internal"\n', encoding="utf-8")
            spec = {"command": "/usr/bin/lbrain", "args": ["mcp"], "env": {"LBRAIN_HOME": "/tmp/b"}}
            action = merge_toml_mcp(path, spec, dry_run=False, force=False, harness="grok-build")
            self.assertTrue(action.changed)
            text = path.read_text(encoding="utf-8")
            self.assertIn("[mcp_servers.lbrain]", text)
            self.assertIn("[mcp_servers.lbrain.env]", text)
            self.assertIn('LBRAIN_HOME = "/tmp/b"', text)
            self.assertIn('installer = "internal"', text)

    def test_leaves_existing_table(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "config.toml"
            path.write_text(
                '[mcp_servers.lbrain]\ncommand = "/old"\nargs = []\n',
                encoding="utf-8",
            )
            spec = {"command": "/new", "args": ["mcp"], "env": {}}
            action = merge_toml_mcp(path, spec, dry_run=False, force=False, harness="grok-build")
            self.assertFalse(action.changed)
            self.assertIn('command = "/old"', path.read_text(encoding="utf-8"))

    def test_remove_table_keeps_siblings(self):
        text = (
            "[cli]\nx = 1\n\n[mcp_servers.lbrain]\ncommand = \"/old\"\n\n"
            "[mcp_servers.lbrain.env]\nLBRAIN_HOME = \"/h\"\n\n[privacy]\ny = 2\n"
        )
        self.assertTrue(_toml_has_table(text, "mcp_servers.lbrain"))
        out = _toml_remove_table(text, "mcp_servers.lbrain")
        self.assertIn("[cli]", out)
        self.assertIn("[privacy]", out)
        self.assertNotIn("[mcp_servers.lbrain]", out)


class McpEntryTests(unittest.TestCase):
    def test_identity_line_points_at_lbrain_ai(self):
        self.assertIn("https://lbrain.ai", IDENTITY_LINE)
        self.assertIn("identity", IDENTITY_LINE.lower())

    def test_mcp_entry_fails_closed_without_lbrain(self):
        import os
        from unittest.mock import patch

        with patch.dict(os.environ, {"PATH": ""}, clear=False):
            with patch("lbrain_agents.mcp_entry.shutil.which", return_value=None):
                self.assertEqual(mcp_main([]), 1)


if __name__ == "__main__":
    unittest.main()
