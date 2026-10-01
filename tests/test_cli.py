# SPDX-License-Identifier: MIT
"""CLI failure-path tests with synthetic hosts and private temporary artifacts."""
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "lib"))
import installer
from test_safety import host


class CLI(unittest.TestCase):
    def invoke(self, home, arguments, value):
        with patch.object(installer.Path, "home", return_value=home), \
             patch.object(installer.os, "getuid", return_value=1000), \
             patch.object(installer, "audit", return_value=value), \
             patch.object(installer, "package_plan", return_value={"roots": [], "transaction": [], "candidates": {}}), \
             patch.object(sys, "argv", ["setup", *arguments]), \
             patch.dict(os.environ, {"XDG_STATE_HOME": str(home / ".local/state"),
                                     "XDG_CONFIG_HOME": str(home / ".config"), "XDG_DATA_HOME": str(home / ".local/share")}), \
             patch.object(installer.subprocess, "run") as privileged_run:
            result = installer.main()
            privileged_run.assert_not_called()
            return result

    def test_unsupported_os_writes_specific_handoff_no_configuration(self):
        with tempfile.TemporaryDirectory() as name:
            home = Path(name)
            value = host()
            value["os"] = "ubuntu"
            self.assertEqual(self.invoke(home, ["apply"], value), 2)
            self.assertFalse((home / ".config/hypr").exists())
            reports = list(home.glob(".local/state/cachyos-hyprland-noctalia/reports/*/handoff.md"))
            self.assertEqual(len(reports), 1)
            self.assertIn("Dell G15 5530", reports[0].read_text())
            self.assertIn("AGENT_HANDOFF", reports[0].read_text())
            self.assertEqual(reports[0].stat().st_mode & 0o777, 0o600)

    def test_audit_is_successful_even_on_unsupported_os(self):
        with tempfile.TemporaryDirectory() as name:
            home = Path(name)
            value = host()
            value["os"] = "ubuntu"
            self.assertEqual(self.invoke(home, ["audit"], value), 0)
            self.assertFalse((home / ".config").exists())
            self.assertFalse((home / ".local/bin").exists())


if __name__ == "__main__":
    unittest.main()
