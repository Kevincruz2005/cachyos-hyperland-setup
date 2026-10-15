# SPDX-License-Identifier: MIT
"""Export consistency checks; no browser, live reload or package install."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class BrowserShortcuts(unittest.TestCase):
    def test_helium_binding_and_dependency(self):
        binds = (ROOT / "config/hypr/config/binds.lua").read_text()
        self.assertIn('hl.bind(mainMod .. " + B",          hl.dsp.exec_cmd(launchPrefix .. "helium-browser"))', binds)
        packages = json.loads((ROOT / "packages.json").read_text())["core"]
        self.assertIn("helium-browser-bin", packages)
        self.assertIn("firefox", packages)
        self.assertIn("kamoso", packages)
        self.assertIn("tesseract", packages)
        self.assertIn("tesseract-data-eng", packages)

    def test_browser_preferences_exported(self):
        binds = (ROOT / "config/hypr/config/binds.lua").read_text()
        self.assertIn('hl.bind(mainMod .. " + W",          hl.dsp.exec_cmd(launchPrefix .. BROWSER))', binds)
        self.assertIn('BROWSER      = "brave"', (ROOT / "config/hypr/config/variables.lua").read_text())
        self.assertIn("export BROWSER=helium-browser", (ROOT / "config/uwsm/env-hyprland").read_text())
        defaults = json.loads((ROOT / "config/appearance.json").read_text())["mimeapps"]["Default Applications"]
        for mime in ("x-scheme-handler/http", "x-scheme-handler/https", "text/html"):
            self.assertEqual(defaults[mime], "helium.desktop")

    def test_shortcut_documentation_matches(self):
        cheatsheet = (ROOT / "config/hypr/SHORTCUTS.txt").read_text()
        self.assertIn("Super + B               Helium browser", cheatsheet)
        self.assertIn("Super + W               Brave browser", cheatsheet)


if __name__ == "__main__":
    unittest.main()
