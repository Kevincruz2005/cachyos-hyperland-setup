# SPDX-License-Identifier: MIT
"""Export consistency checks; no browser, live reload or package install."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class BrowserShortcuts(unittest.TestCase):
    def test_firefox_binding_and_dependency(self):
        binds = (ROOT / "config/hypr/config/binds.lua").read_text()
        self.assertIn('hl.bind(mainMod .. " + B",          hl.dsp.exec_cmd(launchPrefix .. "firefox"))', binds)
        self.assertIn("firefox", json.loads((ROOT / "packages.json").read_text())["core"])

    def test_other_browser_preferences_preserved(self):
        binds = (ROOT / "config/hypr/config/binds.lua").read_text()
        self.assertIn('hl.bind(mainMod .. " + W",          hl.dsp.exec_cmd(launchPrefix .. BROWSER))', binds)
        self.assertIn('BROWSER      = "brave"', (ROOT / "config/hypr/config/variables.lua").read_text())
        self.assertIn("export BROWSER=brave", (ROOT / "config/uwsm/env-hyprland").read_text())

    def test_shortcut_documentation_matches(self):
        cheatsheet = (ROOT / "config/hypr/SHORTCUTS.txt").read_text()
        self.assertIn("Super + B               Firefox browser", cheatsheet)
        self.assertIn("Super + W               Brave browser", cheatsheet)


if __name__ == "__main__":
    unittest.main()
