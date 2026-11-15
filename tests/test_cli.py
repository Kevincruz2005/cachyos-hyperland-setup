# SPDX-License-Identifier: MIT
"""CLI failure-path tests with synthetic hosts and private temporary artifacts."""
import json
import hashlib
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
from test_current_install import current_host


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

    def test_current_apply_and_rollback_in_disposable_home_without_privileges(self):
        with tempfile.TemporaryDirectory(prefix='current-apply-test-') as name:
            home = Path(name)
            original = home / '.config/hypr/config/variables.lua'
            original.parent.mkdir(parents=True)
            original.write_text('target-original-editor\n')
            model = home / '.local/share/hypr-dictation/models' / installer.MODEL_NAME
            model.parent.mkdir(parents=True)
            model.write_bytes(b'fixture-model-not-an-actual-recognizer')
            with patch.object(installer.Path, 'home', return_value=home), \
                 patch.object(installer.os, 'getuid', return_value=1000), \
                 patch.object(installer, 'audit', return_value=current_host()), \
                 patch.object(installer, 'package_plan', return_value={'roots':[], 'transaction':[], 'candidates':{}}), \
                 patch.object(installer, 'wallpaper_file', return_value=home/'wallpaper.png'), \
                 patch.object(installer, 'prompt'), \
                 patch.object(installer, 'packages', return_value={}), \
                 patch.object(installer, 'run', return_value=(0, 'inactive')), \
                 patch.object(installer, 'apply_preferences') as preferences, \
                 patch.object(installer, 'MODEL_SHA', hashlib.sha256(model.read_bytes()).hexdigest()), \
                 patch.object(installer.subprocess, 'run') as external, \
                 patch.object(sys, 'argv', ['setup', 'apply']), \
                 patch.dict(os.environ, {'XDG_CONFIG_HOME':str(home/'.config'),
                                         'XDG_STATE_HOME':str(home/'.local/state'),
                                         'XDG_DATA_HOME':str(home/'.local/share')}):
                self.assertEqual(installer.main(), 0)
                external.assert_not_called()
                preferences.assert_called_once()
            backups = list(home.glob('.local/state/cachyos-hyprland-noctalia/backups/*'))
            self.assertEqual(len(backups), 1)
            self.assertIn('mousepad --disable-server', original.read_text())
            self.assertIn('window-switcher hold', (home/'.config/hypr/config/binds.lua').read_text())
            installer.rollback(home, backups[0])
            self.assertEqual(original.read_text(), 'target-original-editor\n')


if __name__ == "__main__":
    unittest.main()
